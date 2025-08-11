from environment import Environment
from agent import KBWumpusAgent
from agent import RandomWumpusAgent
import pygame
import os
import sys
import time
import math
import random

from config import (
    WIN, TILE_MAPS, N, POSITIONS, LIGHT, FPS, WIDTH, HEIGHT,
    HUNTER_IDLE, WUMPUS_IDLE, GOLD, PIT, 
    W_BREEZE, W_STENCH, W_BS, W_GOLD, EXIT, ADVANCE_SETTING,
    GAME_N, GAME_NUM_WUMPUS, GAME_PIT_PROB, GAME_CONSOLE_MODE, GAME_AGENT_TYPE
)

from utils import rotate, load_map

# Global variables for visual announcements
announcement_text = ""
announcement_timer = 0
announcement_type = "info"  # "info", "success", "warning"

# Global variables for game configuration (set via command line arguments)


def display_visual_announcement(text, duration=3000, ann_type="info"):
    """Display announcement on game screen"""
    global announcement_text, announcement_timer, announcement_type
    announcement_text = text
    announcement_timer = pygame.time.get_ticks() + duration
    announcement_type = ann_type

def clear_visual_announcement():
    """Clear any active visual announcement"""
    global announcement_text, announcement_timer, announcement_type
    announcement_text = ""
    announcement_timer = 0
    announcement_type = "info"

def draw_visual_announcement():
    """Draw current announcement on screen if active"""
    global announcement_text, announcement_timer, announcement_type
    
    current_time = pygame.time.get_ticks()
    if current_time < announcement_timer and announcement_text:
        # Initialize font if not already done
        pygame.font.init()
        
        # Colors based on announcement type
        colors = {
            "info": ((100, 149, 237), (255, 255, 255)),      # Blue background, white text
            "success": ((0, 128, 0), (255, 255, 255)),       # Green background, white text  
            "warning": ((255, 140, 0), (0, 0, 0)),           # Orange background, black text
            "error": ((220, 20, 60), (255, 255, 255))        # Red background, white text
        }
        
        bg_color, text_color = colors.get(announcement_type, colors["info"])
        
        # Font setup
        font = pygame.font.Font(None, 36)
        
        # Create text surface
        text_surface = font.render(announcement_text, True, text_color)
        text_rect = text_surface.get_rect()
        
        # Position at top center of screen
        text_rect.centerx = WIDTH // 2
        text_rect.y = 20
        
        # Create background rectangle with padding
        padding = 20
        bg_rect = pygame.Rect(
            text_rect.x - padding,
            text_rect.y - padding // 2,
            text_rect.width + padding * 2,
            text_rect.height + padding
        )
        
        # Fade effect based on remaining time
        time_remaining = announcement_timer - current_time
        fade_duration = 500  # Last 500ms for fade
        
        if time_remaining < fade_duration:
            alpha = int(255 * (time_remaining / fade_duration))
        else:
            alpha = 255
        
        # Draw semi-transparent background
        overlay = pygame.Surface((bg_rect.width, bg_rect.height))
        overlay.set_alpha(min(200, alpha))
        overlay.fill(bg_color)
        WIN.blit(overlay, bg_rect)
        
        # Draw border
        pygame.draw.rect(WIN, (255, 255, 255), bg_rect, 2)
        
        # Draw text
        text_surface.set_alpha(alpha)
        WIN.blit(text_surface, text_rect)

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
    env = Environment(size=GAME_N, num_wumpus=GAME_NUM_WUMPUS, pit_prob=GAME_PIT_PROB)
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
    if row == 0 and col == 0:
        return 'map11'      # Bottom-left
    elif row == 0 and col == N-1:
        return 'map31'      # Bottom-right
    elif row == N-1 and col == 0:
        return 'map13'      # Top-left
    elif row == N-1 and col == N-1:
        return 'map33'      # Top-right
    # Top border (excluding corners)
    elif row == N-1 and col > 0 and col < N-1:
        return 'map23'
    # Bottom border (excluding corners)
    elif row == 0 and col > 0 and col < N-1:
        return 'map21'
    # Left border (excluding corners)
    elif col == 0 and row > 0 and row < N-1:
        return 'map12'
    # Right border (excluding corners)
    elif col == N-1 and row > 0 and row < N-1:
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
        for row in range(0, N):      # row = y + 1 (1-indexed)
            for col in range(0, N):  # col = x + 1 (1-indexed)
                has_gold = agent.has_gold
                #Draw gate at (0,0)
                if has_gold:
                    tile_type = 'exit'
                    tile_img = load_map(tile_type, N, 800, 800)
                    x, y = POSITIONS[0][0]
                    rect = tile_img.get_rect(center=(x, y))
                    WIN.blit(tile_img, rect)
                
                #Draw map at each cell
                tile_type = get_tile_type(row, col, N)
                tile_img = load_map(tile_type, N, 800, 800)  # Pass grid size for dynamic scaling
                # Convert to 0-indexed for POSITIONS array
                x, y = POSITIONS[row][col]
                rect = tile_img.get_rect(center=(x, y))
                WIN.blit(tile_img, rect)
    # Draw environment elements (pits, wumpus, gold)
    draw_environment_elements(environment)
    
    # Draw percepts at agent's current position
    draw_percepts(environment, agent)

    
    # Draw game elements if provided
    if game_elements:
        for element in game_elements:
            if element:
                element.draw()
    
    # Draw visual announcements on top of everything
    draw_visual_announcement()
    
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

