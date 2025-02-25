import pygame
import sys
from game import Game

def main():
    pygame.init()
    
    # Set up the display
    screen_width = 1280
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Portal Shift")
    
    # Create the game instance
    game = Game(screen)
    
    # Main game loop
    clock = pygame.time.Clock()
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            game.handle_event(event)
        
        # Update game state
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        game.update(dt)
        
        # Render the game
        game.render()
        pygame.display.flip()

if __name__ == "__main__":
    main()