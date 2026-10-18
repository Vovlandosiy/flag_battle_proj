# src/core/game.py
import pygame
import sys
import random
import math
from src.core.space_manager import SpaceManager
from src.entities.arena import ARENA_REGISTRY 
from src.entities.ball import CountryBall
from src.services.country_db import get_all_countries  
from src.services.tournament_manager import TournamentManager

class Game:
    def __init__(self):
        pygame.init()
        
        self.width = 450
        self.height = 800
        self.fps = 60
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Country Flag Battle")
        self.clock = pygame.time.Clock()
        
        self.sim_size = 800
        self.sim_surface = pygame.Surface((self.sim_size, self.sim_size))
        
        self.space_manager = SpaceManager()
        self.tournament_manager = TournamentManager()
        
        self.arena = None
        self.balls = []
        self.eliminated_this_round = []
        
        self.hud_flag_cache = {}
        
        # --- Переменные для логики плавного свайпа верхнего HUD ---
        self.hud_page = 0              # Текущая страница
        self.next_page = 0             # Страница, на которую переключаемся
        self.page_timer = 0            
        self.page_duration_frames = 300 # 5 секунд до свайпа
        
        # Анимация
        self.is_animating_hud = False  # Идет ли сейчас процесс анимации сдвига
        self.hud_anim_progress = 0.0   # Прогресс анимации от 0.0 до 1.0
        self.hud_anim_speed = 0.05     # Скорость свайпа (чем больше, тем быстрее свайп)
        
        # Временные поверхности под каждую колонку/страницу HUD (размер зоны: ширина 410, высота 130)
        self.hud_surf_current = pygame.Surface((410, 150), pygame.SRCALPHA)
        self.hud_surf_next = pygame.Surface((410, 150), pygame.SRCALPHA)
        
        self.setup_scene()
        self.running = True

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
            r = random.uniform(0, 80)
            angle = random.uniform(0, 2 * math.pi)
            spawn_x = cx + r * math.cos(angle)
            spawn_y = cy + r * math.sin(angle)
            
            self.balls.append(CountryBall(self.space_manager, spawn_x, spawn_y, country))



    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
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
            self.setup_scene()

    def _get_cached_flag(self, country_code, size=24):
        """Ленивая загрузка флага из assets в высоком качестве (без мыла)."""
        key = f"{country_code}_{size}"
        if key in self.hud_flag_cache:
            return self.hud_flag_cache[key]
            
        import os
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
        self.screen.fill((15, 18, 26))
        self.sim_surface.fill((20, 24, 35))
        
        if self.arena: 
            self.arena.draw(self.sim_surface)
        for ball in self.balls:
            ball.draw(self.sim_surface)
            
        render_size = 430
        scaled_sim = pygame.transform.smoothscale(self.sim_surface, (render_size, render_size))
        
        arena_x = (self.width - render_size) // 2
        # Сдвигаем арену чуть ниже на Y=180, освобождая место для двух колонок верхнего HUD
        arena_y = 180 
        self.screen.blit(scaled_sim, (arena_x, arena_y))
        
        self._draw_hud(arena_y, render_size)
        
        pygame.display.flip()

    def _render_page_to_surface(self, surface, page_idx, font):
        """Вспомогательный метод для отрисовки конкретной страницы на отдельный холст."""
        surface.fill((0, 0, 0, 0)) 
        
        start_idx = page_idx * 10
        page_countries = self.tournament_manager.qualified_countries[start_idx : start_idx + 10]
        
        icon_size_top = 24  # Увеличили размер флагов до 24
        base_y = 10        # Начальная точка Y внутри холста
        line_height = 26   # Оптимальный шаг между строками для размера 24
        
        for i, country_code in enumerate(page_countries):
            global_rank = start_idx + i + 1
            
            if i < 5:
                col_x = 0
                row_y = base_y + i * line_height
            else:
                col_x = 210
                row_y = base_y + (i - 5) * line_height
                
            # Порядковый номер (сдвиг +5 по Y для центрирования относительно флага 24x24)
            rank_text = font.render(f"{global_rank}.", True, (150, 150, 150))
            surface.blit(rank_text, (col_x, row_y + 5))
            
            # Большой качественный флаг 24x24
            flag_img = self._get_cached_flag(country_code, icon_size_top)
            surface.blit(flag_img, (col_x + 25, row_y))
            
            # Код страны (сдвиг +5 по Y для идеального центрирования с флагом)
            code_text = font.render(f"— {country_code.upper()}", True, (220, 220, 220))
            surface.blit(code_text, (col_x + 25 + icon_size_top + 8, row_y + 5))



    def _draw_hud(self, arena_y, render_size):
        """Отрисовывает двухколоночный верхний HUD с ПЛАВНЫМ свайпом и динамическую нижнюю сетку."""
        font = pygame.font.SysFont("Arial", 14, bold=True)
        title_font = pygame.font.SysFont("Arial", 16, bold=True)
        
        # ==========================================
        # 1. ВЕРХНИЙ HUD (Анимированный плавный свайп)
        # ==========================================
        total_qualified = len(self.tournament_manager.qualified_countries)
        top_text = title_font.render(f"QUALIFIED ({total_qualified}/50)", True, (100, 220, 100))
        self.screen.blit(top_text, (20, 12))
        
        # Рендерим текущую страницу на её холст
        self._render_page_to_surface(self.hud_surf_current, self.hud_page, font)
        
        hud_pos_x = 20
        hud_pos_y = 16
        
        if self.is_animating_hud:
            # Рендерим следующую страницу на второй холст, пока идет анимация
            self._render_page_to_surface(self.hud_surf_next, self.next_page, font)
            
            # Рассчитываем смещение на основе кубического сглаживания (ease-out), чтобы свайп замедлялся к концу
            # Формула плавности: t = 1 - (1 - x)^3
            t = 1.0 - math.pow(1.0 - self.hud_anim_progress, 3)
            offset_x = int(t * 430) # Шаг сдвига равен ширине рабочей зоны свайпа
            
            # Текущий холст уезжает ВЛЕВО (вычитаем offset_x)
            self.screen.blit(self.hud_surf_current, (hud_pos_x - offset_x, hud_pos_y))
            # Новой холст выезжает СПРАВА (начинает движение от hud_pos_x + 430)
            self.screen.blit(self.hud_surf_next, (hud_pos_x + 430 - offset_x, hud_pos_y))
        else:
            # Если анимации нет, просто выводим текущую страницу статично
            self.screen.blit(self.hud_surf_current, (hud_pos_x, hud_pos_y))

        # ==========================================
        # 2. НИЖНЯЯ ПАНЕЛЬ (Динамическая сетка с вытеснением)
        # ==========================================
        bottom_y = arena_y + render_size + 15
        bottom_text = title_font.render("ELIMINATED THIS ROUND:", True, (220, 100, 100))
        self.screen.blit(bottom_text, (20, bottom_y))
        
        start_x = 20
        start_y = bottom_y + 25
        icon_size_bottom = 28
        spacing = 4
        max_width = self.width - 20
        
        current_x = start_x
        current_y = start_y
        
        visible_eliminated = self.eliminated_this_round[-48:]
        
        for ball_data in visible_eliminated:
            if current_x + icon_size_bottom > max_width:
                current_x = start_x
                current_y += icon_size_bottom + spacing
                
            small_flag = pygame.transform.smoothscale(ball_data["image"], (icon_size_bottom, icon_size_bottom))
            self.screen.blit(small_flag, (current_x, current_y))
            current_x += icon_size_bottom + spacing
        
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
