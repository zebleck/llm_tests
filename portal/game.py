import pygame
from player import Player
from level import Level
from camera import Camera

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Initialize game components
        self.current_level = 0
        self.camera = Camera(self.width, self.height)
        self.level = Level(self.current_level)
        self.player = Player(self.level.player_start_pos)
        
        # Connect player to level and set camera
        self.level.player = self.player
        self.level.camera = self.camera
        
        # Game state
        self.game_state = "playing"  # "playing", "menu", "game_over", "level_complete"
    
    def handle_event(self, event):
        # Handle input events
        if event.type == pygame.KEYDOWN:
            if self.game_state == "menu":
                # Exit menu with any key press
                self.game_state = "playing"
            elif event.key == pygame.K_ESCAPE:
                self.game_state = "menu"
        
        # Only pass events to the player when playing
        if self.game_state == "playing":
            self.player.handle_event(event, self.level)
    
    def update(self, dt):
        if self.game_state == "playing":
            # Update player and game objects
            self.player.update(dt, self.level)
            self.level.update(dt)
            
            # Update camera to follow player
            self.camera.update(self.player)
            
            # Check for level completion
            if self.level.is_complete():
                self.current_level += 1
                if self.current_level >= 3:  # We have 3 levels total
                    self.game_state = "game_over"
                else:
                    self.level = Level(self.current_level)
                    self.player.reset(self.level.player_start_pos)
                    self.level.player = self.player
                    self.level.camera = self.camera
    
    def render(self):
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Render level, player, and objects through the camera
        self.level.render(self.screen, self.camera)
        self.player.render(self.screen, self.camera)
        
        # Render UI elements
        if self.game_state == "menu":
            self.render_menu()
        elif self.game_state == "game_over":
            self.render_game_over()
    
    def render_menu(self):
        # Render a simple menu
        font = pygame.font.SysFont(None, 64)
        text = font.render("PORTAL SHIFT", True, (255, 255, 255))
        self.screen.blit(text, (self.width/2 - text.get_width()/2, self.height/2 - 50))
        
        font = pygame.font.SysFont(None, 32)
        text = font.render("Press any key to continue", True, (200, 200, 200))
        self.screen.blit(text, (self.width/2 - text.get_width()/2, self.height/2 + 30))
    
    def render_game_over(self):
        # Render game over screen
        font = pygame.font.SysFont(None, 64)
        text = font.render("You completed all levels!", True, (255, 255, 255))
        self.screen.blit(text, (self.width/2 - text.get_width()/2, self.height/2 - 50))