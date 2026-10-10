import pymunk

class SpaceManager:
    def __init__(self, gravity_y=500):
        self.space = pymunk.Space()
        self.space.gravity = (0, gravity_y)
        
    def update(self, dt):
        self.space.step(dt)
        
    def add_object(self, body, shape):
        # Проверяем, добавлено ли уже тело в физический мир Pymunk
        # Если тела нет в пространстве и оно передано — добавляем
        if body and body not in self.space.bodies:
            self.space.add(body)
            
        # Форму (коллайдер) добавляем всегда
        if shape and shape not in self.space.shapes:
            self.space.add(shape)
        
    def remove_object(self, body, shape):
        if shape and shape in self.space.shapes:
            self.space.remove(shape)
        if body and body in self.space.bodies:
            self.space.remove(body)