def display_game_over_screen(env, agent, step_count, advance_enabled, game_result="unknown"):
    """Display comprehensive game over screen with statistics and effects. Returns 'restart', 'quit', or 'continue'"""
    # Initialize font
    pygame.font.init()
    
    # Font sizes
    title_font = pygame.font.Font(None, 72)
    subtitle_font = pygame.font.Font(None, 48)
    stats_font = pygame.font.Font(None, 36)
    detail_font = pygame.font.Font(None, 28)
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    GOLD = (255, 215, 0)
    BLUE = (100, 149, 237)
    GRAY = (128, 128, 128)
    
    # Determine result colors and messages
    if game_result == "victory":
        title_color = GOLD
        subtitle_color = GREEN
        bg_color = (0, 50, 0)  # Dark green background
        title_text = "🏆 VICTORY! 🏆"
        subtitle_text = "Successfully Escaped with Gold!"
        effect_particles = True
    elif game_result == "death":
        title_color = RED
        subtitle_color = WHITE
        bg_color = (50, 0, 0)  # Dark red background
        title_text = "💀 GAME OVER 💀"
        
        # Determine specific death cause
        if hasattr(env, 'death_cause') and env.death_cause:
            if env.death_cause == "wumpus":
                subtitle_text = "Killed by the Wumpus! 🐉"
            elif env.death_cause == "pit":
                subtitle_text = "Fell into a Pit! 🕳️"
            else:
                subtitle_text = "Did Not Survive"
        else:
            subtitle_text = "Did Not Survive"

        effect_particles = False
    elif game_result == "timeout":
        title_color = (255, 165, 0)  # Orange
        subtitle_color = WHITE
        bg_color = (50, 25, 0)  # Dark orange background
        title_text = "⏰ TIME'S UP ⏰"
        subtitle_text = "Maximum Steps Reached"
        effect_particles = False
    else:
        title_color = GRAY
        subtitle_color = WHITE
        bg_color = (25, 25, 25)  # Dark gray
        title_text = "GAME ENDED"
        subtitle_text = "Session Complete"
        effect_particles = False
    
    # Calculate statistics
    final_score = env.score
    total_actions = step_count
    cells_explored = len(agent.visited) if hasattr(agent, 'visited') else 0
    total_cells = env.size * env.size
    exploration_percentage = (cells_explored / total_cells) * 100
    
    # Performance rating
    if game_result == "victory":
        if final_score > 900:
            performance = "EXCELLENT"
            perf_color = GOLD
        elif final_score > 700:
            performance = "GOOD"
            perf_color = GREEN
        elif final_score > 500:
            performance = "FAIR"
            perf_color = BLUE
        else:
            performance = "POOR"
            perf_color = RED
    else:
        performance = "FAILED"
        perf_color = RED
    
    # Animation variables
    animation_time = 0
    fade_alpha = 0
    
    # Main game over loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return 'quit'
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    running = False
                    return 'continue'
                elif event.key == pygame.K_r:
                    running = False
                    return 'restart'
                elif event.key == pygame.K_q:
                    running = False
                    return 'quit'
        
        # Update animation
        animation_time += clock.get_time() / 1000.0
        if fade_alpha < 255:
            fade_alpha = min(255, fade_alpha + 5)
        
        # Clear screen with animated background
        bg_intensity = int(25 + 15 * abs(math.sin(animation_time * 2)))
        animated_bg = (min(255, bg_color[0] + bg_intensity), 
                      min(255, bg_color[1] + bg_intensity), 
                      min(255, bg_color[2] + bg_intensity))
        WIN.fill(animated_bg)
        
        # Draw particle effects for victory
        if effect_particles and game_result == "victory":
            for i in range(50):
                x = (animation_time * 100 + i * 20) % WIDTH
                y = (animation_time * 50 + i * 15) % HEIGHT
                star_size = 3 + int(2 * abs(math.sin(animation_time * 3 + i)))
                pygame.draw.circle(WIN, GOLD, (int(x), int(y)), star_size)
        
        # Create title surface with fade effect
        title_surface = title_font.render(title_text, True, title_color)
        title_surface.set_alpha(fade_alpha)
        title_rect = title_surface.get_rect(center=(WIDTH//2, HEIGHT//4))
        WIN.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_surface = subtitle_font.render(subtitle_text, True, subtitle_color)
        subtitle_surface.set_alpha(max(0, fade_alpha - 50))
        subtitle_rect = subtitle_surface.get_rect(center=(WIDTH//2, HEIGHT//4 + 80))
        WIN.blit(subtitle_surface, subtitle_rect)
        
        # Statistics panel
        stats_y_start = HEIGHT//2 - 50
        stats_spacing = 40
        
        # Performance rating
        perf_text = f"Performance: {performance}"
        perf_surface = stats_font.render(perf_text, True, perf_color)
        perf_surface.set_alpha(max(0, fade_alpha - 100))
        perf_rect = perf_surface.get_rect(center=(WIDTH//2, stats_y_start))
        WIN.blit(perf_surface, perf_rect)
        
        # Statistics
        stats = [
            f"Final Score: {final_score:,}",
            f"Advance Setting: {'ON' if advance_enabled else 'OFF'}",
            f"Grid Size: {env.size}x{env.size}",
            f"Total Actions: {total_actions}",
            f"Cells Explored: {cells_explored}/{total_cells} ({exploration_percentage:.1f}%)",
        ]
        
        for i, stat in enumerate(stats):
            stat_surface = detail_font.render(stat, True, WHITE)
            stat_surface.set_alpha(max(0, fade_alpha - 50 - i * 25))
            stat_rect = stat_surface.get_rect(center=(WIDTH//2, stats_y_start + stats_spacing * (i + 2)))
            WIN.blit(stat_surface, stat_rect)
        
        # Instructions
        instruction_y = HEIGHT - 120
        instructions = [
            "Press R to restart game",
            "Press SPACE or ENTER to continue",
            "Press Q to quit"
        ]
        
        for i, instruction in enumerate(instructions):
            # Blinking effect for instructions
            alpha = max(0, 200 + 55 * math.sin(animation_time * 4))
            inst_surface = detail_font.render(instruction, True, GRAY)
            inst_surface.set_alpha(int(alpha))
            inst_rect = inst_surface.get_rect(center=(WIDTH//2, instruction_y + i * 30))
            WIN.blit(inst_surface, inst_rect)
        
        pygame.display.flip()
        clock.tick(60)  # Higher FPS for smooth animation
    
    # Print detailed console summary
    print("\n" + "="*60)
    print(f"  {title_text}")
    print("="*60)
    print(f"Grid Size: {env.size}x{env.size}")
    print(f"Moving Wumpus Module: {'ENABLED' if advance_enabled else 'DISABLED'}")
    print(f"Performance Rating: {performance}")
    print(f"Final Score: {final_score:,}")
    print(f"Total Actions Taken: {total_actions}")
    print(f"Cells Explored: {cells_explored}/{total_cells} ({exploration_percentage:.1f}%)")
    
    if hasattr(agent, 'has_gold') and agent.has_gold:
        print(f"Gold Status: COLLECTED ✓")
    else:
        print(f"Gold Status: NOT COLLECTED ✗")
    
    if game_result == "victory":
        print("Outcome: SUCCESSFUL ESCAPE WITH GOLD! 🏆")
        efficiency = (1000 + final_score) / (total_actions * 10)
        print(f"Efficiency Score: {efficiency:.2f}")
    elif game_result == "death":
        print("Outcome: AGENT ELIMINATED 💀")
        if hasattr(env, 'death_cause') and env.death_cause:
            if env.death_cause == "wumpus":
                print("Cause: Killed by the Wumpus 🐉")
            elif env.death_cause == "pit":
                print("Cause: Fell into a pit 🕳️")
            else:
                print(f"Cause: {env.death_cause}")
        elif hasattr(env, 'last_death_cause'):
            print(f"Cause: {env.last_death_cause}")
        else:
            print("Cause: Unknown hazard")
    else:
        print("Outcome: MISSION INCOMPLETE")
    
    print("="*60)
    print()
    return 'continue'

def run_game_with_gui():
    """Run game with graphical interface and proper asset positioning"""
    
    # Show visual welcome screen first
    print("Loading Wumpus World...")
    pygame.display.set_caption("Wumpus World - Loading...")
    
    # Display visual welcome screen
    continue_game = display_welcome_screen()
    if not continue_game:
        pygame.quit()
        return
    
    while True:
        # Initialize with advance setting from config
        advance_enabled = ADVANCE_SETTING
        env = Environment(size=GAME_N, num_wumpus=GAME_NUM_WUMPUS, pit_prob=GAME_PIT_PROB, advance_setting=advance_enabled)
        
        # Create agent based on global setting
        if GAME_AGENT_TYPE == "random":
            agent = RandomWumpusAgent(env)
        else:
            agent = KBWumpusAgent(env)
        
        # Clear event queue before starting each game instance
        pygame.event.clear()
        
        result = run_single_game(env, agent, advance_enabled)
        
        if result == 'restart':
            pygame.quit()
            pygame.init()
            global WIN, clock
            WIN = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("Wumpus World")
            clock = pygame.time.Clock()
            # Clear any accumulated events after reinitialization
            pygame.event.clear()
            continue  # Restart the game loop
        else:
            break  # Exit for 'quit' or 'end'

def run_single_game(env, agent, advance_enabled):
    """Run a single game instance"""
    # agent = RandomWumpusAgent(env)  # Use random agent for GUI demo
    
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
    
    print("\n" + "="*60)
    print("🎮 WUMPUS WORLD - GAME STARTED!")
    print("="*60)
    print("🎮 CONTROLS:")
    print("  SPACE - Execute manual step")
    print("  A     - Toggle auto-play mode")
    print("  M     - Toggle Moving Wumpus (Advance Setting)")
    print("  R     - Reset/Restart game")
    print("  H     - Show in-game help")
    print("  Q     - Quit game")
    print("\n🎯 CURRENT SETTINGS:")
    print(f"  Moving Wumpus Module: {'🟢 ACTIVATED' if advance_enabled else '🔴 DEACTIVATED'}")
    if advance_enabled:
        print("  ⚠️  Wumpuses will move every 5 actions!")
    print(f"  Auto-play: 🔴 DEACTIVATED (Press A to toggle)")
    print("="*60)
    
    # Clear any accumulated events before starting the main game loop
    pygame.event.clear()
    
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

                        # Check if Wumpus will move after this action
                        will_move_wumpus = advance_enabled and (env.action_count + 1) % 5 == 0

                        # Apply action
                        env.apply_action(agent, action)
                        
                        # Update agent knowledge if Wumpus moved
                        if will_move_wumpus and hasattr(agent, 'update_wumpus_knowledge'):
                            agent.update_wumpus_knowledge()
                            
                        env.print_state(agent)
                        hunter.move_to(agent.position[0], agent.position[1], agent.direction)
                        step_count += 1
                    elif event.key == pygame.K_a:
                        # Toggle auto step
                        auto_step = not auto_step
                        
                        # Visual announcement on game screen
                        if auto_step:
                            display_visual_announcement("🤖 AUTO-PLAY ACTIVATED - AI Taking Control!", 1000, "success")
                        else:
                            display_visual_announcement("🎮 MANUAL MODE - You Have Control!", 1000, "info")
                        
                        # Console announcement
                        print("\n" + "="*50)
                        print(f"🤖 AUTO-PLAY MODE: {'🟢 ACTIVATED' if auto_step else '🔴 DEACTIVATED'}")
                        print("="*50)
                        if auto_step:
                            print("✨ Agent will now execute moves automatically!")
                            print("📝 Watch the AI make intelligent decisions!")
                            print("⏸️  Press A again to return to manual mode")
                        else:
                            print("🎮 Manual control restored!")
                            print("👆 Use SPACE to execute each step carefully")
                            print("🔄 Press A again to re-enable auto-play")
                        print("="*50)
                    elif event.key == pygame.K_m:
                        # Toggle Moving Wumpus (Advance Setting)
                        advance_enabled = not advance_enabled
                        env.advance_setting = advance_enabled
                        
                        # Visual announcement on game screen
                        if advance_enabled:
                            display_visual_announcement("🐉 MOVING WUMPUS ACTIVATED - DANGER INCREASED!", 1000, "warning")
                        else:
                            display_visual_announcement("🛡️ CLASSIC MODE - WUMPUSES NOW STATIONARY", 1000, "success")
                        
                        # Console announcement
                        print("\n" + "="*60)
                        print(f"🐉 MOVING WUMPUS MODULE: {'🟢 ACTIVATED' if advance_enabled else '🔴 DEACTIVATED'}")
                        print("="*60)
                        if advance_enabled:
                            print("⚠️  DANGER LEVEL INCREASED!")
                            print("🎯 Wumpuses will now move every 5 actions!")
                            print("💀 Be extra careful - they can hunt you down!")
                            print("🧠 Agent knowledge will adapt to moving threats")
                            print("🔥 Challenge mode engaged!")
                        else:
                            print("🛡️  Classic mode restored!")
                            print("🎮 Wumpuses are now stationary (Original gameplay)")
                            print("📚 Perfect for learning the basics")
                            print("🎯 Focus on knowledge base reasoning")
                        print("="*60)
                    elif event.key == pygame.K_r:
                        # Reset game
                        env = Environment(size=GAME_N, num_wumpus=GAME_NUM_WUMPUS, pit_prob=GAME_PIT_PROB, advance_setting=advance_enabled)
                        
                        # Create new agent based on global setting
                        if GAME_AGENT_TYPE == "random":
                            agent = RandomWumpusAgent(env)
                        else:
                            agent = KBWumpusAgent(env)
                            
                        hunter.move_to(agent.position[0], agent.position[1], agent.direction)
                        step_count = 0
                        auto_step = False
                        
                        # Clear any existing visual announcements
                        clear_visual_announcement()
                        
                        # Console announcement
                        print("\n" + "="*50)
                        print("🔄 GAME RESET - NEW ADVENTURE BEGINS!")
                        print("="*50)
                        print("🌍 Fresh environment generated!")
                        print("🤖 Agent repositioned at start")
                        print(f"🎯 Settings: Moving Wumpus {'🟢 ON' if advance_enabled else '🔴 OFF'}")
                        print("📊 Step counter reset to 0")
                        print("🎮 Auto-play disabled (Use A to toggle)")
                        print("="*50)
                    elif event.key == pygame.K_h:
                        # Display visual instructions overlay
                        continue_game = display_visual_instructions()
                        if not continue_game:
                            running = False
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
                # Check if Wumpus will move after this action
                will_move_wumpus = advance_enabled and (env.action_count + 1) % 5 == 0
                log_file.write(log_str + "\n")

                # Apply action
                env.apply_action(agent, action)
                
                # Update agent knowledge if Wumpus moved
                if will_move_wumpus and hasattr(agent, 'update_wumpus_knowledge'):
                    agent.update_wumpus_knowledge()
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
                game_result = "victory"
                choice = display_game_over_screen(env, agent, step_count, advance_enabled, game_result)
            else:
                game_result = "death"
                choice = display_game_over_screen(env, agent, step_count, advance_enabled, game_result)
        elif step_count >= 50:
            game_result = "timeout"
            choice = display_game_over_screen(env, agent, step_count, advance_enabled, game_result)
        else:
            choice = None
        
        # Handle post-game choices
        if choice == 'restart':
            print("Restarting game...")
            return 'restart'  # Return restart signal to caller
        elif choice == 'quit':
            print("Exiting game...")
            return 'quit'  # Return quit signal to caller
        # If choice is 'continue' or None, the game loop continues normally
        
        pygame.quit()
        return 'end'

def step_game_once(env, agent, step_count, advance_enabled=False):
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

    # Check if Wumpus will move after this action
    will_move_wumpus = advance_enabled and (env.action_count + 1) % 5 == 0

    # Apply action
    env.apply_action(agent, action)
    
    # Update agent knowledge if Wumpus moved
    if will_move_wumpus and hasattr(agent, 'update_wumpus_knowledge'):
        agent.update_wumpus_knowledge()
    
    env.print_state(agent)

    return log_str

def run_game():
    env = Environment(size=GAME_N, num_wumpus=GAME_NUM_WUMPUS, pit_prob=GAME_PIT_PROB, advance_setting=ADVANCE_SETTING)
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

def display_game_instructions():
    """Display comprehensive game instructions and controls"""
    print("\n" + "="*80)
    print("🎮 WUMPUS WORLD - GAME INSTRUCTIONS & CONTROLS")
    print("="*80)
    
    print("\n🎯 OBJECTIVE:")
    print("  • Navigate the dangerous Wumpus World to find gold and escape alive")
    print("  • Avoid deadly Wumpuses and bottomless pits")
    print("  • Use your knowledge base to make intelligent decisions")
    
    print("\n🎮 GAME CONTROLS:")
    print("  SPACE        - Execute one manual step (when auto-play is OFF)")
    print("  A            - Toggle Auto-play mode (ON/OFF)")
    print("  M            - Toggle Moving Wumpus Module (Advance Setting)")
    print("  R            - Reset/Restart current game")
    print("  Q            - Quit game")
    
    print("\n🎮 GAME OVER SCREEN CONTROLS:")
    print("  R            - Restart with new game environment")
    print("  SPACE/ENTER  - Continue viewing results")
    print("  Q            - Quit application")
    
    print("\n⚙️ GAME FEATURES:")
    print("  📊 Statistics Display:")
    print("     • Performance rating and final score")
    print("     • Total actions taken and exploration percentage")
    print("     • Game outcome with specific death causes")
    
    print("\n  🤖 Agent Intelligence:")
    print("     • Knowledge-based reasoning using logical inference")
    print("     • Safe path planning and risk assessment")
    print("     • Wumpus hunting with arrow shots")
    
    print("\n  🌟 Advanced Features:")
    print("     • Moving Wumpus Module: Wumpuses move every 5 actions")
    print("     • Enhanced death messages (Wumpus/Pit specific)")
    print("     • Visual game over screen with animations")
    print("     • Restart functionality for multiple games")
    
    print("\n🎯 GAME ELEMENTS:")
    print("  A  - Agent (You)")
    print("  W  - Wumpus (Deadly creature)")
    print("  G  - Gold (Your objective)")
    print("  P  - Pit (Bottomless hole)")
    print("  .  - Safe empty cell")
    print("  #  - Wall boundary")
    
    print("\n🧠 KNOWLEDGE BASE:")
    print("  • Agent uses logical reasoning to deduce safe moves")
    print("  • Percepts: Stench (near Wumpus), Breeze (near Pit)")
    print("  • Knowledge facts: safe/unsafe cells, Wumpus locations")
    
    print("\n🎮 GAMEPLAY MODES:")
    print("  Manual Mode:  Use SPACE to execute each step carefully")
    print("  Auto Mode:    Agent automatically executes optimal moves")
    print("  Standard:     Static Wumpuses for classic gameplay")
    print("  Advanced:     Moving Wumpuses for increased challenge")
    
    print("\n💡 TIPS:")
    print("  • Watch percepts to identify nearby dangers")
    print("  • Use auto-play to see agent's reasoning in action")
    print("  • Try both standard and advanced modes")
    print("  • Restart anytime to try different strategies")
    
    print("="*80)
    print("🚀 Press any key to start the game...")
    print("="*80)

def display_in_game_help(advance_enabled, auto_step):
    """Display concise in-game help during gameplay"""
    print("\n" + "="*50)
    print("📋 QUICK HELP")
    print("="*50)
    print("🎮 CONTROLS:")
    print("  SPACE - Manual step")
    print("  A     - Toggle auto-play")
    print("  M     - Toggle Moving Wumpus")
    print("  R     - Reset game")
    print("  H     - Show this help")
    print("  Q     - Quit")
    
    print("\n🎯 CURRENT STATUS:")
    print(f"  Auto-play: {'🟢 ON' if auto_step else '🔴 OFF'}")
    print(f"  Moving Wumpus: {'🟢 ON' if advance_enabled else '🔴 OFF'}")
    
    print("\n🧠 GAME ELEMENTS:")
    print("  A=Agent, W=Wumpus, G=Gold, P=Pit")
    print("  Percepts: Stench(Wumpus nearby), Breeze(Pit nearby)")
    print("="*50)

def display_visual_instructions():
    """Display animated visual instructions overlay in game window"""
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    BLUE = (100, 149, 237)
    GOLD = (255, 215, 0)
    GREEN = (0, 255, 0)
    GRAY = (128, 128, 128)
    PURPLE = (147, 112, 219)
    RED = (255, 0, 0)
    
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    
    # Fonts
    title_font = pygame.font.Font(None, 48)
    header_font = pygame.font.Font(None, 36)
    detail_font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 20)
    
    # Particle system for background effect
    particles = []
    for _ in range(50):
        particles.append({
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT),
            'dx': random.uniform(-1, 1),
            'dy': random.uniform(-1, 1),
            'size': random.randint(1, 3),
            'color': random.choice([BLUE, PURPLE, GOLD])
        })
    
    showing = True
    while showing:
        current_time = pygame.time.get_ticks()
        animation_time = (current_time - start_time) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_h, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN]:
                    showing = False
                    return True
        
        # Draw background with gradient effect
        WIN.fill(BLACK)
        
        # Draw animated particles
        for particle in particles:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            
            # Wrap around screen
            if particle['x'] < 0: particle['x'] = WIDTH
            if particle['x'] > WIDTH: particle['x'] = 0
            if particle['y'] < 0: particle['y'] = HEIGHT
            if particle['y'] > HEIGHT: particle['y'] = 0
            
            # Pulsing effect
            alpha = 100 + 50 * math.sin(animation_time * 3 + particle['x'] * 0.01)
            color = (*particle['color'], int(alpha))
            
            # Create surface for alpha blending
            particle_surface = pygame.Surface((particle['size']*2, particle['size']*2))
            particle_surface.set_alpha(int(alpha))
            particle_surface.fill(particle['color'])
            WIN.blit(particle_surface, (particle['x'], particle['y']))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 20, 40))
        WIN.blit(overlay, (0, 0))
        
        # Main title with glow effect
        title_y = 40
        glow_offset = 3 * math.sin(animation_time * 2)
        
        # Title glow
        for offset in range(3, 0, -1):
            glow_surface = title_font.render("🎮 GAME INSTRUCTIONS 🎮", True, BLUE)
            glow_surface.set_alpha(30 * offset)
            glow_rect = glow_surface.get_rect(center=(WIDTH//2 + glow_offset, title_y + offset))
            WIN.blit(glow_surface, glow_rect)
        
        # Main title
        title_surface = title_font.render("🎮 GAME INSTRUCTIONS 🎮", True, GOLD)
        title_rect = title_surface.get_rect(center=(WIDTH//2 + glow_offset, title_y))
        WIN.blit(title_surface, title_rect)
        
        # Controls section
        controls_y = 100
        controls_title = header_font.render("🎯 CONTROLS", True, GREEN)
        controls_rect = controls_title.get_rect(center=(WIDTH//2, controls_y))
        WIN.blit(controls_title, controls_rect)
        
        # Control items with icons and descriptions
        controls = [
            ("SPACE", "Execute manual step", WHITE),
            ("A", "Toggle auto-play mode", BLUE),
            ("M", "Toggle Moving Wumpus", PURPLE),
            ("R", "Reset/Restart game", GREEN),
            ("H", "Show/Hide this help", GOLD),
            ("Q", "Quit game", RED)
        ]
        
        for i, (key, desc, color) in enumerate(controls):
            y_pos = controls_y + 40 + i * 30
            
            # Sliding animation
            slide_offset = max(0, 300 - (animation_time - i * 0.1) * 500)
            x_pos = WIDTH//2 - 200 + slide_offset
            
            if slide_offset <= 0:  # Only show when animation is complete
                # Key box
                key_surface = detail_font.render(f"[{key}]", True, color)
                WIN.blit(key_surface, (x_pos, y_pos))
                
                # Description
                desc_surface = detail_font.render(f"- {desc}", True, WHITE)
                WIN.blit(desc_surface, (x_pos + 100, y_pos))
        
        # Game elements section
        elements_y = 360
        elements_alpha = max(0, 255 * (animation_time - 1.5))
        if elements_alpha > 0:
            elements_title = header_font.render("🎯 GAME ELEMENTS", True, GREEN)
            elements_title.set_alpha(int(min(255, elements_alpha)))
            elements_rect = elements_title.get_rect(center=(WIDTH//2, elements_y))
            WIN.blit(elements_title, elements_rect)
            
            elements = [
                ("A", "Agent (You)", WHITE),
                ("W", "Wumpus (Deadly)", RED),
                ("G", "Gold (Objective)", GOLD),
                ("P", "Pit (Dangerous)", GRAY),
                (".", "Safe cell", GREEN),
                ("#", "Wall", WHITE)
            ]
            
            for i, (symbol, desc, color) in enumerate(elements):
                y_pos = elements_y + 40 + i * 25
                x_pos = WIDTH//2 - 150
                
                symbol_surface = detail_font.render(f"[{symbol}]", True, color)
                symbol_surface.set_alpha(int(min(255, elements_alpha)))
                WIN.blit(symbol_surface, (x_pos, y_pos))
                
                desc_surface = small_font.render(f"- {desc}", True, WHITE)
                desc_surface.set_alpha(int(min(255, elements_alpha)))
                WIN.blit(desc_surface, (x_pos + 60, y_pos))
        
        # Features section
        features_y = 550
        features_alpha = max(0, 255 * (animation_time - 2.5))
        if features_alpha > 0:
            features_title = header_font.render("✨ FEATURES", True, PURPLE)
            features_title.set_alpha(int(min(255, features_alpha)))
            features_rect = features_title.get_rect(center=(WIDTH//2, features_y))
            WIN.blit(features_title, features_rect)
            
            features = [
                "🧠 AI Knowledge Base System",
                "🐉 Moving Wumpus Module",
                "💀 Specific Death Messages",
                "🔄 Restart Functionality",
                "📊 Detailed Statistics"
            ]
            
            for i, feature in enumerate(features):
                y_pos = features_y + 40 + i * 25
                feature_surface = small_font.render(feature, True, WHITE)
                feature_surface.set_alpha(int(min(255, features_alpha)))
                feature_rect = feature_surface.get_rect(center=(WIDTH//2, y_pos))
                WIN.blit(feature_surface, feature_rect)
        
        # Exit instruction at bottom
        exit_y = HEIGHT - 50
        exit_alpha = 150 + 100 * math.sin(animation_time * 3)
        exit_surface = detail_font.render("Press H, ESC, SPACE, or ENTER to close", True, GOLD)
        exit_surface.set_alpha(int(exit_alpha))
        exit_rect = exit_surface.get_rect(center=(WIDTH//2, exit_y))
        WIN.blit(exit_surface, exit_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return True

def display_welcome_screen():
    """Display animated welcome screen with basic instructions"""
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    BLUE = (100, 149, 237)
    GOLD = (255, 215, 0)
    GREEN = (0, 255, 0)
    PURPLE = (147, 112, 219)
    
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    
    # Fonts
    title_font = pygame.font.Font(None, 64)
    subtitle_font = pygame.font.Font(None, 36)
    detail_font = pygame.font.Font(None, 28)
    
    # Particle system
    particles = []
    for _ in range(30):
        particles.append({
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT),
            'dx': random.uniform(-0.5, 0.5),
            'dy': random.uniform(-0.5, 0.5),
            'size': random.randint(2, 4),
            'color': random.choice([BLUE, PURPLE, GOLD])
        })
    
    showing = True
    while showing:
        current_time = pygame.time.get_ticks()
        animation_time = (current_time - start_time) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                showing = False
                return True
        
        # Background
        WIN.fill(BLACK)
        
        # Animated particles
        for particle in particles:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            
            if particle['x'] < 0: particle['x'] = WIDTH
            if particle['x'] > WIDTH: particle['x'] = 0
            if particle['y'] < 0: particle['y'] = HEIGHT
            if particle['y'] > HEIGHT: particle['y'] = 0
            
            alpha = 100 + 50 * math.sin(animation_time * 2 + particle['x'] * 0.01)
            particle_surface = pygame.Surface((particle['size']*2, particle['size']*2))
            particle_surface.set_alpha(int(alpha))
            particle_surface.fill(particle['color'])
            WIN.blit(particle_surface, (particle['x'], particle['y']))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 30, 60))
        WIN.blit(overlay, (0, 0))
        
        # Main title with animation
        title_y = 150
        title_offset = 10 * math.sin(animation_time * 1.5)
        
        # Title glow effect
        for offset in range(4, 0, -1):
            glow_surface = title_font.render("🎮 WUMPUS WORLD 🎮", True, BLUE)
            glow_surface.set_alpha(20 * offset)
            glow_rect = glow_surface.get_rect(center=(WIDTH//2, title_y + title_offset + offset))
            WIN.blit(glow_surface, glow_rect)
        
        # Main title
        title_surface = title_font.render("🎮 WUMPUS WORLD 🎮", True, GOLD)
        title_rect = title_surface.get_rect(center=(WIDTH//2, title_y + title_offset))
        WIN.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_alpha = max(0, 255 * (animation_time - 1))
        if subtitle_alpha > 0:
            subtitle_surface = subtitle_font.render("AI Knowledge-Based Agent Adventure", True, WHITE)
            subtitle_surface.set_alpha(int(min(255, subtitle_alpha)))
            subtitle_rect = subtitle_surface.get_rect(center=(WIDTH//2, title_y + 80))
            WIN.blit(subtitle_surface, subtitle_rect)
        
        # Quick start instructions
        instructions_alpha = max(0, 255 * (animation_time - 2))
        if instructions_alpha > 0:
            instructions = [
                "🎯 Find the gold and escape alive!",
                "🧠 Use AI reasoning to avoid dangers",
                "",
                "Quick Controls:",
                "SPACE - Manual step  |  A - Auto-play",
                "H - Help screen  |  M - Moving Wumpus",
                "R - Restart  |  Q - Quit"
            ]
            
            for i, instruction in enumerate(instructions):
                if instruction:  # Skip empty lines
                    color = GOLD if "Quick Controls:" in instruction else WHITE
                    font = subtitle_font if "Quick Controls:" in instruction else detail_font
                    
                    inst_surface = font.render(instruction, True, color)
                    inst_surface.set_alpha(int(min(255, instructions_alpha)))
                    inst_rect = inst_surface.get_rect(center=(WIDTH//2, 300 + i * 35))
                    WIN.blit(inst_surface, inst_rect)
        
        # Press any key prompt
        prompt_alpha = 150 + 100 * math.sin(animation_time * 4)
        prompt_surface = detail_font.render("Press any key to start your adventure!", True, GREEN)
        prompt_surface.set_alpha(int(prompt_alpha))
        prompt_rect = prompt_surface.get_rect(center=(WIDTH//2, HEIGHT - 100))
        WIN.blit(prompt_surface, prompt_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return True

if __name__ == "__main__":
    print(f"🎮 Starting Wumpus World {GAME_N}x{GAME_N} with {GAME_NUM_WUMPUS} wumpus(es) and {GAME_PIT_PROB:.1%} pit probability")
    print(f"🤖 Agent type: {'Random Agent' if GAME_AGENT_TYPE == 'random' else 'Knowledge-Based Agent'}")
    
    # Display game instructions
    display_game_instructions()
    
    # Choose which version to run based on config
    if GAME_CONSOLE_MODE:
        # Run console version
        if GAME_AGENT_TYPE == "random":
            run_random_agent()
        else:
            run_game()
    else:
        # Run GUI version with proper asset positioning
        run_game_with_gui()