import pygame
import random
import noise
import numpy as np
from enum import Enum

# Define tile types
class TileType(Enum):
    DEEP_WATER = 0
    SHALLOW_WATER = 1
    SAND = 2
    GRASS = 3
    FOREST = 4
    MOUNTAIN = 5
    CAVE_ENTRANCE = 6
    HOUSE = 7
    CAVE = 8

# Define colors for each tile type
TILE_COLORS = {
    TileType.DEEP_WATER: (0, 0, 139),      # Dark blue
    TileType.SHALLOW_WATER: (65, 105, 225), # Royal blue
    TileType.SAND: (238, 214, 175),        # Sand
    TileType.GRASS: (34, 139, 34),         # Forest green
    TileType.FOREST: (0, 100, 0),          # Dark green
    TileType.MOUNTAIN: (139, 137, 137),    # Gray
    TileType.CAVE_ENTRANCE: (101, 67, 33), # Brown
    TileType.HOUSE: (178, 34, 34),         # Firebrick red
    TileType.CAVE: (50, 50, 50),           # Dark gray
}

class LushPlanetGenerator:
    def __init__(self, width, height, tile_size=10):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.map_width = width // tile_size
        self.map_height = height // tile_size
        self.tilemap = np.zeros((self.map_width, self.map_height), dtype=int)
        
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Lush Planet Generator")
        self.clock = pygame.time.Clock()
        
        # Generation parameters
        self.seed = random.randint(0, 1000)
        self.scale = 100.0
        self.octaves = 6
        self.persistence = 0.5
        self.lacunarity = 2.0
        
        # Settlement parameters
        self.min_settlements = 3
        self.max_settlements = 7
        self.min_houses_per_settlement = 3
        self.max_houses_per_settlement = 12
        
        # Cave parameters
        self.cave_chance = 0.2
        self.cave_entrances = []
        
    def generate_heightmap(self):
        """Generate a heightmap using Perlin noise"""
        heightmap = np.zeros((self.map_width, self.map_height))
        
        for i in range(self.map_width):
            for j in range(self.map_height):
                nx = i / self.map_width - 0.5
                ny = j / self.map_height - 0.5
                
                # Generate elevation using Perlin noise
                elevation = noise.pnoise2(
                    nx * self.scale + self.seed, 
                    ny * self.scale + self.seed, 
                    octaves=self.octaves, 
                    persistence=self.persistence, 
                    lacunarity=self.lacunarity, 
                    repeatx=1024, 
                    repeaty=1024, 
                    base=self.seed
                )
                
                # Normalize elevation to [0, 1]
                heightmap[i][j] = (elevation + 1) / 2
                
        return heightmap
    
    def generate_moisture_map(self):
        """Generate a moisture map using a different seed"""
        moisture_map = np.zeros((self.map_width, self.map_height))
        moisture_seed = self.seed + 1000
        
        for i in range(self.map_width):
            for j in range(self.map_height):
                nx = i / self.map_width - 0.5
                ny = j / self.map_height - 0.5
                
                # Generate moisture using Perlin noise with a different seed
                moisture = noise.pnoise2(
                    nx * self.scale + moisture_seed, 
                    ny * self.scale + moisture_seed, 
                    octaves=self.octaves, 
                    persistence=self.persistence, 
                    lacunarity=self.lacunarity, 
                    repeatx=1024, 
                    repeaty=1024, 
                    base=moisture_seed
                )
                
                # Normalize moisture to [0, 1]
                moisture_map[i][j] = (moisture + 1) / 2
                
        return moisture_map
    
    def generate_base_terrain(self):
        """Generate the base terrain using heightmap and moisture"""
        heightmap = self.generate_heightmap()
        moisture_map = self.generate_moisture_map()
        
        for i in range(self.map_width):
            for j in range(self.map_height):
                height = heightmap[i][j]
                moisture = moisture_map[i][j]
                
                # Determine tile type based on height and moisture
                if height < 0.3:
                    if height < 0.2:
                        self.tilemap[i][j] = TileType.DEEP_WATER.value
                    else:
                        self.tilemap[i][j] = TileType.SHALLOW_WATER.value
                elif height < 0.35:
                    self.tilemap[i][j] = TileType.SAND.value
                elif height < 0.75:
                    if moisture > 0.6:
                        self.tilemap[i][j] = TileType.FOREST.value
                    else:
                        self.tilemap[i][j] = TileType.GRASS.value
                else:
                    self.tilemap[i][j] = TileType.MOUNTAIN.value
    
    def add_caves(self):
        """Add cave entrances and cave systems"""
        # Find suitable locations for cave entrances (mountains)
        potential_entrances = []
        for i in range(1, self.map_width - 1):
            for j in range(1, self.map_height - 1):
                if self.tilemap[i][j] == TileType.MOUNTAIN.value:
                    # Check if surrounded by at least some mountain tiles
                    mountain_neighbors = 0
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            if di == 0 and dj == 0:
                                continue
                            if self.tilemap[i+di][j+dj] == TileType.MOUNTAIN.value:
                                mountain_neighbors += 1
                    
                    if mountain_neighbors >= 3:
                        potential_entrances.append((i, j))
        
        # Randomly select cave entrances
        num_caves = min(len(potential_entrances), int(self.map_width * self.map_height * self.cave_chance / 100))
        if potential_entrances and num_caves > 0:
            cave_entrances = random.sample(potential_entrances, num_caves)
            
            for x, y in cave_entrances:
                self.tilemap[x][y] = TileType.CAVE_ENTRANCE.value
                self.cave_entrances.append((x, y))
                
                # Generate cave system from each entrance
                self.generate_cave_system(x, y)
    
    def generate_cave_system(self, start_x, start_y):
        """Generate a cave system starting from an entrance"""
        # Parameters for the cave system
        max_length = random.randint(10, 30)
        current_length = 0
        
        # Start at the entrance
        current_x, current_y = start_x, start_y
        
        # Direction vectors for possible movements
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # Generate the cave path
        while current_length < max_length:
            # Choose a random direction
            dx, dy = random.choice(directions)
            new_x, new_y = current_x + dx, current_y + dy
            
            # Check if the new position is valid
            if (0 <= new_x < self.map_width and 
                0 <= new_y < self.map_height and 
                self.tilemap[new_x][new_y] == TileType.MOUNTAIN.value):
                
                # Create a cave tile
                self.tilemap[new_x][new_y] = TileType.CAVE.value
                
                # Update current position
                current_x, current_y = new_x, new_y
                current_length += 1
                
                # Occasionally branch the cave
                if random.random() < 0.2:
                    branch_length = random.randint(3, 8)
                    self.branch_cave(current_x, current_y, branch_length)
            else:
                # If we can't move in this direction, try another
                continue
                
            # Small chance to stop early
            if random.random() < 0.05:
                break
    
    def branch_cave(self, start_x, start_y, max_length):
        """Create a branch in the cave system"""
        current_length = 0
        current_x, current_y = start_x, start_y
        
        # Direction vectors for possible movements
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # Generate the branch
        while current_length < max_length:
            # Choose a random direction
            dx, dy = random.choice(directions)
            new_x, new_y = current_x + dx, current_y + dy
            
            # Check if the new position is valid
            if (0 <= new_x < self.map_width and 
                0 <= new_y < self.map_height and 
                self.tilemap[new_x][new_y] == TileType.MOUNTAIN.value):
                
                # Create a cave tile
                self.tilemap[new_x][new_y] = TileType.CAVE.value
                
                # Update current position
                current_x, current_y = new_x, new_y
                current_length += 1
            else:
                # If we can't move in this direction, stop branching
                break
    
    def add_settlements(self):
        """Add settlements with houses"""
        # Find suitable locations for settlements (flat grass areas)
        potential_settlements = []
        
        for i in range(2, self.map_width - 2):
            for j in range(2, self.map_height - 2):
                if self.tilemap[i][j] == TileType.GRASS.value:
                    # Check if there's enough flat grass area around
                    flat_area = True
                    for di in range(-2, 3):
                        for dj in range(-2, 3):
                            if not (0 <= i+di < self.map_width and 0 <= j+dj < self.map_height):
                                flat_area = False
                                break
                            
                            if self.tilemap[i+di][j+dj] not in [TileType.GRASS.value, TileType.FOREST.value]:
                                flat_area = False
                                break
                    
                    if flat_area:
                        # Check if near water (settlements often near water)
                        near_water = False
                        for di in range(-4, 5):
                            for dj in range(-4, 5):
                                if not (0 <= i+di < self.map_width and 0 <= j+dj < self.map_height):
                                    continue
                                
                                if self.tilemap[i+di][j+dj] in [TileType.SHALLOW_WATER.value, TileType.DEEP_WATER.value]:
                                    near_water = True
                                    break
                        
                        if near_water:
                            potential_settlements.append((i, j))
        
        # Randomly select settlement locations
        num_settlements = random.randint(self.min_settlements, self.max_settlements)
        if potential_settlements and num_settlements > 0:
            num_settlements = min(num_settlements, len(potential_settlements))
            settlements = random.sample(potential_settlements, num_settlements)
            
            for center_x, center_y in settlements:
                # Generate a small settlement around the center
                num_houses = random.randint(self.min_houses_per_settlement, self.max_houses_per_settlement)
                self.generate_settlement(center_x, center_y, num_houses)
    
    def generate_settlement(self, center_x, center_y, num_houses):
        """Generate a settlement with houses around a center point"""
        # Place the first house at the center
        self.tilemap[center_x][center_y] = TileType.HOUSE.value
        
        # Place remaining houses
        houses_placed = 1
        max_distance = 3
        
        while houses_placed < num_houses:
            # Try to place a house within max_distance of the center
            for _ in range(20):  # Try 20 times before giving up
                dx = random.randint(-max_distance, max_distance)
                dy = random.randint(-max_distance, max_distance)
                
                x, y = center_x + dx, center_y + dy
                
                # Check if the position is valid
                if (0 <= x < self.map_width and 
                    0 <= y < self.map_height and 
                    self.tilemap[x][y] == TileType.GRASS.value):
                    
                    # Check if there's already a house nearby
                    house_nearby = False
                    for di in range(-1, 2):
                        for dj in range(-1, 2):
                            if not (0 <= x+di < self.map_width and 0 <= y+dj < self.map_height):
                                continue
                            
                            if self.tilemap[x+di][y+dj] == TileType.HOUSE.value:
                                house_nearby = True
                                break
                    
                    if not house_nearby:
                        # Place a house
                        self.tilemap[x][y] = TileType.HOUSE.value
                        houses_placed += 1
                        break
            
            # If we couldn't place a house after 20 tries, just stop
            if houses_placed < num_houses:
                houses_placed += 1
    
    def generate_world(self):
        """Generate the complete world"""
        self.generate_base_terrain()
        self.add_caves()
        self.add_settlements()
        
    def draw_map(self):
        """Draw the tilemap on the screen"""
        for i in range(self.map_width):
            for j in range(self.map_height):
                tile_type = TileType(self.tilemap[i][j])
                color = TILE_COLORS[tile_type]
                
                rect = pygame.Rect(
                    i * self.tile_size, 
                    j * self.tile_size, 
                    self.tile_size, 
                    self.tile_size
                )
                pygame.draw.rect(self.screen, color, rect)
    
    def run(self):
        """Run the generator and display the result"""
        self.generate_world()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Regenerate the world with a new seed
                        self.seed = random.randint(0, 1000)
                        self.generate_world()
                    elif event.key == pygame.K_s:
                        # Save the map as an image
                        pygame.image.save(self.screen, "lush_planet_map.png")
                        print("Map saved as lush_planet_map.png")
            
            self.screen.fill((0, 0, 0))
            self.draw_map()
            
            # Display instructions
            font = pygame.font.SysFont(None, 24)
            text1 = font.render("Press SPACE to regenerate", True, (255, 255, 255))
            text2 = font.render("Press S to save the map", True, (255, 255, 255))
            self.screen.blit(text1, (10, 10))
            self.screen.blit(text2, (10, 40))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    # Create and run the generator
    generator = LushPlanetGenerator(800, 600, tile_size=8)
    generator.run()