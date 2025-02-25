import pygame
import json
from objects import PhysicsObject, Switch

class Obstacle:
    def __init__(self, rect, allows_portals=True):
        self.rect = rect
        self.allows_portals = allows_portals  # Can portals be placed on this surface?

class Level:
    def __init__(self, level_number):
        self.level_number = level_number
        self.obstacles = []
        self.physics_objects = []
        self.switches = []
        self.doors = []
        self.player_start_pos = (100, 100)  # Default
        
        # Load level data
        self.load_level(level_number)
        
        # Reference to the player (will be set by the Game class)
        self.player = None
    
    def load_level(self, level_number):
        # In a real implementation, this would load from a file
        # For now, we'll create levels programmatically
        
        if level_number == 0:  # Tutorial level
            # Ground
            self.obstacles.append(Obstacle(pygame.Rect(0, 500, 1000, 100)))
            
            # Walls
            self.obstacles.append(Obstacle(pygame.Rect(0, 0, 50, 500)))
            self.obstacles.append(Obstacle(pygame.Rect(950, 0, 50, 500)))
            
            # Ceiling
            self.obstacles.append(Obstacle(pygame.Rect(0, 0, 1000, 50)))
            
            # Platforms
            self.obstacles.append(Obstacle(pygame.Rect(200, 400, 200, 20)))
            self.obstacles.append(Obstacle(pygame.Rect(600, 300, 200, 20)))
            
            # Portal-resistant wall
            self.obstacles.append(Obstacle(pygame.Rect(450, 300, 50, 200), False))
            
            # Add a cube
            self.physics_objects.append(PhysicsObject((300, 350), (40, 40), "cube"))
            
            # Add a switch
            self.switches.append(Switch((700, 290)))
            
            # Player start position
            self.player_start_pos = (100, 400)
            
        elif level_number == 1:  # Intermediate level
            # More complex level setup here
            pass
            
        elif level_number == 2:  # Advanced level
            # Even more complex level with enemies
            pass
    
    def update(self, dt):
        # Update all physics objects
        for obj in self.physics_objects:
            obj.update(dt, self)
        
        # Update switches and check for activations
        for switch in self.switches:
            if switch.update(dt, self.physics_objects):
                # Switch changed state, handle door opening/closing
                self.handle_switch_activation()
        
        # Update doors
        for door in self.doors:
            door.update(dt)
    
    def handle_switch_activation(self):
        # Check if all switches are activated
        all_activated = all(switch.activated for switch in self.switches)
        
        # Open/close doors accordingly
        for door in self.doors:
            door.set_open(all_activated)
    
    def can_place_portal(self, pos):
        # Check if the position is on a valid surface for portal placement
        # This is a simplified version - a real implementation would do ray casting
        
        for obstacle in self.obstacles:
            if obstacle.rect.collidepoint(pos) and obstacle.allows_portals:
                # For better portal placement, we should check if this is the edge of an obstacle
                # For now, we'll just return True if it hits any valid obstacle
                return True
        
        return False
    
    def is_complete(self):
        # Check if the level is complete
        # For example, player reached the exit
        # This is a placeholder implementation
        return False
    
    def render(self, screen, camera):
        # Render all obstacles
        for obstacle in self.obstacles:
            camera_rect = pygame.Rect(
                obstacle.rect.x - camera.offset.x,
                obstacle.rect.y - camera.offset.y,
                obstacle.rect.width,
                obstacle.rect.height
            )
            
            # Different color for portal-resistant surfaces
            color = (100, 100, 100) if obstacle.allows_portals else (50, 50, 120)
            pygame.draw.rect(screen, color, camera_rect)
        
        # Render all physics objects
        for obj in self.physics_objects:
            obj.render(screen, camera)
        
        # Render switches
        for switch in self.switches:
            switch.render(screen, camera)
        
        # Render doors
        for door in self.doors:
            door.render(screen, camera)