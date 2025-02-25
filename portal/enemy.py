import pygame
import math
import random

class Enemy:
    def __init__(self, pos, patrol_points=None):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)
        self.size = pygame.Vector2(30, 30)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
        
        # AI properties
        self.patrol_points = patrol_points or [self.pos]
        self.current_target = 0
        self.speed = 100
        self.detection_range = 300
        self.state = "patrol"  # "patrol", "chase", "confused"
        self.confusion_timer = 0
        
        # For portal transition tracking
        self.last_portal_time = 0
        self.portal_cooldown = 1.0  # Seconds before can use another portal
    
    def update(self, dt, level):
        # Update state based on player position
        player_pos = level.player.pos
        dist_to_player = (player_pos - self.pos).length()
        
        # State machine
        if self.state == "confused":
            self.confusion_timer -= dt
            if self.confusion_timer <= 0:
                self.state = "patrol"
        elif dist_to_player < self.detection_range:
            # Check if player is visible (no obstacles in the way)
            if self.can_see_player(player_pos, level):
                self.state = "chase"
            else:
                self.state = "patrol"
        else:
            self.state = "patrol"
        
        # Act based on current state
        if self.state == "patrol":
            self.patrol(dt)
        elif self.state == "chase":
            self.chase_player(player_pos, dt)
        else:  # confused
            # Random movement when confused
            if pygame.time.get_ticks() % 1000 < 50:
                self.vel = pygame.Vector2(
                    random.uniform(-self.speed, self.speed),
                    random.uniform(-self.speed, self.speed)
                )
        
        # Apply velocity
        self.pos += self.vel * dt
        self.rect.center = self.pos
        
        # Handle collisions with obstacles
        self.handle_collisions(level)
        
        # Check for portal transitions
        self.check_portal_transition(level)
    
    def patrol(self, dt):
        if not self.patrol_points:
            return
            
        # Move toward current patrol point
        target = self.patrol_points[self.current_target]
        direction = pygame.Vector2(target) - self.pos
        
        if direction.length() < 10:  # Close enough to target
            # Move to next patrol point
            self.current_target = (self.current_target + 1) % len(self.patrol_points)
        else:
            # Move toward target
            if direction.length() > 0:
                direction.normalize_ip()
            self.vel = direction * self.speed
    
    def chase_player(self, player_pos, dt):
        # Move toward player
        direction = pygame.Vector2(player_pos) - self.pos
        
        if direction.length() > 0:
            direction.normalize_ip()
        self.vel = direction * self.speed
    
    def can_see_player(self, player_pos, level):
        # Simple line-of-sight check
        # In a real implementation, this would check for obstacles between enemy and player
        return True
    
    def handle_collisions(self, level):
        # Check collisions with obstacles
        for obstacle in level.obstacles:
            if self.rect.colliderect(obstacle.rect):
                # Simple bounce behavior
                overlap_x = min(
                    self.rect.right - obstacle.rect.left,
                    obstacle.rect.right - self.rect.left
                )
                overlap_y = min(
                    self.rect.bottom - obstacle.rect.top,
                    obstacle.rect.bottom - self.rect.top
                )
                
                if overlap_x < overlap_y:
                    # Horizontal collision
                    if self.rect.centerx < obstacle.rect.centerx:
                        self.pos.x -= overlap_x
                    else:
                        self.pos.x += overlap_x
                    self.vel.x = -self.vel.x * 0.8
                else:
                    # Vertical collision
                    if self.rect.centery < obstacle.rect.centery:
                        self.pos.y -= overlap_y
                    else:
                        self.pos.y += overlap_y
                    self.vel.y = -self.vel.y * 0.8
                
                # Update rect after position change
                self.rect.center = self.pos
    
    def check_portal_transition(self, level):
        # Similar to player portal transition but with confusion after going through
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_portal_time < self.portal_cooldown:
            return
            
        blue_portal = level.player.blue_portal
        orange_portal = level.player.orange_portal
        
        if blue_portal and orange_portal:
            if self.rect.colliderect(blue_portal.rect):
                self.teleport_through_portal(blue_portal, orange_portal)
                self.become_confused()
            elif self.rect.colliderect(orange_portal.rect):
                self.teleport_through_portal(orange_portal, blue_portal)
                self.become_confused()
    
    def teleport_through_portal(self, entry_portal, exit_portal):
        # Position at exit portal
        self.pos.x = exit_portal.pos.x
        self.pos.y = exit_portal.pos.y
        self.rect.center = self.pos
        
        # Transform velocity (similar to other objects)
        angle_diff = exit_portal.angle - entry_portal.angle
        angle_rad = math.radians(angle_diff)
        
        old_vel = pygame.Vector2(self.vel.x, self.vel.y)
        self.vel.x = old_vel.x * math.cos(angle_rad) - old_vel.y * math.sin(angle_rad)
        self.vel.y = old_vel.x * math.sin(angle_rad) + old_vel.y * math.cos(angle_rad)
        
        # Mark the time of the portal use
        self.last_portal_time = pygame.time.get_ticks() / 1000.0
    
    def become_confused(self):
        self.state = "confused"
        self.confusion_timer = 3.0  # 3 seconds of confusion
    
    def render(self, screen, camera):
        camera_pos = camera.apply(self.pos)
        
        # Draw different colors based on state
        if self.state == "patrol":
            color = (0, 100, 200)  # Blue
        elif self.state == "chase":
            color = (200, 0, 0)  # Red
        else:  # confused
            color = (200, 200, 0)  # Yellow
            
        pygame.draw.circle(screen, color, 
                         (int(camera_pos.x), int(camera_pos.y)), 
                         int(self.size.x / 2))