import pymunk

class SpaceManager:
    def __init__(self, gravity_y=6000):
        self.gravity_y = gravity_y
        self.space = pymunk.Space()
        self.space.gravity = (0, self.gravity_y)
        
    def update(self, dt):
        self.space.step(dt)
        
    def add_object(self, body, shape):
        if body and body not in self.space.bodies:
            self.space.add(body)
            
        if shape and shape not in self.space.shapes:
            self.space.add(shape)
        
    def remove_object(self, body, shape):
        # Проверяем наличие перед удалением, чтобы избежать KeyError
        if shape and shape in self.space.shapes:
            self.space.remove(shape)
        if body and body in self.space.bodies:
            self.space.remove(body)

    def clear_all(self):
        """Полностью и безопасно очищает физическое пространство для загрузки новой сцены."""
        for shape in list(self.space.shapes):
            self.space.remove(shape)
        for body in list(self.space.bodies):
            self.space.remove(body)
