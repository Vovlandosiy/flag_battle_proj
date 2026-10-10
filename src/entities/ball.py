import os
import pygame
import pymunk

class CountryBall:
    def __init__(self, space_manager, x, y, country_code, radius=20):
        self.space_manager = space_manager
        self.radius = radius
        self.country_code = country_code.upper() # Храним код страны (например, "RU")
        
        # Настройка физических свойств
        mass = 1
        moment = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = x, y
        self.body.velocity = (0, 0) # На старте пусть будут неподвижны, пока вся толпа не спавнится
        
        # Создание круглого коллайдера
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = 0.6
        self.shape.friction = 0.3
        
        # Добавляем в симуляцию
        self.space_manager.add_object(self.body, self.shape)
        
        # Загружаем и подготавливаем текстуру флага
        self.image = self._load_and_crop_flag()

    def _load_and_crop_flag(self):
        # Путь к файлу флага (имя файла в нижнем регистре, например assets/flags/ru.png)
        flag_path = os.path.join("assets", "flags", f"{self.country_code.lower()}.png")
        
        # Базовый размер текстуры под диаметр шара
        size = self.radius * 2
        
        if os.path.exists(flag_path):
            # Загружаем изображение и масштабируем под размер шарика
            flag_surf = pygame.image.load(flag_path).convert_alpha()
            flag_surf = pygame.transform.smoothscale(flag_surf, (size, size))
        else:
            # Если картинка флага не найдена, создаем временную серую заглушку с кодом страны
            flag_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(flag_surf, (100, 100, 100), (self.radius, self.radius), self.radius)
            # Пишем первые 2 буквы кода прямо на шаре
            font = pygame.font.SysFont("Arial", 12, bold=True)
            text_surf = font.render(self.country_code[:2], True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(self.radius, self.radius))
            flag_surf.blit(text_surf, text_rect)
            return flag_surf

        # --- КРУГЛАЯ МАСКА (Чтобы сделать прямоугольный флаг идеально круглым) ---
        mask_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255), (self.radius, self.radius), self.radius)
        
        # Накладываем маску на флаг через специальный блендинг Pygame
        cropped_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cropped_surf.blit(flag_surf, (0, 0))
        cropped_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        return cropped_surf

    def draw(self, surface):
        pos_x = int(self.body.position.x)
        pos_y = int(self.body.position.y)
        
        # Отрисовываем текстуру флага с выравниванием по центру физического тела
        # Вычитаем радиус, так как Pygame рисует картинки от верхнего левого угла
        surface.blit(self.image, (pos_x - self.radius, pos_y - self.radius))
