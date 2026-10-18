import math
import random
import pygame
import pymunk

class BaseArena:
    """Базовый класс для всех арен. Любая новая арена должна наследоваться от него."""
    def __init__(self, space_manager, center_x, center_y, radius):
        self.space_manager = space_manager
        self.center = (center_x, center_y)
        self.radius = radius
        self.body = None
        self.shapes = []

    def update(self, dt):
        """Метод для обновления внутренней логики арены (если нужно что-то двигать вручную)."""
        pass

    def is_inside(self, ball_pos):
        """Каждая арена сама решает, находится ли шарик внутри её границ."""
        raise NotImplementedError("Каждая арена должна реализовать метод is_inside!")

    def draw(self, surface):
        """Отрисовка элементов арены."""
        raise NotImplementedError("Каждая арена должна реализовать метод draw!")

    def destroy(self):
        """Безопасное удаление всех физических тел и форм арены."""
        for shape in self.shapes:
            self.space_manager.remove_object(None, shape)
        if self.body:
            self.space_manager.remove_object(self.body, None)
        self.shapes.clear()


class ClassicRotatingArena(BaseArena):
    """Классическая круглая вращающаяся арена с отверстием."""
    WALL_THICKNESS = 6
    ELASTICITY = 0.6
    FRICTION = 0.3

    def __init__(self, space_manager, center_x, center_y, radius):
        super().__init__(space_manager, center_x, center_y, radius)
        
        self.rotation_speed = random.uniform(0.3, 0.8)
        self.direction = random.choice([1, -1])
        self.hole_angle_deg = random.randint(15, 25)
        
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.center
        self.body.angular_velocity = self.rotation_speed * self.direction
        
        self.space_manager.add_object(self.body, None)
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
            
            self.space_manager.add_object(None, wall_shape)  
            self.shapes.append(wall_shape)

    def is_inside(self, ball_pos):
        cx, cy = self.center
        dx = ball_pos.x - cx
        dy = ball_pos.y - cy
        distance = math.sqrt(dx*dx + dy*dy)
        return distance <= (self.radius + self.WALL_THICKNESS)

    def draw(self, surface):
        current_angle = self.body.angle
        cx, cy = self.center
        for shape in self.shapes:
            a, b = shape.a, shape.b
            
            def rotate_point(pt, angle):
                x = pt.x * math.cos(angle) - pt.y * math.sin(angle)
                y = pt.x * math.sin(angle) + pt.y * math.cos(angle)
                return int(x + cx), int(y + cy)
                
            screen_a = rotate_point(a, current_angle)
            screen_b = rotate_point(b, current_angle)
            pygame.draw.line(surface, (80, 100, 140), screen_a, screen_b, self.WALL_THICKNESS)


class PropellerRotatingArena(ClassicRotatingArena):
    """Круглая арена, внутри которой встроен вращающийся пропеллер."""
    BLADE_LENGTH_RATIO = 1 
    PROP_THICKNESS = 6     
    PROP_ELASTICITY = 0.8
    PROP_FRICTION = 0.15

    def __init__(self, space_manager, center_x, center_y, radius):
        # Строим внешнее кольцо через конструктор родителя
        super().__init__(space_manager, center_x, center_y, radius)
        
        # Настройки пропеллера
        self.prop_speed = random.uniform(1.0, 1.0)
        self.prop_direction = random.choice([1, -1])
        
        self.prop_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.prop_body.position = self.center
        # Пропеллер крутится в противоположную от арены сторону (как у тебя в коде)
        self.prop_body.angular_velocity = self.prop_speed * (-self.direction)
        
        self.space_manager.add_object(self.prop_body, None)
        self.prop_shapes = []
        self._build_propeller()

    def _build_propeller(self):
        blade_length = self.radius * self.BLADE_LENGTH_RATIO
        directions = [
            ((0, 0), (0, blade_length)),
            ((0, 0), (0, -blade_length)),
            ((0, 0), (blade_length, 0)),
            ((0, 0), (-blade_length, 0))
        ]

        for a, b in directions:
            blade_shape = pymunk.Segment(self.prop_body, a, b, self.PROP_THICKNESS)
            blade_shape.elasticity = self.PROP_ELASTICITY
            blade_shape.friction = self.PROP_FRICTION
            
            self.space_manager.add_object(None, blade_shape)
            self.prop_shapes.append(blade_shape)

    def draw(self, surface):
        # Рисуем кольцо (базовый метод)
        super().draw(surface)
        
        # Рисуем пропеллер
        cx, cy = self.center
        current_angle = self.prop_body.angle
        for shape in self.prop_shapes:
            a, b = shape.a, shape.b
            
            def rotate_point(pt, angle):
                x = pt.x * math.cos(angle) - pt.y * math.sin(angle)
                y = pt.x * math.sin(angle) + pt.y * math.cos(angle)
                return int(x + cx), int(y + cy)

            screen_a = rotate_point(a, current_angle)
            screen_b = rotate_point(b, current_angle)
            pygame.draw.line(surface, (235, 120, 40), screen_a, screen_b, self.PROP_THICKNESS)

    def destroy(self):
        # Сначала уничтожаем формы пропеллера и его тело
        for shape in self.prop_shapes:
            self.space_manager.remove_object(None, shape)
        if self.prop_body:
            self.space_manager.remove_object(self.prop_body, None)
        self.prop_shapes.clear()
        # Затем чистим всё остальное (кольцо)
        super().destroy()


# Список (реестр) всех доступных арен для автоматического рандома
ARENA_REGISTRY = [
    ClassicRotatingArena,
    PropellerRotatingArena
]
