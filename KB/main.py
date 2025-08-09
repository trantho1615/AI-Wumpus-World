from environment import Environment
from agent import KBWumpusAgent
from agent import RandomWumpusAgent
import pygame
import os

from config import (
    WIN, TILE_MAPS, N, POSITIONS, MAP, LIGHT, FPS, WIDTH, HEIGHT,
    HUNTER_IDLE, WUMPUS_IDLE, GOLD, PIT, 
    W_BREEZE, W_STENCH, W_BS, W_GOLD
)

from utils import rotate, load_map

def get_pixel_position(grid_x, grid_y):
    """Convert grid coordinates to pixel position using POSITIONS array"""
    # Ensure coordinates are within bounds
    if 0 <= grid_x < N and 0 <= grid_y < N:
        return POSITIONS[grid_y][grid_x]  # POSITIONS[row][col]
    return (0, 0)  # Default position if out of bounds

class GameElement:
    """Base class for drawable game elements"""
    def __init__(self, grid_x, grid_y, image):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.image = image
        self.pixel_x, self.pixel_y = get_pixel_position(grid_x, grid_y)
        
    def draw(self):
        if self.image:
            rect = self.image.get_rect(center=(self.pixel_x, self.pixel_y))
            WIN.blit(self.image, rect)
    
    def update_position(self, grid_x, grid_y):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pixel_x, self.pixel_y = get_pixel_position(grid_x, grid_y)

class Hunter(GameElement, pygame.sprite.Sprite):
    """Hunter/Agent sprite with animations"""
    def __init__(self, grid_x, grid_y, direction="E"):
        # Use first frame of idle animation
        super().__init__(grid_x, grid_y, HUNTER_IDLE[0] if HUNTER_IDLE else None)
        pygame.sprite.Sprite.__init__(self)
        
        self.direction = direction
        self.sprites = {
            'idle': HUNTER_IDLE,
            'move': HUNTER_IDLE,  # Use idle for now
            'shoot': HUNTER_IDLE
        }
        self.current_sprite = 0
        self.current_state = 'idle'
        self.animation_speed = 0.1
        
        # Direction angles for rotation
        self.facing_angles = {
            'E': 0,    # East (right)
            'N': 90,   # North (up) 
            'W': 180,  # West (left)
            'S': 270   # South (down)
        }
        
        if self.image:
            self.rect = self.image.get_rect(center=(self.pixel_x, self.pixel_y))
    
    def move_to(self, grid_x, grid_y, direction="E"):
        """Move hunter to new grid position"""
        self.update_position(grid_x, grid_y)
        self.direction = direction
        
        # Update image with rotation
        if self.sprites[self.current_state]:
            base_image = self.sprites[self.current_state][int(self.current_sprite)]
            angle = self.facing_angles.get(direction, 0)
            self.image = rotate(base_image, angle)
            self.rect = self.image.get_rect(center=(self.pixel_x, self.pixel_y))
    
    def update(self):
        """Update animation"""
        if self.sprites[self.current_state]:
            self.current_sprite += self.animation_speed
            if self.current_sprite >= len(self.sprites[self.current_state]):
                self.current_sprite = 0
            
            # Update image
            base_image = self.sprites[self.current_state][int(self.current_sprite)]
            angle = self.facing_angles.get(self.direction, 0)
            self.image = rotate(base_image, angle)

class Wumpus(GameElement):
    """Wumpus sprite"""
    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y, WUMPUS_IDLE[0] if WUMPUS_IDLE else None)

class GoldElement(GameElement):
    """Gold sprite"""
    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y, GOLD)

class PitElement(GameElement):
    """Pit sprite"""
    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y, PIT)

class PerceptElement(GameElement):
    """Percept warnings (breeze, stench, etc.)"""
    def __init__(self, grid_x, grid_y, percept_type):
        percept_images = {
            'breeze': W_BREEZE,
            'stench': W_STENCH,
            'both': W_BS,
            'gold': W_GOLD
        }
        image = percept_images.get(percept_type, None)
        super().__init__(grid_x, grid_y, image)

