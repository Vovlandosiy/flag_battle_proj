import math
import random
import pygame
import pymunk

class RotatingHoleArena:
    def __init__(self, space_manager, center_x, center_y, radius=350):
        self.space_manager = space_manager
        self.center = (center_x, center_y)
        self.radius = radius
        
        # --- РАНДОМИЗАЦИЯ ПАРАМЕТРОВ АРЕНЫ ---
        # Скорость вращения (радиан в секунду). Например, от 0.3 до 0.8
        self.rotation_speed = random.uniform(0.3, 0.8)
        # Направление вращения: 1 — по часовой, -1 — против часовой
        self.direction = random.choice([1, -1])
        
        # Размер отверстия в градусах (например, от 25 до 45 градусов)
        self.hole_angle_deg = random.randint(15, 25)
        
        # --- СОЗДАНИЕ ТЕЛА АРЕНЫ ---
        # Чтобы объект мог вращаться, его тип должен быть KINEMATIC (двигается скриптом/мотором, игнорирует гравитацию)
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.center
        
        # Задаем угловую скорость вращения тела
        self.body.angular_velocity = self.rotation_speed * self.direction
        
        self.shapes = []
        self._build_arena_with_hole()

    def _build_arena_with_hole(self):
        segment_count = 90  # Общее количество сегментов для круга
        hole_segments = int(segment_count * (self.hole_angle_deg / 360.0))
        
        # Строим круг, пропуская сегменты, которые попадают в зону "отверстия"
        for i in range(segment_count):
            # Если текущий сегмент находится в зоне дыры (например, в самом верху круга) — пропускаем его
            if 0 <= i < hole_segments:
                continue
                
            angle1 = (i / segment_count) * math.pi * 2
            angle2 = ((i + 1) / segment_count) * math.pi * 2
            
            # Координаты точек относительно центра локального тела арены (0, 0)
            x1 = math.cos(angle1) * self.radius
            y1 = math.sin(angle1) * self.radius
            x2 = math.cos(angle2) * self.radius
            y2 = math.sin(angle2) * self.radius
            
            # Создаем сегмент стены, привязанный к нашему вращающемуся телу self.body
            wall_shape = pymunk.Segment(self.body, (x1, y1), (x2, y2), 6)
            wall_shape.elasticity = 0.6  # Чуть уменьшим прыгучесть, чтобы шары предсказуемо скатывались
            wall_shape.friction = 0.3
            
            # Регистрируем форму в физическом пространстве
            self.space_manager.add_object(self.body, wall_shape)  # Передаем None для тела, так как само тело добавим один раз позже
            self.shapes.append(wall_shape)
            

    def draw(self, surface):
        # Чтобы красиво нарисовать вращающуюся арену в Pygame, 
        # нужно учесть текущий угол поворота физического тела (self.body.angle)
        current_angle = self.body.angle
        
        for shape in self.shapes:
            # Получаем локальные координаты точек сегмента
            a = shape.a
            b = shape.b
            
            # Поворачиваем точки по тригонометрической матрице с учетом угла тела
            def rotate_point(pt, angle):
                x = pt.x * math.cos(angle) - pt.y * math.sin(angle)
                y = pt.x * math.sin(angle) + pt.y * math.cos(angle)
                return int(x + self.center[0]), int(y + self.center[1])
                
            screen_a = rotate_point(a, current_angle)
            screen_b = rotate_point(b, current_angle)
            
            # Рисуем линию сегмента стены на экране
            pygame.draw.line(surface, (80, 100, 140), screen_a, screen_b, 6)
