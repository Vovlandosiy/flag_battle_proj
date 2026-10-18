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
        
        self.width = 800 
        self.height = 800  
        self.fps = 60
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Country Flag Battle")
        self.clock = pygame.time.Clock()
        
        self.space_manager = SpaceManager()
        
        # Инициализируем менеджер турнира (нашу БД)
        self.tournament_manager = TournamentManager()
        
        self.arena = None
        self.balls = []
        
        # Список для хранения выбывших в текущем раунде (для отрисовки внизу экрана)
        self.eliminated_this_round = []
        
        self.setup_scene()
        self.running = True

    def setup_scene(self):
        """Полностью очищает старую сцену и создает новую со списком валидных флагов."""
        if self.arena: self.arena.destroy()
        for ball in self.balls: ball.destroy()
        self.balls.clear()
        
        self.space_manager.clear_all()
        
        # Очищаем список выбывших флагов для новой сцены
        self.eliminated_this_round.clear()
        
        arena_radius = int(self.width * 0.42) 
        ArenaClass = random.choice(ARENA_REGISTRY)
        self.arena = ArenaClass(self.space_manager, self.width // 2, self.height // 2, radius=arena_radius)
        
        # Запрашиваем у БД список стран, которые еще НЕ прошли квалификацию
        available_countries = self.tournament_manager.get_available_countries()
        
        # Если вдруг список пуст (например, все прошли), сбрасываем турнир
        if not available_countries:
            print("Нет доступных стран. Сброс турнира.")
            self.tournament_manager.reset_tournament()
            available_countries = self.tournament_manager.get_available_countries()

        cx, cy = self.width // 2, self.height // 2
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
                    # Сохраняем иконку флага и код для нижней панели
                    self.eliminated_this_round.append({
                        "code": ball.country_code.lower(),
                        "image": ball.image
                    })
                    print(f"{ball.country_code.lower()} выбыл (программно)")
            
            # 2. Физическое удаление при падении ниже экрана
            if ball.body.position.y > self.height + 50:
                ball.destroy()         
                self.balls.remove(ball)

        # 3. ПРОВЕРКА НА ПОБЕДИТЕЛЯ РАУНДА
        # Если остался ровно 1 шар (или меньше, на случай одновременного вылета)
        if len(self.balls) == 1:
            winner_ball = self.balls[0]
            # Записываем победителя в постоянную память БД
            self.tournament_manager.register_winner(winner_ball.country_code)
            
            # Перезапускаем сцену на новый раунд
            self.setup_scene()
        
    def draw(self):
        self.screen.fill((20, 24, 35))
        
        if self.arena: 
            self.arena.draw(self.screen)
            
        for ball in self.balls:
            ball.draw(self.screen)
        
        pygame.display.flip()

        
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
