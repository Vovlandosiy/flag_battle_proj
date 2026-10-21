import os
import pygame
import pymunk

class CountryBall:
    RADIUS = 44
    MASS = 1.8
    ELASTICITY = 0.7
    FRICTION = 0.3

    def __init__(self, space_manager, x, y, country_code):
        self.space_manager = space_manager
        self.country_code = country_code.upper()
        self.is_eliminated = False  # Флаг для программного выбывания
        
        mass = self.MASS
        moment = pymunk.moment_for_circle(mass, 0, self.RADIUS)
        
        self.body = pymunk.Body(mass, moment)
        self.body.position = x, y
        self.body.velocity = (0, 0)
        
        self.shape = pymunk.Circle(self.body, self.RADIUS)
        self.shape.elasticity = self.ELASTICITY
        self.shape.friction = self.FRICTION
        
        self.space_manager.add_object(self.body, self.shape)
        self.image = self._load_and_crop_flag()

    def _load_and_crop_flag(self):
        flag_path = os.path.join("assets", "flags", f"{self.country_code.lower()}.png")
        size = self.RADIUS * 2
        
        if os.path.exists(flag_path):
            flag_surf = pygame.image.load(flag_path).convert_alpha()
            flag_surf = pygame.transform.smoothscale(flag_surf, (size, size))
        else:
            flag_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(flag_surf, (100, 100, 100), (self.RADIUS, self.RADIUS), self.RADIUS)
            font = pygame.font.SysFont("Arial", 22, bold=True) # Увеличили шрифт с 10 до 22
            text_surf = font.render(self.country_code[:2], True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(self.RADIUS, self.RADIUS))
            flag_surf.blit(text_surf, text_rect)
            return flag_surf

        mask_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255), (self.RADIUS, self.RADIUS), self.RADIUS)
        
        cropped_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cropped_surf.blit(flag_surf, (0, 0))
        cropped_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        return cropped_surf

    def destroy(self):
        self.space_manager.remove_object(self.body, self.shape)

    def draw(self, surface):
        pos_x = int(self.body.position.x)
        pos_y = int(self.body.position.y)
        surface.blit(self.image, (pos_x - self.RADIUS, pos_y - self.RADIUS))
