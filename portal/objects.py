import pygame
import math
class PhysicsObject:
    def __init__(self, pos, size, type="cube"):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)
        self.size = pygame.Vector2(size)
        self.type = type
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
        self.on_ground = False
        
        # Physics properties
        self.gravity = 1000
        self.mass = 1.0
        self.restitution = 0.3  # Bounciness
        self.friction = 0.8
    
    def update(self, dt, level):
        # Apply gravity
        self.vel.y += self.gravity * dt
        
        # Apply friction if on ground
        if self.on_ground:
            self.vel.x *= (1 - self.friction * dt)
        
        # Update position
        self.pos.x += self.vel.x * dt
        self.rect.x = self.pos.x
        self.handle_collisions(level, 'horizontal')
        
        self.pos.y += self.vel.y * dt
        self.rect.y = self.pos.y
        self.on_ground = False
        self.handle_collisions(level, 'vertical')
        
        # Check for portal transitions
        self.check_portal_transition(level)
    
    def handle_collisions(self, level, direction):
        # Similar to player collision handling
        for obstacle in level.obstacles:
            if self.rect.colliderect(obstacle.rect):
                if direction == 'horizontal':
                    if self.vel.x > 0:  # Moving right
                        self.pos.x = obstacle.rect.left - self.size.x
                    elif self.vel.x < 0:  # Moving left
                        self.pos.x = obstacle.rect.right
                    # Bounce with reduced velocity
                    self.vel.x = -self.vel.x * self.restitution
                
                elif direction == 'vertical':
                    if self.vel.y > 0:  # Moving down
                        self.pos.y = obstacle.rect.top - self.size.y
                        self.on_ground = True
                        self.vel.y = 0
                    elif self.vel.y < 0:  # Moving up
                        self.pos.y = obstacle.rect.bottom
                        # Bounce with reduced velocity
                        self.vel.y = -self.vel.y * self.restitution
        
        # Update rect after position changes
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
    
    def check_portal_transition(self, level):
        # Check if object is entering a portal
        # We'll need the portals from the player or level
        blue_portal = level.player.blue_portal
        orange_portal = level.player.orange_portal
        
        if blue_portal and orange_portal:
            if self.rect.colliderect(blue_portal.rect):
                self.teleport_through_portal(blue_portal, orange_portal)
            elif self.rect.colliderect(orange_portal.rect):
                self.teleport_through_portal(orange_portal, blue_portal)
    
    def teleport_through_portal(self, entry_portal, exit_portal):
        """Teleport object from entry portal to exit portal with proper physics."""
        # Calculate how far the object is through the entry portal
        # This helps determine where it should appear on the other side
        
        entry_center = pygame.Vector2(entry_portal.rect.center)
        obj_center = pygame.Vector2(self.rect.center)
        
        # Calculate penetration depth and direction
        if entry_portal.orientation == "vertical":
            # For vertical portals, measure horizontal penetration
            penetration_dir = 1 if self.vel.x > 0 else -1
            penetration_dist = abs(entry_center.x - obj_center.x)
        else:  # horizontal portal
            # For horizontal portals, measure vertical penetration
            penetration_dir = 1 if self.vel.y > 0 else -1
            penetration_dist = abs(entry_center.y - obj_center.y)
        
        # Calculate angle difference for rotation
        angle_diff = exit_portal.angle - entry_portal.angle
        angle_rad = math.radians(angle_diff)
        
        # Calculate new position relative to exit portal
        if exit_portal.orientation == "vertical":
            # Place object at proper distance from vertical exit portal
            self.pos.x = exit_portal.pos.x + (self.size.x/2 * penetration_dir) 
            
            # Center vertically relative to portal height
            offset_y = obj_center.y - entry_center.y
            self.pos.y = exit_portal.pos.y + exit_portal.height/2 - self.size.y/2 + offset_y
        else:  # horizontal portal
            # Center horizontally relative to portal width
            offset_x = obj_center.x - entry_center.x
            self.pos.x = exit_portal.pos.x + exit_portal.width/2 - self.size.x/2 + offset_x
            
            # Place object at proper distance from horizontal exit portal
            self.pos.y = exit_portal.pos.y + (self.size.y/2 * penetration_dir)
        
        # Update rectangle position
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        
        # Transform velocity based on portal orientation difference
        old_vel = pygame.Vector2(self.vel.x, self.vel.y)
        
        # Rotate velocity vector according to difference in portal orientations
        self.vel.x = old_vel.x * math.cos(angle_rad) - old_vel.y * math.sin(angle_rad)
        self.vel.y = old_vel.x * math.sin(angle_rad) + old_vel.y * math.cos(angle_rad)
        
        # Apply a small boost to prevent getting stuck in portal
        self.vel *= 1.05
    
    def render(self, screen, camera):
        # Draw the physics object
        camera_pos = camera.apply(self.pos)
        
        if self.type == "cube":
            color = (200, 100, 50)  # Brown-ish for wooden crate
        elif self.type == "metal_cube":
            color = (150, 150, 150)  # Gray for metal
        else:
            color = (255, 255, 255)  # White default
            
        pygame.draw.rect(screen, color, 
                        (camera_pos.x, camera_pos.y, self.size.x, self.size.y))

class Switch:
    def __init__(self, pos, size=(40, 10)):
        self.pos = pygame.Vector2(pos)
        self.size = pygame.Vector2(size)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
        self.activated = False
        self.activation_timer = 0  # For visual feedback
    
    def update(self, dt, physics_objects):
        was_activated = self.activated
        self.activated = False
        
        # Check if any physics object is on the switch
        for obj in physics_objects:
            if self.rect.colliderect(obj.rect):
                self.activated = True
                break
        
        # Reset or increment activation timer for visual effect
        if self.activated:
            self.activation_timer = min(1.0, self.activation_timer + dt * 2)
        else:
            self.activation_timer = max(0.0, self.activation_timer - dt * 2)
            
        # Return true if activation state changed
        return was_activated != self.activated
    
    def render(self, screen, camera):
        camera_pos = camera.apply(self.pos)
        
        # Draw base
        pygame.draw.rect(screen, (100, 100, 100), 
                       (camera_pos.x, camera_pos.y + 5, self.size.x, self.size.y))
        
        # Draw button - changes height based on activation
        button_height = 5 - int(self.activation_timer * 4)
        button_color = (255, 0, 0) if not self.activated else (0, 255, 0)
        
        pygame.draw.rect(screen, button_color, 
                       (camera_pos.x + 5, camera_pos.y + button_height, 
                        self.size.x - 10, 5))