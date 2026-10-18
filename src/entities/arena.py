import math
import random
import pygame
import pymunk

class RotatingHoleArena:
    WALL_THICKNESS = 6
    ELASTICITY = 0.6
    FRICTION = 0.3

    def __init__(self, space_manager, center_x, center_y, radius):
        self.space_manager = space_manager
        self.center = (center_x, center_y)
        self.radius = radius # Принимает адаптивный радиус из game.py
        
        # Рандомизация параметров вращения и дыры/отверстия
        self.rotation_speed = random.uniform(0.3, 0.8)
        self.direction = random.choice([1, -1])
        self.hole_angle_deg = random.randint(15, 25)
        
        # Создаем кинематическое тело
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.center
        self.body.angular_velocity = self.rotation_speed * self.direction
        
        # Регистрируем тело в физическом мире ОДИН раз до цикла
        self.space_manager.add_object(self.body, None)
        
        self.shapes = []
        self._build_arena_with_hole()

    def _build_arena_with_hole(self):
        segment_count = 90  
        hole_segments = int(segment_count * (self.hole_angle_deg / 360.0))
        
        for i in range(segment_count):
            if 0 <= i < hole_segments:
                continue
                
            angle1 = (i / segment_count) * math.pi * 2
            angle2 = ((i + 1) / segment_count) * math.pi * 2
            
            x1 = math.cos(angle1) * self.radius
            y1 = math.sin(angle1) * self.radius
            x2 = math.cos(angle2) * self.radius
            y2 = math.sin(angle2) * self.radius
            
            wall_shape = pymunk.Segment(self.body, (x1, y1), (x2, y2), self.WALL_THICKNESS)
            wall_shape.elasticity = self.ELASTICITY  
            wall_shape.friction = self.FRICTION
            
            # Добавляем в пространство только форму (коллайдер), передавая None вместо тела
            self.space_manager.add_object(None, wall_shape)  
            self.shapes.append(wall_shape)
            
    def destroy(self):
        # Удаляем все формы стен
        for shape in self.shapes:
            self.space_manager.remove_object(None, shape)
        # Удаляем само тело арены
        self.space_manager.remove_object(self.body, None)
        self.shapes.clear()

    def draw(self, surface):
        current_angle = self.body.angle
        for shape in self.shapes:
            a = shape.a
            b = shape.b
            
            def rotate_point(pt, angle):
                x = pt.x * math.cos(angle) - pt.y * math.sin(angle)
                y = pt.x * math.sin(angle) + pt.y * math.cos(angle)
                return int(x + self.center[0]), int(y + self.center[1])
                
            screen_a = rotate_point(a, current_angle)
            screen_b = rotate_point(b, current_angle)
            pygame.draw.line(surface, (80, 100, 140), screen_a, screen_b, self.WALL_THICKNESS)

    def is_inside(self, ball_pos):
        """Проверяет, находится ли шар внутри круглых границ арены."""
        cx, cy = self.center
        dx = ball_pos.x - cx
        dy = ball_pos.y - cy
        distance = math.sqrt(dx*dx + dy*dy)
        # Возвращаем True, если шар внутри. Если вылетел за радиус — False.
        return distance <= (self.radius + self.WALL_THICKNESS)



class CentralPropeller:
    BLADE_LENGTH_RATIO = 1 
    THICKNESS = 6     
    ELASTICITY = 0.8
    FRICTION = 0.15
    
    MIN_SPEED = 1
    MAX_SPEED = 1

    def __init__(self, space_manager, center_x, center_y, arena_radius):
        self.space_manager = space_manager
        self.center = (center_x, center_y)
        
        # Динамически вычисляем длину лопасти на основе переданного радиуса арены
        self.blade_length = arena_radius * self.BLADE_LENGTH_RATIO

        self.rotation_speed = random.uniform(self.MIN_SPEED, self.MAX_SPEED)
        self.direction = random.choice([1, -1])

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.center
        self.body.angular_velocity = self.rotation_speed * self.direction

        # Регистрируем тело ОДИН раз
        self.space_manager.add_object(self.body, None)

        self.shapes = []
        self._build_propeller()

    def _build_propeller(self):
        directions = [
            ((0, 0), (0, self.blade_length)),
            ((0, 0), (0, -self.blade_length)),
            ((0, 0), (self.blade_length, 0)),
            ((0, 0), (-self.blade_length, 0))
        ]

        for a, b in directions:
            blade_shape = pymunk.Segment(self.body, a, b, self.THICKNESS)
            blade_shape.elasticity = self.ELASTICITY
            blade_shape.friction = self.FRICTION
            
            self.space_manager.add_object(None, blade_shape)
            self.shapes.append(blade_shape)


    def destroy(self):
        for shape in self.shapes:
            self.space_manager.remove_object(None, shape)
        self.space_manager.remove_object(self.body, None)
        self.shapes.clear()

    def draw(self, surface):
        current_angle = self.body.angle
        cx, cy = self.center
        
        for shape in self.shapes:
            a = shape.a
            b = shape.b

            def rotate_point(pt, angle):
                x = pt.x * math.cos(angle) - pt.y * math.sin(angle)
                y = pt.x * math.sin(angle) + pt.y * math.cos(angle)
                return int(x + cx), int(y + cy)

            screen_a = rotate_point(a, current_angle)
            screen_b = rotate_point(b, current_angle)
            
            pygame.draw.line(surface, (235, 120, 40), screen_a, screen_b, self.THICKNESS)