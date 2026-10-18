# src/core/game.py
import pygame
import sys
import random
import math
from src.core.space_manager import SpaceManager
from src.entities.arena import RotatingHoleArena, CentralPropeller 
from src.entities.ball import CountryBall
from src.services.country_db import get_all_countries  

class Game:
    def __init__(self):
        pygame.init()
        
        self.width = 800 
        self.height = 800  
        self.fps = 60
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Country Flag Battle")
        self.clock = pygame.time.Clock()
        
        # Настройка физики полностью внутри SpaceManager
        self.space_manager = SpaceManager()
        
        self.current_scene_type = "propeller"  # В Шаге 2 заменим на динамический выбор
        self.arena = None
        self.propeller = None
        self.balls = []
        
        # Список для фиксации порядка выбывания флагов в текущем раунде
        self.eliminated_this_round = []
        
        self.setup_scene()
        self.running = True

    def setup_scene(self):
        """Полностью очищает старую сцену и создает новую с равномерным спавном флагов."""
        if self.arena: self.arena.destroy()
        if self.propeller: self.propeller.destroy()
        for ball in self.balls: ball.destroy()
        self.balls.clear()
        
        # Дополнительно сбрасываем менеджер физики (на случай остаточных связей)
        self.space_manager.clear_all()
        
        #геометрия арены
        arena_radius = int(self.width * 0.42) 
        self.arena = RotatingHoleArena(self.space_manager, self.width // 2, self.height // 2, radius=arena_radius)
        
        # Если выбрана сцена с пропеллером — создаем его
        if self.current_scene_type == "propeller":
            self.propeller = CentralPropeller(self.space_manager, self.width // 2, self.height // 2, arena_radius=arena_radius)
            self.propeller.body.angular_velocity = self.propeller.rotation_speed * (-self.arena.direction)
        else:
            self.propeller = None

        # РАВНОМЕРНЫЙ СПАВН ШАРОВ ПО КРУГУ (полярные координаты)
        available_countries = get_all_countries()
        cx, cy = self.width // 2, self.height // 2
        
        for country in available_countries:
            # случайный радиус
            r = random.uniform(0, 80)
            # случайный угол(в радианах)
            angle = random.uniform(0, 2 * math.pi)
            
            # Переводим в декартовы координаты X и Y
            spawn_x = cx + r * math.cos(angle)
            # Смещаем спавн чуть выше (на 30 пикселей)???
            #spawn_y = cy + r * math.sin(angle) - 30 
            spawn_y = cy + r * math.sin(angle);
            
            self.balls.append(CountryBall(self.space_manager, spawn_x, spawn_y, country))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        dt = 1.0 / self.fps
        self.space_manager.update(dt)
        
        for ball in self.balls[:]:
            # 1. Проверяем, вылетел ли шар из арены программно
            if not ball.is_eliminated:
                if self.arena and not self.arena.is_inside(ball.body.position):
                    ball.is_eliminated = True
                    self.eliminated_this_round.append(ball.country_code.lower())
                    print(f"{ball.country_code.lower()} выбыл (программно)")
            
            # 2. Физическое удаление из памяти при падении вниз экрана
            if ball.body.position.y > self.height + 50:
                ball.destroy()         
                self.balls.remove(ball)
        
    def draw(self):
        self.screen.fill((20, 24, 35))
        
        if self.arena: 
            self.arena.draw(self.screen)
        if self.propeller: 
            self.propeller.draw(self.screen)
            
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
        self.propeller.destroy()
        pygame.quit()
        sys.exit()