def run_random_agent():
    env = Environment(size=4, num_wumpus=1, pit_prob=0.2)
    agent = RandomWumpusAgent(env)

    steps = 0
    while not agent.done and steps < 50:
        percepts = env.get_percepts(agent.position, bump=getattr(agent, "bump", False))
        agent.perceive(percepts)
        percepts["bump"] = getattr(agent, "bump", False)
        percepts["scream"] = env.scream

        action = agent.choose_action()
        print(f"[Step {steps}] Action: {action}")

        env.apply_action(agent, action)
        
        if action == "move":
            agent.update_position_on_move()

        env.print_state(agent)
        steps += 1


def get_tile_type(row, col, N):
    # Corners
    if row == 1 and col == 1:
        return 'map11'      # Bottom-left
    elif row == 1 and col == N:
        return 'map31'      # Bottom-right
    elif row == N and col == 1:
        return 'map13'      # Top-left
    elif row == N and col == N:
        return 'map33'      # Top-right
    # Top border (excluding corners)
    elif row == N and col > 1 and col < N:
        return 'map23'
    # Bottom border (excluding corners)
    elif row == 1 and col > 1 and col < N:
        return 'map21'
    # Left border (excluding corners)
    elif col == 1 and row > 1 and row < N:
        return 'map12'
    # Right border (excluding corners)
    elif col == N and row > 1 and row < N:
        return 'map32'
    # Inside
    else:
        return 'map22'


def draw_window(environment, agent, game_elements=None):
    """Update the window with all game elements"""
    WIN.fill((0, 0, 0))  # Clear screen with black

    # Draw tile map background
    use_tilemap = len(TILE_MAPS) > 0
    if use_tilemap:
        for row in range(1, N + 1):      # row = y + 1 (1-indexed)
            for col in range(1, N + 1):  # col = x + 1 (1-indexed)
                tile_type = get_tile_type(row, col, N)
                tile_img = load_map(tile_type, N, 800, 800)  # Pass grid size for dynamic scaling
                # Convert to 0-indexed for POSITIONS array
                x, y = POSITIONS[row - 1][col - 1]
                rect = tile_img.get_rect(center=(x, y))
                WIN.blit(tile_img, rect)
    else:
        WIN.blit(MAP, (0, 0))
    # Draw environment elements (pits, wumpus, gold)
    draw_environment_elements(environment)
    
    # Draw percepts at agent's current position
    draw_percepts(environment, agent)

    
    # Draw game elements if provided
    if game_elements:
        for element in game_elements:
            if element:
                element.draw()
    
    pygame.display.update()

def draw_environment_elements(environment):
    """Draw pits, wumpus, and gold from environment"""
    for x in range(environment.size):
        for y in range(environment.size):
            cell = environment.grid[x][y]
            pixel_x, pixel_y = get_pixel_position(x, y)
            
            # Draw pit
            if cell.pit and PIT:
                rect = PIT.get_rect(center=(pixel_x, pixel_y))
                WIN.blit(PIT, rect)
            
            # Draw wumpus
            if cell.wumpus and WUMPUS_IDLE:
                wumpus_img = WUMPUS_IDLE[0]  # Use first frame
                rect = wumpus_img.get_rect(center=(pixel_x, pixel_y))
                WIN.blit(wumpus_img, rect)
            
            # Draw gold
            if cell.gold and GOLD:
                rect = GOLD.get_rect(center=(pixel_x, pixel_y))
                WIN.blit(GOLD, rect)

