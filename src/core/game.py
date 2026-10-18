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
        
        # 1. Реальное разрешение окна для YouTube Shorts
        self.width = 450
        self.height = 800
        self.fps = 60
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Country Flag Battle - Shorts Mode")
        self.clock = pygame.time.Clock()
        
        # 2. Виртуальный холст для физики (чтобы флаги оставались большими и четкими)
        self.sim_size = 800
        self.sim_surface = pygame.Surface((self.sim_size, self.sim_size))
        
        self.space_manager = SpaceManager()
        self.tournament_manager = TournamentManager()
        
        self.arena = None
        self.balls = []
        self.eliminated_this_round = []
        
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
        
        for ball in self.balls[:]:
            # 1. Программное выбывание флага из арены
            if not ball.is_eliminated:
                if self.arena and not self.arena.is_inside(ball.body.position):
                    ball.is_eliminated = True
                    self.eliminated_this_round.append({
                        "code": ball.country_code.lower(),
                        "image": ball.image
                    })
                    print(f"{ball.country_code.lower()} выбыл (программно)")
            
            # 2. Физическое удаление при падении ниже виртуального холста
            if ball.body.position.y > self.sim_size + 50:
                ball.destroy()         
                self.balls.remove(ball)

        # 3. Проверка на победителя раунда
        if len(self.balls) == 1:
            winner_ball = self.balls[0]
            self.tournament_manager.register_winner(winner_ball.country_code)
            self.setup_scene()
        
    def draw(self):
        # Очищаем основной экран глубоким темным цветом
        self.screen.fill((15, 18, 26))
        
        # Очищаем виртуальный холст симуляции
        self.sim_surface.fill((20, 24, 35))
        
        # Отрисовка физических объектов на виртуальном холсте
        if self.arena: 
            self.arena.draw(self.sim_surface)
        for ball in self.balls:
            ball.draw(self.sim_surface)
            
        # СЖАТИЕ И ПЕРЕНОС: Масштабируем холст симуляции 800x800 под ширину Shorts (например, до 430x430)
        render_size = 430
        scaled_sim = pygame.transform.smoothscale(self.sim_surface, (render_size, render_size))
        
        # Центрируем уменьшенную арену на экране 450x800 (по Y смещаем примерно на центр)
        arena_x = (self.width - render_size) // 2
        arena_y = (self.height - render_size) // 2 - 20  # Чуть приподнимем, чтобы снизу было больше места
        self.screen.blit(scaled_sim, (arena_x, arena_y))
        
        # --- ОТРИСОВКА HUD ПАНЕЛЕЙ (СВЕРХУ И СНИЗУ) ---
        self._draw_hud(arena_y, render_size)
        
        pygame.display.flip()
        
    def _draw_hud(self, arena_y, render_size):
        """Отрисовывает интерфейс: прошедших квалификацию сверху, выбывших снизу."""
        # Настройки шрифта
        font = pygame.font.SysFont("Arial", 16, bold=True)
        
        # 1. ТОП ПАНЕЛЬ (Прошедшие квалификацию)
        top_text = font.render(f"QUALIFIED ({len(self.tournament_manager.qualified_countries)}/50)", True, (100, 220, 100))
        self.screen.blit(top_text, (15, 15))
        
        # Выводим последние несколько флагов, которые прошли квалификацию вверху в ряд
        x_offset = 15
        for country_code in self.tournament_manager.qualified_countries[-10:]: # Показываем последние 10
            # Чтобы не загружать заново картинку флага, можно выводить просто текст, 
            # но в будущем мы сможем подгружать сюда мини-иконки. Пока пишем текстом:
            code_text = font.render(country_code.upper(), True, (200, 200, 200))
            self.screen.blit(code_text, (x_offset, 40))
            x_offset += 40

        # 2. НИЖНЯЯ ПАНЕЛЬ (Лента выбывших в этом раунде флагов)
        bottom_y = arena_y + render_size + 20
        bottom_text = font.render("ELIMINATED THIS ROUND:", True, (220, 100, 100))
        self.screen.blit(bottom_text, (15, bottom_y))
        
        # Отрисовываем иконки флагов выбывших стран горизонтальной лентой
        # Берем последние выбывшие флаги, которые помещаются на экране
        flag_x = 15
        flag_y = bottom_y + 25
        icon_size = 28
        
        for ball_data in self.eliminated_this_round[-14:]: # Показываем последние 14 выбывших
            # Берем готовую иконку из сохраненных данных шара и масштабируем под ленту
            small_flag = pygame.transform.smoothscale(ball_data["image"], (icon_size, icon_size))
            self.screen.blit(small_flag, (flag_x, flag_y))
            flag_x += icon_size + 3 # Смещение + отступ в 3 пикселя

        
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
