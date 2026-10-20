# src/core/game.py
import pygame
import sys
import os
import random
import math
import pyttsx3
import threading
from src.core.space_manager import SpaceManager
from src.entities.arena import ARENA_REGISTRY 
from src.entities.ball import CountryBall
from src.services.country_db import get_all_countries  
from src.services.tournament_manager import TournamentManager

class Game:
    def __init__(self):
        pygame.init()
        
        # Настоящее Full HD разрешение для YouTube Shorts
        self.virtual_width = 1080
        self.virtual_height = 1920
        
        # Коэффициент сжатия окна для твоего монитора (1080 * 0.45 = 486, 1920 * 0.45 = 864)
        self.window_scale = 0.50 
        self.window_width = int(self.virtual_width * self.window_scale)
        self.window_height = int(self.virtual_height * self.window_scale)
        
        self.fps = 60
        
        # Физическое окно на мониторе
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        # Внутренний холст, где всё рендерится в идеальном качестве
        self.virtual_screen = pygame.Surface((self.virtual_width, self.virtual_height))
        
        pygame.display.set_caption("Country Flag Battle")
        self.clock = pygame.time.Clock()
        
        # Размер холста симуляции физики (арены) делаем больше
        self.sim_size = 1920
        self.sim_surface = pygame.Surface((self.sim_size, self.sim_size))
        
        self.space_manager = SpaceManager()
        self.tournament_manager = TournamentManager()
        
        self.arena = None
        self.balls = []
        self.eliminated_this_round = []
        
        self.hud_flag_cache = {}
        
        self.hud_page = 0              
        self.next_page = 0             
        self.page_timer = 0            
        self.page_duration_frames = 300 
        
        self.is_animating_hud = False  
        self.hud_anim_progress = 0.0   
        self.hud_anim_speed = 0.05     
        
        # Увеличили размеры поверхностей HUD под новое разрешение (ширина 1000, высота 400)
        self.hud_surf_current = pygame.Surface((1000, 400), pygame.SRCALPHA)
        self.hud_surf_next = pygame.Surface((1000, 400), pygame.SRCALPHA)

        self.show_fps = True
        
        self.setup_scene()
        self.running = True

        self.game_state = "PLAYING"     
        self.winner_timer = 0           
        self.winner_data = None         

    def _speak_worker(self, text):
        """Вспомогательный метод для озвучки. Создает чистый инстанс TTS при каждом вызове."""
        try:
            # Инициализируем движок локально прямо в потоке, чтобы запустить чистый цикл событий
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
            # Насильно удаляем объект из памяти для очистки ресурсов потока
            del engine 
        except Exception as e:
            print(f"Ошибка TTS: {e}")



    def setup_scene(self):
        """Полностью очищает старую сцену и создает новую на виртуальном холсте."""
        if self.arena: self.arena.destroy()
        for ball in self.balls: ball.destroy()
        self.balls.clear()
        
        self.space_manager.clear_all()
        self.eliminated_this_round.clear()
        
        # Расчет радиуса арены идет относительно виртуального размера 800
        arena_radius = int(self.sim_size * 0.42) 
        ArenaClass = random.choice(ARENA_REGISTRY)
        
        # Спавним арену ровно по центру виртуального холста (400, 400)
        self.arena = ArenaClass(self.space_manager, self.sim_size // 2, self.sim_size // 2, radius=arena_radius)
        
        available_countries = self.tournament_manager.get_available_countries()
        if not available_countries:
            print("Нет доступных стран. Сброс турнира.")
            self.tournament_manager.reset_tournament()
            available_countries = self.tournament_manager.get_available_countries()

        cx, cy = self.sim_size // 2, self.sim_size // 2
        for country in available_countries:
            r = random.uniform(0, 250) 
            angle = random.uniform(0, 2 * math.pi)
            spawn_x = cx + r * math.cos(angle)
            spawn_y = cy + r * math.sin(angle)
            
            self.balls.append(CountryBall(self.space_manager, spawn_x, spawn_y, country))



    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    self.show_fps = not self.show_fps


    def update(self):

        if self.game_state == "WINNER_SCENE":
            self.winner_timer -= 1
            if self.winner_timer <= 0:
                self.game_state = "PLAYING"
                self.setup_scene()
            return  # Пропускаем обновление физики во время триумфа

        dt = 1.0 / self.fps
        self.space_manager.update(dt)
        
        # Логика таймера и анимации свайпа верхнего HUD
        if not self.is_animating_hud:
            self.page_timer += 1
            if self.page_timer >= self.page_duration_frames:
                self.page_timer = 0
                potential_next = self.hud_page + 1
                
                # Проверяем, есть ли флаги на следующей странице
                if potential_next * 10 < len(self.tournament_manager.qualified_countries):
                    self.next_page = potential_next
                else:
                    self.next_page = 0 # Возвращаемся на первую страницу
                
                # Запускаем анимацию только если страницы действительно РАЗНЫЕ
                if self.next_page != self.hud_page:
                    self.is_animating_hud = True
                    self.hud_anim_progress = 0.0
        else:
            # Прогресс анимации сдвига
            self.hud_anim_progress += self.hud_anim_speed
            if self.hud_anim_progress >= 1.0:
                self.hud_anim_progress = 1.0
                self.hud_page = self.next_page
                self.is_animating_hud = False

        for ball in self.balls[:]:
            if not ball.is_eliminated:
                if self.arena and not self.arena.is_inside(ball.body.position):
                    ball.is_eliminated = True
                    self.eliminated_this_round.append({
                        "code": ball.country_code.lower(),
                        "image": ball.image
                    })
                    print(f"{ball.country_code.lower()} выбыл (программно)")
            
            if ball.body.position.y > self.sim_size + 50:
                ball.destroy()         
                self.balls.remove(ball)

        if len(self.balls) == 1:
            winner_ball = self.balls[0]
            self.tournament_manager.register_winner(winner_ball.country_code)
            
            high_res_flag = self._get_cached_flag(winner_ball.country_code, 350)

            self.winner_data = {
                "code": winner_ball.country_code.upper(),
                "image": high_res_flag
            }
            self.game_state = "WINNER_SCENE"
            self.winner_timer = 180  
            
            spoken_code = " ".join(list(self.winner_data['code']))
            text_to_speak = f"{spoken_code} win"
            
            threading.Thread(target=self._speak_worker, args=(text_to_speak,), daemon=True).start()

    def _get_cached_flag(self, country_code, size=24):
        """Ленивая загрузка флага из assets в высоком качестве (без мыла)."""
        key = f"{country_code}_{size}"
        if key in self.hud_flag_cache:
            return self.hud_flag_cache[key]
            
        flag_path = os.path.join("assets", "flags", f"{country_code.lower()}.png")
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        if os.path.exists(flag_path):
            flag_img = pygame.image.load(flag_path).convert_alpha()
            # Используем качественное масштабирование
            flag_img = pygame.transform.smoothscale(flag_img, (size, size))
            
            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
            surf.blit(flag_img, (0, 0))
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        else:
            pygame.draw.circle(surf, (100, 100, 100), (size // 2, size // 2), size // 2)
            
        self.hud_flag_cache[key] = surf
        return surf
        
    def draw(self):
        self.virtual_screen.fill((15, 18, 26))
        self.sim_surface.fill((20, 24, 35))
        
        if self.arena: 
            self.arena.draw(self.sim_surface)
        for ball in self.balls:
            ball.draw(self.sim_surface)
            
        render_size = 1000
        scaled_sim = pygame.transform.smoothscale(self.sim_surface, (render_size, render_size))
        
        arena_x = (self.virtual_width - render_size) // 2
        arena_y = 460 
        self.virtual_screen.blit(scaled_sim, (arena_x, arena_y))
        
        self._draw_hud(arena_y, render_size)
        
        if self.game_state == "WINNER_SCENE" and self.winner_data:
            # Создаем полупрозрачную темную подложку на весь экран
            overlay = pygame.Surface((self.virtual_width, self.virtual_height), pygame.SRCALPHA)
            overlay.fill((10, 12, 18, 220)) # Темный фон с альфа-каналом
            self.virtual_screen.blit(overlay, (0, 0))
            
            # Масштабируем флаг победителя до огромного размера (350x350 пикселей)
            big_flag = self.winner_data["image"]
            flag_x = (self.virtual_width - 350) // 2
            flag_y = (self.virtual_height - 350) // 2 - 100
            self.virtual_screen.blit(big_flag, (flag_x, flag_y))
            
            # Отрисовываем текст победителя
            win_font = pygame.font.SysFont("Arial", 80, bold=True)
            win_text = win_font.render(f"{self.winner_data['code']} WIN!", True, (255, 215, 0)) # Золотой цвет
            text_x = (self.virtual_width - win_text.get_width()) // 2
            text_y = flag_y + 400
            self.virtual_screen.blit(win_text, (text_x, text_y))
            
        # Масштабирование под физическое окно монитора
        scaled_window = pygame.transform.smoothscale(self.virtual_screen, (self.window_width, self.window_height))
        self.screen.blit(scaled_window, (0, 0))
        
        pygame.display.flip()

    def _render_page_to_surface(self, surface, page_idx, font):
        """Вспомогательный метод для отрисовки конкретной страницы на отдельный холст."""
        surface.fill((0, 0, 0, 0)) 
        
        start_idx = page_idx * 10
        page_countries = self.tournament_manager.qualified_countries[start_idx : start_idx + 10]
        
        icon_size_top = 54  
        base_y = 10        # Подняли вверх, так как заголовок ушел в _draw_hud
        line_height = 62   
        
        for i, country_code in enumerate(page_countries):
            global_rank = start_idx + i + 1
            
            if i < 5:
                col_x = 0
                row_y = base_y + i * line_height
            else:
                col_x = 500 
                row_y = base_y + (i - 5) * line_height
                
            rank_text = font.render(f"{global_rank}.", True, (150, 150, 150))
            surface.blit(rank_text, (col_x, row_y + 10))
            
            flag_img = self._get_cached_flag(country_code, icon_size_top)
            surface.blit(flag_img, (col_x + 65, row_y))
            
            code_text = font.render(f"— {country_code.upper()}", True, (220, 220, 220))
            surface.blit(code_text, (col_x + 65 + icon_size_top + 15, row_y + 10))


    def _draw_hud(self, arena_y, render_size):
        """Отрисовывает двухколоночный верхний HUD с ПЛАВНЫМ свайпом и динамическую нижнюю сетку."""
        font = pygame.font.SysFont("Arial", 32, bold=True) 
        title_font = pygame.font.SysFont("Arial", 42, bold=True) 
        
        # ==========================================
        # 1. ВЕРХНИЙ HUD (Статичный заголовок по центру + свайп флагов)
        # ==========================================
        total_qualified = len(self.tournament_manager.qualified_countries)
        top_text = title_font.render(f"QUALIFIED ({total_qualified}/50)", True, (100, 220, 100))
        # Центрируем заголовок по ширине экрана (1080)
        title_x = (self.virtual_width - top_text.get_width()) // 2
        self.virtual_screen.blit(top_text, (title_x, 30))
        
        # Рендерим текущую страницу на её холст
        self._render_page_to_surface(self.hud_surf_current, self.hud_page, font)
        
        hud_pos_x = 40
        hud_pos_y = 100 # Опустили холст ниже, чтобы он не перекрывал заголовок
        hud_width = self.hud_surf_current.get_width() 
        
        if self.is_animating_hud:
            self._render_page_to_surface(self.hud_surf_next, self.next_page, font)
            
            t = 1.0 - math.pow(1.0 - self.hud_anim_progress, 3)
            offset_x = int(t * hud_width) 
            
            self.virtual_screen.blit(self.hud_surf_current, (hud_pos_x - offset_x, hud_pos_y))
            self.virtual_screen.blit(self.hud_surf_next, (hud_pos_x + hud_width - offset_x, hud_pos_y))
        else:
            self.virtual_screen.blit(self.hud_surf_current, (hud_pos_x, hud_pos_y))

        # ==========================================
        # 2. НИЖНЯЯ ПАНЕЛЬ (Идеальная геометрия сетки выбывших)
        # ==========================================
        bottom_y = arena_y + render_size + 40
        bottom_text = title_font.render("ELIMINATED THIS ROUND:", True, (220, 100, 100))
        self.virtual_screen.blit(bottom_text, (40, bottom_y))
        
        icon_size_bottom = 64
        spacing = 8  # Уменьшили отступ до 8px
        # Пересчитываем стартовый X так, чтобы 14 флагов встали ровно по центру холста
        # 14 флагов * 64px + 13 отступов * 8px = 896 + 104 = 1000px общей ширины ряда.
        # (1080 - 1000) // 2 = 40px отступ слева и справа. Идеальная симметрия!
        start_x = 40 
        start_y = bottom_y + 60
        max_width = self.virtual_width - 40
        
        current_x = start_x
        current_y = start_y
        
        visible_eliminated = self.eliminated_this_round[-56:] # Берем до 42 флагов (3 полных ряда по 14)
        
        for ball_data in visible_eliminated:
            if current_x + icon_size_bottom > max_width:
                current_x = start_x
                current_y += icon_size_bottom + spacing
                
            small_flag = pygame.transform.smoothscale(ball_data["image"], (icon_size_bottom, icon_size_bottom))
            self.virtual_screen.blit(small_flag, (current_x, current_y))
            current_x += icon_size_bottom + spacing

        # СЧЕТЧИК ФПС
        if self.show_fps:
            fps_font = pygame.font.SysFont("Arial", 24, bold=True)
            fps_value = int(self.clock.get_fps())
            fps_text = fps_font.render(f"FPS: {fps_value}", True, (0, 255, 0) if fps_value > 50 else (255, 165, 0))
            # Прижимаем к правому краю (1080 - ширина текста - 40px отступа)
            fps_x = self.virtual_width - fps_text.get_width() - 40
            self.virtual_screen.blit(fps_text, (fps_x, 30))


        
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)
            
        # При выходе из игры корректно уничтожаем структуры
        self.arena.destroy()
        pygame.quit()
        sys.exit()