def draw_percepts(environment, agent):
    """Draw percept warnings at agent's position relative to hunter direction"""
    percepts = environment.get_percepts(agent.position)
    x, y = agent.position
    pixel_x, pixel_y = get_pixel_position(x, y)
    
    # Calculate dynamic offset based on grid size to prevent overlap with hunter
    # For smaller grids (larger cells), use larger offsets
    cell_size = min(WIDTH, HEIGHT) // N
    base_offset = max(30, cell_size // 5)  # Minimum 30px, or 1/6 of cell size
    
    # Calculate direction-based offsets for right-top positioning
    direction_offsets = {
        "N": (base_offset, base_offset),      # Facing North: right-top is right and up
        "E": (-base_offset, base_offset),     # Facing East: right-top is back and up
        "S": (-base_offset, base_offset),     # Facing South: right-top is left and up
        "W": (base_offset, base_offset)       # Facing West: right-top is forward and up
    }
    
    dx, dy = direction_offsets.get(agent.direction, (base_offset, base_offset))
    
    if percepts.get("breeze") and percepts.get("stench"):
        # Both breeze and stench - use combined asset if available
        if W_BS:
            rect = W_BS.get_rect(center=(pixel_x + dx, pixel_y + dy))
            WIN.blit(W_BS, rect)
        else:
            # Position them side by side if no combined asset
            side_offset = base_offset // 2
            if W_BREEZE:
                rect = W_BREEZE.get_rect(center=(pixel_x + dx - side_offset, pixel_y + dy))
                WIN.blit(W_BREEZE, rect)
            if W_STENCH:
                rect = W_STENCH.get_rect(center=(pixel_x + dx + side_offset, pixel_y + dy))
                WIN.blit(W_STENCH, rect)
    elif percepts.get("breeze"):
        # Only breeze
        if W_BREEZE:
            rect = W_BREEZE.get_rect(center=(pixel_x + dx, pixel_y + dy))
            WIN.blit(W_BREEZE, rect)
    elif percepts.get("stench"):
        # Only stench
        if W_STENCH:
            rect = W_STENCH.get_rect(center=(pixel_x + dx, pixel_y + dy))
            WIN.blit(W_STENCH, rect)
    
    if percepts.get("glitter"):
        # Gold glitter - position slightly below the warning area
        if W_GOLD:
            rect = W_GOLD.get_rect(center=(pixel_x + dx, pixel_y + dy - base_offset // 2))
            WIN.blit(W_GOLD, rect)

def run_game_with_gui():
    """Run game with graphical interface and proper asset positioning"""
    env = Environment(size=N, num_wumpus=1, pit_prob=0.01)
    agent = KBWumpusAgent(env)
    
    # Create hunter sprite
    hunter = Hunter(agent.position[0], agent.position[1], agent.direction)
    all_sprites = pygame.sprite.Group()
    all_sprites.add(hunter)

    # Game state
    clock = pygame.time.Clock()
    running = True
    step_count = 0
    auto_step = False
    step_delay = 100  # milliseconds between auto steps
    last_step_time = 0
    
    print("Game started! Controls:")
    print("SPACE - Manual step")
    print("A - Toggle auto-play") 
    print("R - Reset game")
    print("Q - Quit")
    
    with open("game_log.txt", "w") as log_file:
        while running and not agent.done and step_count < 50:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Manual step
                        percepts = env.get_percepts(agent.position, bump=getattr(agent, "bump", False))
                        agent.perceive(percepts)
                        percepts["bump"] = getattr(agent, "bump", False)
                        percepts["scream"] = env.scream

                        # Agent chooses action
                        action = agent.choose_action()

                        # Log step
                        log_str = (
                            f"[Step {step_count + 1}] Action: {action}, "
                            f"Position: {agent.position}, "
                            f"Direction: {agent.direction}, "
                            f"Has Gold: {agent.has_gold}, "
                            f"Percepts: {percepts}"
                        )
                        print(log_str)
                        log_file.write(log_str + "\n")

                        # Apply action
                        env.apply_action(agent, action)
                        env.print_state(agent)
                        hunter.move_to(agent.position[0], agent.position[1], agent.direction)
                        step_count += 1
                    elif event.key == pygame.K_a:
                        # Toggle auto step
                        auto_step = not auto_step
                        print(f"Auto step: {'ON' if auto_step else 'OFF'}")
                    elif event.key == pygame.K_r:
                        # Reset game
                        env = Environment(size=N, num_wumpus=2, pit_prob=0.2)
                        agent = KBWumpusAgent(env)
                        hunter.move_to(agent.position[0], agent.position[1], agent.direction)
                        step_count = 0
                        auto_step = False
                        print("Game reset!")
                    elif event.key == pygame.K_q:
                        running = False
            
            # Auto step
            if auto_step and current_time - last_step_time >= step_delay:
                percepts = env.get_percepts(agent.position, bump=getattr(agent, "bump", False))
                agent.perceive(percepts)
                percepts["bump"] = getattr(agent, "bump", False)
                percepts["scream"] = env.scream

                # Agent chooses action
                action = agent.choose_action()

                # Log step
                log_str = (
                    f"[Step {step_count + 1}] Action: {action}, "
                    f"Position: {agent.position}, "
                    f"Direction: {agent.direction}, "
                    f"Has Gold: {agent.has_gold}, "
                    f"Percepts: {percepts}"
                )
                print(log_str)
                log_file.write(log_str + "\n")

                # Apply action
                env.apply_action(agent, action)
                env.print_state(agent)
                hunter.move_to(agent.position[0], agent.position[1], agent.direction)
                step_count += 1
                last_step_time = current_time
            
            # Update sprites
            all_sprites.update()
            
            # Draw everything with proper positioning
            draw_window(env, agent, all_sprites)
            clock.tick(FPS)
        
        # Game over
        if agent.done:
            if agent.has_gold and agent.position == (0, 0):
                print("VICTORY! Agent escaped with the gold!")
            else:
                print("GAME OVER! Agent died or failed.")
        elif step_count >= 50:
            print("GAME OVER! Maximum steps reached.")
        
        pygame.quit()

def step_game_once(env, agent, step_count):
    """Execute one game step"""
    # Get percepts
    percepts = env.get_percepts(agent.position, bump=getattr(agent, "bump", False))
    agent.perceive(percepts)
    percepts["bump"] = getattr(agent, "bump", False)
    percepts["scream"] = env.scream

    # Agent chooses action
    action = agent.choose_action()

    # Log step
    log_str = (
        f"[Step {step_count + 1}] Action: {action}, "
        f"Position: {agent.position}, "
        f"Direction: {agent.direction}, "
        f"Has Gold: {agent.has_gold}, "
        f"Percepts: {percepts}"
    )
    print(log_str)


    # Apply action
    env.apply_action(agent, action)
    env.print_state(agent)

    return log_str

def run_game():
    env = Environment(size=4, num_wumpus=1, pit_prob=0.2)
    agent = KBWumpusAgent(env)

    steps = 0

    # Open the file for writing logs
    with open("game_log.txt", "w") as log_file:
        while not agent.done and steps < 50:
            percepts = env.get_percepts(agent.position, bump=getattr(agent, "bump", False))
            agent.perceive(percepts)

            percepts["bump"] = getattr(agent, "bump", False)
            percepts["scream"] = env.scream

            action = agent.choose_action()

            # Create the log string
            log_str = (
                f"[Step {steps}] Action: {action}, "
                f"Position: {agent.position}, "
                f"Direction: {agent.direction}, "
                f"Has Gold: {agent.has_gold}, "
                f"Scream: {percepts.get('scream', False)}, "
                f"Bump: {percepts.get('bump', False)}"
            )

            print(log_str)
            log_file.write(log_str + "\n")

            env.apply_action(agent, action)
            env.print_state(agent)
            steps += 1


if __name__ == "__main__":
    # Choose which version to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        # Run console version
        run_game()
    else:
        # Run GUI version with proper asset positioning
        run_game_with_gui()