import pygame
import math
import random

class Portal:
    def __init__(self, pos, orientation, color):
        self.pos = pygame.Vector2(pos)
        self.orientation = orientation  # "vertical" or "horizontal"
        self.color = color  # "blue" or "orange"
        
        # Portal dimensions based on orientation
        if orientation == "vertical":
            self.width = 20
            self.height = 80
        else:  # horizontal
            self.width = 80
            self.height = 20
        
        # Create rect for collision detection (centered on position)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.width, self.height)
        
        # Portal orientation angle in degrees (0 is right, 90 is down)
        self.angle = 90 if orientation == "vertical" else 0
        
        # Visual effects
        self.particles = []
        self.animation_timer = 0
    
    def update(self, dt):
        # Update portal animation
        self.animation_timer += dt
        
        # Update particles for visual effect
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.lifetime <= 0:
                self.particles.remove(particle)
        
        # Add new particles
        if len(self.particles) < 20 and pygame.time.get_ticks() % 100 < 20:
            self.add_particle()
    
    def add_particle(self):
        # Add visual particle for portal effect
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-30, 30) if self.orientation == "vertical" else random.randint(-10, 10)
        self.particles.append(PortalParticle(
            self.pos.x + offset_x,
            self.pos.y + offset_y,
            self.color
        ))
    
    def render(self, screen, camera):
        # Apply camera transformation
        portal_pos = camera.apply(self.pos)
        
        # Draw portal base 
        color_rgb = (0, 0, 255) if self.color == "blue" else (255, 165, 0)
        pygame.draw.rect(screen, color_rgb, 
                        (portal_pos.x, portal_pos.y, self.width, self.height))
        
        # Draw inner portal effect (more bright)
        inner_color = (100, 100, 255) if self.color == "blue" else (255, 200, 100)
        inner_rect = pygame.Rect(portal_pos.x + 2, portal_pos.y + 2, 
                                self.width - 4, self.height - 4)
        pygame.draw.rect(screen, inner_color, inner_rect)
        
        # Draw portal shine effect
        shine_pos = (self.animation_timer * 5) % (self.width + self.height)
        if self.orientation == "vertical":
            pygame.draw.line(screen, (255, 255, 255, 150), 
                           (portal_pos.x, portal_pos.y + shine_pos), 
                           (portal_pos.x + self.width, portal_pos.y + shine_pos), 2)
        else:
            pygame.draw.line(screen, (255, 255, 255, 150), 
                           (portal_pos.x + shine_pos, portal_pos.y), 
                           (portal_pos.x + shine_pos, portal_pos.y + self.height), 2)
        
        # Draw particles
        for particle in self.particles:
            particle.render(screen, camera)

class PortalParticle:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.color = color
        self.lifetime = 1.0  # Seconds
        self.radius = random.randint(2, 5)
        
        # Random movement
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(10, 30)
        self.vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
    
    def update(self, dt):
        self.pos += self.vel * dt
        self.lifetime -= dt
        self.radius = max(0, self.radius - dt * 2)
    
    def render(self, screen, camera):
        # Only render if still alive
        if self.lifetime <= 0:
            return
            
        # Apply camera
        render_pos = camera.apply(self.pos)
        
        # Draw particle
        color_rgb = (0, 0, 255) if self.color == "blue" else (255, 165, 0)
        # Add alpha based on lifetime
        alpha = int(255 * self.lifetime)
        color_rgba = (*color_rgb, alpha)
        
        # Create a surface with per-pixel alpha
        particle_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color_rgba, 
                         (self.radius, self.radius), self.radius)
        
        # Blit to screen
        screen.blit(particle_surface, 
                  (render_pos.x - self.radius, render_pos.y - self.radius))