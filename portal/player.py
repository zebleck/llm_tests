import pygame
import math
from portal import Portal

class Player:
    def __init__(self, start_pos):
        self.pos = pygame.Vector2(start_pos)
        self.vel = pygame.Vector2(0, 0)
        self.size = pygame.Vector2(32, 64)  # Player hitbox
        self.on_ground = False
        self.facing_right = True
        
        # Portal-related attributes
        self.blue_portal = None
        self.orange_portal = None
        
        # Movement parameters
        self.speed = 300
        self.jump_strength = 600
        self.gravity = 1500
        
    def reset(self, start_pos):
        self.pos = pygame.Vector2(start_pos)
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
    
    def handle_event(self, event, level):
        # Handle portal creation
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Get mouse position in screen coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Try to get camera offset from level, otherwise use default (0,0)
            camera_offset_x = 0
            camera_offset_y = 0
            
            # This checks if camera exists in the level before using it
            if hasattr(level, 'camera') and level.camera:
                camera_offset_x = level.camera.offset.x
                camera_offset_y = level.camera.offset.y
            
            # Convert to world coordinates
            world_x = mouse_x + camera_offset_x
            world_y = mouse_y + camera_offset_y
            
            # Create appropriate portal based on mouse button
            if event.button == 1:  # Left mouse button - blue portal
                self.blue_portal = self.create_portal((world_x, world_y), "blue", level)
            elif event.button == 3:  # Right mouse button - orange portal
                self.orange_portal = self.create_portal((world_x, world_y), "orange", level)
    
    def create_portal(self, target_pos, color, level):
        # Cast a ray from player position to target position (mouse click)
        # to find where it hits a wall
        hit_pos, hit_normal, hit_obstacle = self.raycast_to_wall(self.pos, target_pos, level)
        
        if hit_pos and hit_obstacle and hit_obstacle.allows_portals:
            # Determine portal orientation based on the hit normal
            if abs(hit_normal[0]) > abs(hit_normal[1]):
                # Hit a vertical wall (normal points horizontally)
                orientation = "vertical"
            else:
                # Hit a horizontal wall (normal points vertically)
                orientation = "horizontal"
            
            # Create portal at the hit position
            portal = Portal(hit_pos, orientation, color)
            
            # Adjust portal position to be embedded in the wall properly
            if orientation == "vertical":
                # Position portal flush with the wall
                if hit_normal[0] < 0:  # Right-facing wall (normal points left)
                    portal.pos.x -= portal.width/2
                else:  # Left-facing wall (normal points right)
                    portal.pos.x -= portal.width/2
                # Center vertically
                portal.pos.y -= portal.height/2
            else:
                # Position portal flush with the floor/ceiling
                if hit_normal[1] < 0:  # Floor (normal points up)
                    portal.pos.y -= portal.height/2
                else:  # Ceiling (normal points down)
                    portal.pos.y -= portal.height/2
                # Center horizontally
                portal.pos.x -= portal.width/2
            
            # Update portal rect
            portal.rect = pygame.Rect(portal.pos.x, portal.pos.y, portal.width, portal.height)
            return portal
        
        return None

    def raycast_to_wall(self, start_pos, end_pos, level):
        """Cast a ray from start_pos toward end_pos and return where it hits a wall."""
        # Direction vector from player to target
        direction = pygame.Vector2(end_pos[0] - start_pos.x, end_pos[1] - start_pos.y)
        
        if direction.length() == 0:
            return None, None, None
        
        direction.normalize_ip()
        
        # Start from player position
        current_pos = pygame.Vector2(start_pos)
        
        # Cast the ray in small steps
        step_size = 5
        max_distance = 1000  # Maximum raycast distance
        
        for _ in range(int(max_distance / step_size)):
            # Move along the ray
            current_pos += direction * step_size
            
            # Check if current position is inside any obstacle
            for obstacle in level.obstacles:
                if obstacle.rect.collidepoint(current_pos):
                    # Found a hit - determine the normal of the wall
                    wall_normal = self.calculate_wall_normal(current_pos, obstacle)
                    
                    # Return hit position, normal, and the obstacle hit
                    return current_pos, wall_normal, obstacle
        
        # No hit found
        return None, None, None

    def calculate_wall_normal(self, hit_pos, obstacle):
        """Calculate the normal vector of the wall at the hit position."""
        # Simplified approach: check which side of the obstacle was hit
        # by comparing distances to each edge
        rect = obstacle.rect
        
        # Calculate distances to each edge
        dist_left = abs(hit_pos.x - rect.left)
        dist_right = abs(hit_pos.x - rect.right)
        dist_top = abs(hit_pos.y - rect.top)
        dist_bottom = abs(hit_pos.y - rect.bottom)
        
        # Find the closest edge
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        
        # Return normal based on closest edge
        if min_dist == dist_left:
            return (-1, 0)  # Left edge, normal points left
        elif min_dist == dist_right:
            return (1, 0)   # Right edge, normal points right
        elif min_dist == dist_top:
            return (0, -1)  # Top edge, normal points up
        else:
            return (0, 1)   # Bottom edge, normal points down
    
    def update(self, dt, level):
        # Handle keyboard input for movement
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.vel.x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel.x = -self.speed
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel.x = self.speed
            self.facing_right = True
            
        # Jumping
        if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel.y = -self.jump_strength
            self.on_ground = False
        
        # Apply gravity
        self.vel.y += self.gravity * dt
        
        # Move player and handle collisions
        self.pos.x += self.vel.x * dt
        # Check horizontal collisions
        self.handle_collisions(level, 'horizontal')
        
        self.pos.y += self.vel.y * dt
        # Check vertical collisions
        self.on_ground = False
        self.handle_collisions(level, 'vertical')
        
        # Check for portal transitions
        self.check_portal_transition(level)
    
    def handle_collisions(self, level, direction):
        # Simplified collision handling
        # Get player rect
        player_rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
        
        # Check collisions with level obstacles
        for obstacle in level.obstacles:
            if player_rect.colliderect(obstacle.rect):
                if direction == 'horizontal':
                    # Fix x position
                    if self.vel.x > 0:  # Moving right
                        self.pos.x = obstacle.rect.left - self.size.x
                    elif self.vel.x < 0:  # Moving left
                        self.pos.x = obstacle.rect.right
                    self.vel.x = 0
                elif direction == 'vertical':
                    if self.vel.y > 0:  # Moving down
                        self.pos.y = obstacle.rect.top - self.size.y
                        self.on_ground = True
                        self.vel.y = 0
                    elif self.vel.y < 0:  # Moving up
                        self.pos.y = obstacle.rect.bottom
                        self.vel.y = 0
    
    def check_portal_transition(self, level):
        # Check if player is entering a portal
        player_rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
        
        # Check blue portal
        if self.blue_portal and self.orange_portal:
            if player_rect.colliderect(self.blue_portal.rect):
                # Transition to orange portal
                self.teleport_through_portal(self.blue_portal, self.orange_portal)
            elif player_rect.colliderect(self.orange_portal.rect):
                # Transition to blue portal
                self.teleport_through_portal(self.orange_portal, self.blue_portal)
    
    def teleport_through_portal(self, entry_portal, exit_portal):
        """Teleport player from entry portal to exit portal with proper physics."""
        # Calculate player's center position
        player_center = pygame.Vector2(self.pos.x + self.size.x/2, self.pos.y + self.size.y/2)
        entry_center = pygame.Vector2(entry_portal.rect.center)
        
        # Calculate penetration depth and direction
        if entry_portal.orientation == "vertical":
            penetration_dir = 1 if self.vel.x > 0 else -1
            penetration_dist = abs(entry_center.x - player_center.x)
        else:  # horizontal portal
            penetration_dir = 1 if self.vel.y > 0 else -1
            penetration_dist = abs(entry_center.y - player_center.y)
        
        # Calculate angle difference for rotation
        angle_diff = exit_portal.angle - entry_portal.angle
        angle_rad = math.radians(angle_diff)
        
        # Calculate new position relative to exit portal
        if exit_portal.orientation == "vertical":
            # Place player at proper distance from vertical exit portal with safe offset
            offset = 25  # Slightly larger offset for player to prevent clipping
            self.pos.x = exit_portal.pos.x + (offset * penetration_dir)
            
            # Center vertically relative to portal height
            offset_y = player_center.y - entry_center.y
            self.pos.y = exit_portal.pos.y + exit_portal.height/2 - self.size.y/2 + offset_y
        else:  # horizontal portal
            # Center horizontally relative to portal width
            offset_x = player_center.x - entry_center.x
            self.pos.x = exit_portal.pos.x + exit_portal.width/2 - self.size.x/2 + offset_x
            
            # Place player at proper distance from horizontal exit portal
            offset = 25  # Safe offset to prevent clipping
            self.pos.y = exit_portal.pos.y + (offset * penetration_dir)
        
        # Transform velocity based on portal orientation
        old_vel = pygame.Vector2(self.vel.x, self.vel.y)
        
        # Rotate velocity vector
        self.vel.x = old_vel.x * math.cos(angle_rad) - old_vel.y * math.sin(angle_rad)
        self.vel.y = old_vel.x * math.sin(angle_rad) + old_vel.y * math.cos(angle_rad)
        
        # Apply a small boost to prevent getting stuck
        self.vel *= 1.05
    
    def render(self, screen, camera):
        # Draw player - simple rectangle for now
        camera_pos = camera.apply(self.pos)
        pygame.draw.rect(screen, (0, 255, 0), 
                        (camera_pos.x, camera_pos.y, self.size.x, self.size.y))
        
        # Render portals if they exist
        if self.blue_portal:
            self.blue_portal.render(screen, camera)
        if self.orange_portal:
            self.orange_portal.render(screen, camera)