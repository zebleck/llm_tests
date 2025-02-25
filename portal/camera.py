import pygame

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset = pygame.Vector2(0, 0)
        self.target = None
        
        # Camera settings
        self.lerp_speed = 5.0  # Controls how quickly camera follows target
    
    def update(self, target):
        self.target = target
        
        # Calculate the desired center position
        desired_x = target.pos.x + target.size.x/2 - self.width/2
        desired_y = target.pos.y + target.size.y/2 - self.height/2
        
        # Lerp (linear interpolation) current position to desired position
        self.offset.x += (desired_x - self.offset.x) * self.lerp_speed * 0.1
        self.offset.y += (desired_y - self.offset.y) * self.lerp_speed * 0.1
    
    def apply(self, pos):
        # Convert world coordinates to screen coordinates
        return pygame.Vector2(pos.x - self.offset.x, pos.y - self.offset.y)