import pygame
import sys
import math
import random
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
G = 6.67  # Gravitational constant (scaled for gameplay)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GREY = (150, 150, 150)

# Game objects
class Earth(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.radius = 40
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.pos = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
        self.mass = 1000
        self.max_health = 100
        self.health = self.max_health
    
    def draw_health_bar(self, screen):
        bar_length = 200
        bar_height = 20
        fill = (self.health / self.max_health) * bar_length
        outline_rect = pygame.Rect(WIDTH // 2 - bar_length // 2, HEIGHT - 30, bar_length, bar_height)
        fill_rect = pygame.Rect(WIDTH // 2 - bar_length // 2, HEIGHT - 30, fill, bar_height)
        pygame.draw.rect(screen, RED, fill_rect)
        pygame.draw.rect(screen, WHITE, outline_rect, 2)

class GravityAttractor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.radius = 15
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=(WIDTH // 4, HEIGHT // 2))
        self.pos = pygame.math.Vector2(WIDTH // 4, HEIGHT // 2)
        self.mass = 800
        self.speed = 5
        
        # Visual indicator for gravitational field
        self.field_radius = 150
        self.field_surface = pygame.Surface((self.field_radius * 2, self.field_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.field_surface, (0, 255, 0, 30), (self.field_radius, self.field_radius), self.field_radius)
    
    def update(self, keys):
        if keys[K_LEFT] or keys[K_a]:
            self.pos.x -= self.speed
        if keys[K_RIGHT] or keys[K_d]:
            self.pos.x += self.speed
        if keys[K_UP] or keys[K_w]:
            self.pos.y -= self.speed
        if keys[K_DOWN] or keys[K_s]:
            self.pos.y += self.speed
        
        # Keep attractor within screen bounds
        self.pos.x = max(self.radius, min(self.pos.x, WIDTH - self.radius))
        self.pos.y = max(self.radius, min(self.pos.y, HEIGHT - self.radius))
        
        self.rect.center = (self.pos.x, self.pos.y)

    def draw_gravitational_field(self, screen):
        field_rect = self.field_surface.get_rect(center=(self.pos.x, self.pos.y))
        screen.blit(self.field_surface, field_rect)

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, position=None, velocity=None):
        super().__init__()
        self.radius = random.randint(10, 25)
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREY, (self.radius, self.radius), self.radius)
        
        # Add some surface details to the asteroid
        for _ in range(3):
            offset = random.randint(3, self.radius - 3)
            angle = random.uniform(0, 2 * math.pi)
            pos_x = self.radius + offset * math.cos(angle)
            pos_y = self.radius + offset * math.sin(angle)
            crater_size = random.randint(2, 5)
            pygame.draw.circle(self.image, (100, 100, 100), (pos_x, pos_y), crater_size)
        
        # Spawn from edge if no position provided
        if position is None:
            side = random.randint(0, 3)  # 0: top, 1: right, 2: bottom, 3: left
            if side == 0:  # top
                x = random.randint(0, WIDTH)
                y = -self.radius
            elif side == 1:  # right
                x = WIDTH + self.radius
                y = random.randint(0, HEIGHT)
            elif side == 2:  # bottom
                x = random.randint(0, WIDTH)
                y = HEIGHT + self.radius
            else:  # left
                x = -self.radius
                y = random.randint(0, HEIGHT)
            position = pygame.math.Vector2(x, y)
        
        self.pos = position
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))
        
        # Initial velocity toward Earth
        if velocity is None:
            direction = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2) - self.pos
            direction = direction.normalize()
            speed = random.uniform(0.8, 2.0)
            self.vel = direction * speed
        else:
            self.vel = velocity
            
        self.mass = self.radius * 10
        self.force_lines = []
    
    def update(self, earth, attractor):
        # Apply gravitational forces
        # Force from Earth
        earth_dir = earth.pos - self.pos
        earth_dist = max(earth_dir.length(), 1)  # Prevent division by zero
        earth_dir = earth_dir.normalize()
        earth_force = G * earth.mass * self.mass / (earth_dist * earth_dist)
        earth_acceleration = earth_dir * earth_force / self.mass
        
        # Force from gravity attractor
        attractor_dir = attractor.pos - self.pos
        attractor_dist = max(attractor_dir.length(), 1)
        
        # Only apply attractor force if asteroid is within field radius
        if attractor_dist < attractor.field_radius + self.radius:
            attractor_dir = attractor_dir.normalize()
            attractor_force = G * attractor.mass * self.mass / (attractor_dist * attractor_dist)
            attractor_acceleration = attractor_dir * attractor_force / self.mass
            
            # Store force line for visualization
            force_magnitude = min(attractor_force / 200, 50)  # Scale for visualization
            line_end = self.pos + attractor_dir * force_magnitude
            self.force_lines = [(self.pos, line_end)]
        else:
            attractor_acceleration = pygame.math.Vector2(0, 0)
            self.force_lines = []
        
        # Apply accelerations to velocity
        self.vel += earth_acceleration + attractor_acceleration
        
        # Update position
        self.pos += self.vel
        self.rect.center = (self.pos.x, self.pos.y)
        
        # Check if out of bounds (fully outside the screen)
        if (self.pos.x < -self.radius * 2 or self.pos.x > WIDTH + self.radius * 2 or 
            self.pos.y < -self.radius * 2 or self.pos.y > HEIGHT + self.radius * 2):
            return True  # Return True if asteroid should be removed
        
        return False
    
    def check_earth_collision(self, earth):
        distance = (earth.pos - self.pos).length()
        return distance < (earth.radius + self.radius)
    
    def draw_force_lines(self, screen):
        for start, end in self.force_lines:
            pygame.draw.line(screen, GREEN, (start.x, start.y), (end.x, end.y), 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gravity Defender")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game objects
        self.earth = Earth()
        self.attractor = GravityAttractor()
        self.asteroids = pygame.sprite.Group()
        
        # Game state
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.spawn_delay = 2000  # milliseconds
        self.game_over = False
        self.deflected_count = 0
        
        # Load sounds
        try:
            self.collision_sound = pygame.mixer.Sound('collision.wav')
            self.deflection_sound = pygame.mixer.Sound('deflection.wav')
            pygame.mixer.music.load('background.mp3')
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # Loop background music
        except:
            print("Sound files not found. Continuing without sound.")
            self.collision_sound = None
            self.deflection_sound = None
        
        # Stars background
        self.stars = []
        for _ in range(100):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)
            brightness = random.randint(150, 255)
            self.stars.append((x, y, size, (brightness, brightness, brightness)))
    
    def spawn_asteroid(self):
        self.asteroids.add(Asteroid())
    
    def check_asteroid_earth_collisions(self):
        for asteroid in self.asteroids:
            if asteroid.check_earth_collision(self.earth):
                damage = int(asteroid.radius)
                self.earth.health -= damage
                if self.collision_sound:
                    self.collision_sound.play()
                self.asteroids.remove(asteroid)
                if self.earth.health <= 0:
                    self.earth.health = 0
                    self.game_over = True
    
    def check_asteroid_deflections(self):
        for asteroid in self.asteroids:
            if asteroid.update(self.earth, self.attractor):
                # Asteroid is out of bounds
                distance_to_earth = (asteroid.pos - self.earth.pos).length()
                if distance_to_earth > 150:  # Ensure it's actually deflected away
                    self.score += int(asteroid.radius * 2)
                    self.deflected_count += 1
                    if self.deflection_sound:
                        self.deflection_sound.play()
                    
                    # Add level progression
                    if self.deflected_count >= 10:
                        self.level += 1
                        self.deflected_count = 0
                        self.spawn_delay = max(500, self.spawn_delay - 200)  # Increase difficulty
                
                self.asteroids.remove(asteroid)
    
    def draw_stars(self):
        for x, y, size, color in self.stars:
            pygame.draw.circle(self.screen, color, (x, y), size)
    
    def display_hud(self):
        # Display score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Display level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (10, 50))
        
        # Display Earth health
        self.earth.draw_health_bar(self.screen)
        health_text = self.small_font.render(f"Earth Health: {self.earth.health}/{self.earth.max_health}", True, WHITE)
        self.screen.blit(health_text, (WIDTH // 2 - 90, HEIGHT - 50))
    
    def display_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
        
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
        
        restart_text = self.font.render("Press R to Restart or ESC to Quit", True, WHITE)
        self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
    
    def display_instructions(self):
        instructions = [
            "Use WASD or Arrow Keys to move the gravity attractor",
            "Deflect asteroids away from Earth",
            "Press SPACE to start"
        ]
        
        for i, line in enumerate(instructions):
            text = self.small_font.render(line, True, WHITE)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + 30 * i))
    
    def reset(self):
        self.earth = Earth()
        self.attractor = GravityAttractor()
        self.asteroids.empty()
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.spawn_delay = 2000
        self.game_over = False
        self.deflected_count = 0
    
    def run(self):
        waiting_for_start = True
        running = True
        
        while running:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_r and self.game_over:
                        self.reset()
                        waiting_for_start = True
                        self.game_over = False
                    elif event.key == K_SPACE and waiting_for_start:
                        waiting_for_start = False
            
            # Get pressed keys for continuous movement
            keys = pygame.key.get_pressed()
            
            # Clear the screen
            self.screen.fill(BLACK)
            
            # Draw stars background
            self.draw_stars()
            
            # Update and draw game objects
            if not waiting_for_start and not self.game_over:
                # Spawn new asteroids
                if current_time - self.spawn_timer > self.spawn_delay:
                    self.spawn_asteroid()
                    self.spawn_timer = current_time
                
                self.attractor.update(keys)
                self.check_asteroid_deflections()
                self.check_asteroid_earth_collisions()
            
            # Draw gravitational field
            self.attractor.draw_gravitational_field(self.screen)
            
            # Draw Earth
            self.screen.blit(self.earth.image, self.earth.rect)
            
            # Draw attractor
            self.screen.blit(self.attractor.image, self.attractor.rect)
            
            # Draw asteroids and force lines
            for asteroid in self.asteroids:
                asteroid.draw_force_lines(self.screen)
                self.screen.blit(asteroid.image, asteroid.rect)
            
            # Display HUD
            self.display_hud()
            
            # Display game over or start screen
            if self.game_over:
                self.display_game_over()
            elif waiting_for_start:
                self.display_instructions()
            
            # Update the display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()