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
        pass

    def is_inside(self, ball_pos):
        raise NotImplementedError("Каждая арена должна реализовать метод is_inside!")

    def draw(self, surface):
        raise NotImplementedError("Каждая арена должна реализовать метод draw!")

    def destroy(self):
        for shape in self.shapes:
            self.space_manager.remove_object(None, shape)
        if self.body:
            self.space_manager.remove_object(self.body, None)
        self.shapes.clear()


class ClassicRotatingArena(BaseArena):
    """Классическая круглая вращающаяся арена с отверстием."""
    WALL_THICKNESS = 34  
    ELASTICITY = 0.6
    FRICTION = 0.3

    def __init__(self, space_manager, center_x, center_y, radius):
        super().__init__(space_manager, center_x, center_y, radius)
        
        self.rotation_speed = random.uniform(0.4, 0.8)
        self.direction = random.choice([1, -1])
        self.hole_angle_deg = random.randint(20, 30)
        
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = self.center
        self.body.angular_velocity = self.rotation_speed * self.direction
        
        self.space_manager.add_object(self.body, None)
        self._build_arena_with_hole()

    def _build_arena_with_hole(self):
        segment_count = 180  # Увеличили плотность для идеальной гладкости физики
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
        
        # Пересчитываем и сглаживаем стыки толстых линий с помощью полигонов трапеций
        for shape in self.shapes:
            a, b = shape.a, shape.b
            
            def rotate_point(pt, angle):
                x = pt.x * math.cos(angle) - pt.y * math.sin(angle)
                y = pt.x * math.sin(angle) + pt.y * math.cos(angle)
                return x + cx, y + cy
                
            ax, ay = rotate_point(a, current_angle)
            bx, by = rotate_point(b, current_angle)
            
            # Находим вектор направления линии и его нормаль для построения идеального прямоугольника
            dx, dy = bx - ax, by - ay
            length = math.sqrt(dx*dx + dy*dy)
            if length == 0: continue
            
            nx, ny = -dy / length, dx / length
            half_t = self.WALL_THICKNESS / 2
            
            # Задаем 4 вершины прямоугольного сегмента стены со скруглением стыков
            p1 = (int(ax - nx * half_t), int(ay - ny * half_t))
            p2 = (int(bx - nx * half_t), int(by - ny * half_t))
            p3 = (int(bx + nx * half_t), int(by + ny * half_t))
            p4 = (int(ax + nx * half_t), int(ay + ny * half_t))
            
            # Рисуем гладкий сегмент
            pygame.draw.polygon(surface, (80, 100, 140), [p1, p2, p3, p4])


class PropellerRotatingArena(ClassicRotatingArena):
    """Круглая арена, внутри которой встроен вращающийся пропеллер."""
    BLADE_LENGTH_RATIO = 1 
    PROP_THICKNESS = 34     # Увеличили толщину пропеллера пропорционально стенам
    PROP_ELASTICITY = 0.8
    PROP_FRICTION = 0.15

    def __init__(self, space_manager, center_x, center_y, radius):
        super().__init__(space_manager, center_x, center_y, radius)
        
        self.prop_speed = random.uniform(1.0, 1.0)
        self.prop_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.prop_body.position = self.center
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
        super().draw(surface)
        
        cx, cy = self.center
        current_angle = self.prop_body.angle
        half_t = self.PROP_THICKNESS / 2
        
        # Исправляем баг косых краев лопастей: рисуем их через ориентированные полигоны
        for shape in self.prop_shapes:
            a, b = shape.a, shape.b
            
            def rotate_point(pt, angle):
                x = pt.x * math.cos(angle) - pt.y * math.sin(angle)
                y = pt.x * math.sin(angle) + pt.y * math.cos(angle)
                return x + cx, y + cy

            ax, ay = rotate_point(a, current_angle)
            bx, by = rotate_point(b, current_angle)
            
            dx, dy = bx - ax, by - ay
            length = math.sqrt(dx*dx + dy*dy)
            if length == 0: continue
            
            nx, ny = -dy / length, dx / length
            
            # Строим четкий прямоугольник лопасти, перпендикулярный углу поворота
            p1 = (int(ax - nx * half_t), int(ay - ny * half_t))
            p2 = (int(bx - nx * half_t), int(by - ny * half_t))
            p3 = (int(bx + nx * half_t), int(by + ny * half_t))
            p4 = (int(ax + nx * half_t), int(ay + ny * half_t))
            
            pygame.draw.polygon(surface, (235, 120, 40), [p1, p2, p3, p4])

    def destroy(self):
        for shape in self.prop_shapes:
            self.space_manager.remove_object(None, shape)
        if self.prop_body:
            self.space_manager.remove_object(self.prop_body, None)
        self.prop_shapes.clear()
        super().destroy()


ARENA_REGISTRY = [
    ClassicRotatingArena,
    PropellerRotatingArena
]
