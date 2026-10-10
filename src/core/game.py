import pygame
import sys
import random
from src.core.space_manager import SpaceManager
from src.entities.arena import RotatingHoleArena  # Новый импорт
from src.entities.ball import CountryBall

class Game:
    def __init__(self):
        pygame.init()
        
        self.width = 800
        self.height = 800
        self.fps = 60
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Country Flag Battle - Rotating Arena")
        self.clock = pygame.time.Clock()
        
        self.space_manager = SpaceManager()
        
        # Создаем новую вращающуюся арену
        self.arena = RotatingHoleArena(self.space_manager, self.width // 2, self.height // 2)
        
        self.balls = []
         # Тестовый список кодов стран для проверки
        test_countries = ["ad", "ae", "af", "ag", "ai", "al", "am", "an", "ao", "aq", 
                          "ar", "at", "au", "aw", "ax", "az", "ba", "bb", "bd", "be", 
                          "bf", "bg", "bh", "bi", "bj", "bm", "bn", "bo", "br", "bs", 
                          "bt", "bw", "by", "bz", "ca", "cd", "cf", "cg", "ch", "ci", 
                          "ck", "cl", "cm", "cn", "co", "cr", "cu", "cv", "cw", "cy", 
                          "cz", "de", "dj", "dk", "dm", "do", "dz", "ec", "ee", "eg", 
                          "eh", "en", "er", "es", "et", "eu", "fi", "fj", "fk", "fm", 
                          "fo", 
                          "fr", "ga", "gb", "gd", "ge", "gf", "gg", "gh", "gi", "gl", 
                          "gm", "gn", "gp", "gq", "gr", "gs", "gt", "gw", "gy", "hk", 
                          "hn", "hr", "ht", "hu", "ic", "id", "ie", "il", "im", "in", 
                          "iq", "ir", "is", "it", "je", "jm", "jo", "jp", "ke", "kg", 
                          "kh", "ki", "km", "kn", "ko", "kp", "kr", "kw", "ky", "kz", 
                          "la", "lb", "lc", "li", "lk", "lr", "ls", "lt", "lu", "lv", 
                          "ly", "ma", "mc", "md", "me", "mg", "mh", "mk", "ml", "mm", 
                          "mn", "mo", "mp", "mq", "mr", "mt", "mu", "mv", "mw", "mx", 
                          "my", "mz", "na", "nc", "ne", "ng", "ni", "nl", "no", "np", 
                          "nr", "nu", "nz", "om", "pa", "pe", "pf", "pg", "ph", "pk", 
                          "pl", "pr", "ps", "pt", "pw", "py", "qa", "qs", "ro", "rs", 
                          "ru", "rw", "sa", "sb", "sc", "sd", "se", "sg", "sh", "si", 
                          "sk", "sl", "sm", "sn", "so", "sr", "ss", "st", "sv", "sx", 
                          "sy", "sz", "tc", "td", "tg", "th", "tj", "tl", "tm", "tn", 
                          "to", "tr", "tt", "tv", "tw", "tz", "ua", "ug", "us", "uy", 
                          "uz", "va", "vc", "ve", "vg", "vi", "vn", "vu", "wl", "ws", 
                          "xi", "xk", "ye", "za", "zm", "zw"]
        
        # Спавним по 5 штук каждой страны из тестового списка
        for country in test_countries:
            for _ in range(1):
                spawn_x = (self.width // 2) + random.randint(-80, 80)
                spawn_y = (self.height // 2) + random.randint(-80, 80)
                # Передаем код страны в конструктор шара
                self.balls.append(CountryBall(self.space_manager, spawn_x, spawn_y, country))

        self.running = True
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Спавн шара по клику мышки (теперь этот блок НАХОДИТСЯ ВНУТРИ цикла for)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # Берём случайную страну из нашего списка test_countries для теста
                # Этот список должен быть доступен (мы объявили его в __init__)
                # Чтобы не дублировать код, выберем например "ru" или случайный из существующих
                random_country = random.choice(["ua"])
                
                # Теперь передаем все 4 параметра, включая код страны
                self.balls.append(CountryBall(self.space_manager, mx, my, random_country))



                
    def update(self):
        dt = 1.0 / self.fps
        self.space_manager.update(dt)
        
    def draw(self):
        self.screen.fill((20, 24, 35))
        
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
            
        pygame.quit()
        sys.exit()
