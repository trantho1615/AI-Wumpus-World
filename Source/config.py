import os
import pygame
import argparse
import sys
from utils import get_assets, rotate, generate_positions, generate_pit_positions, load_map_tiles, scale_for_grid

# Grid size on pixel
WIDTH = 800
HEIGHT = 800

pygame.init()
pygame.mixer.init()  # Initialize pygame mixer for sound effects

FPS = 30

# Parse command line arguments
def parse_arguments():
    """Parse command line arguments for game configuration"""
    parser = argparse.ArgumentParser(
        description='Wumpus World AI Game',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python main.py                    # Default: 8x8 grid, 2 wumpuses, 20% pits, KB agent, GUI
        python main.py 4                  # 4x4 grid with defaults
        python main.py 4 1 0.01           # 4x4 grid, 1 wumpus, 1% pits
        python main.py 6 3 0.15 -r        # 6x6 grid, 3 wumpuses, 15% pits, random agent
        python main.py 4 1 0.01 -a --console  # 4x4 grid, KB agent, console mode
        """
    )
    
    # Positional arguments
    parser.add_argument('grid_size', nargs='?', type=int, default=8,
                       help='Grid size N for NxN world (default: 8)')
    parser.add_argument('num_wumpus', nargs='?', type=int, default=2,
                       help='Number of wumpuses in the world (default: 2)')
    parser.add_argument('pit_prob', nargs='?', type=float, default=0.2,
                       help='Probability of pits in each cell (default: 0.2)')
    
    # Optional arguments
    parser.add_argument('--console', action='store_true',
                       help='Run in console mode instead of GUI')
    parser.add_argument('-r', '--random', action='store_true',
                       help='Use random agent instead of KB agent')
    parser.add_argument('-a', '--kb-agent', action='store_true',
                       help='Use KB agent (default behavior)')
    parser.add_argument('--no-light', action='store_true',
                       help='Disable fog of war light effect')
    
    args = parser.parse_args()
    
    # Validation
    if not (3 <= args.grid_size <= 20):
        print(f"❌ Error: Grid size must be between 3 and 20, got {args.grid_size}")
        sys.exit(1)
    
    max_wumpuses = args.grid_size * args.grid_size - 2  # Leave space for agent and gold
    if not (0 <= args.num_wumpus <= max_wumpuses):
        print(f"❌ Error: Number of wumpuses must be between 0 and {max_wumpuses} for {args.grid_size}x{args.grid_size} grid, got {args.num_wumpus}")
        sys.exit(1)
    
    if not (0.0 <= args.pit_prob <= 1.0):
        print(f"❌ Error: Pit probability must be between 0.0 and 1.0, got {args.pit_prob}")
        sys.exit(1)
    
    return args

# Parse arguments and set global game configuration
args = parse_arguments()

# Global game configuration variables
GAME_N = args.grid_size
GAME_NUM_WUMPUS = args.num_wumpus
GAME_PIT_PROB = args.pit_prob
GAME_CONSOLE_MODE = args.console
GAME_AGENT_TYPE = 'random' if args.random else 'kb'
GAME_LIGHT_ENABLED = not args.no_light  # Light effect enabled by default

# Use GAME_N for asset scaling and positioning
N = GAME_N
# print(f"Generated {N}x{N} Wumpus World grid")

TILE_MAPS = load_map_tiles()
print(f"Loaded {len(TILE_MAPS)} map tiles: {list(TILE_MAPS.keys())}")

# Advanced Setting: Moving Wumpus Module (can be toggled during gameplay)
ADVANCE_SETTING = False  # Default off, can be toggled with 'M' key
print(f"Moving Wumpus Module (Advance Setting): {'ON' if ADVANCE_SETTING else 'OFF'}")

# Generate pixel positions for the grid base on grid size N
POSITIONS = generate_positions(N)
print(POSITIONS)


#ASSETS
ASSETS = os.path.join(os.path.dirname(
    __file__), 'assets')

FONT = os.path.join(ASSETS, 'Arial.ttf')

LIGHT = get_assets(ASSETS, 'light.png')[0]
LIGHT = scale_for_grid(LIGHT, N, "light", WIDTH, HEIGHT)

hunter_idle_path = os.path.join(ASSETS, 'hunter', 'idle')
HUNTER_IDLE = get_assets(hunter_idle_path, 'survivor-idle')
HUNTER_IDLE = [scale_for_grid(x, N, "hunter", WIDTH, HEIGHT) for x in HUNTER_IDLE]

hunter_move_path = os.path.join(ASSETS, 'hunter', 'move')
HUNTER_MOVE = get_assets(hunter_move_path, 'survivor-move')
HUNTER_MOVE = [scale_for_grid(x, N, "hunter", WIDTH, HEIGHT) for x in HUNTER_MOVE]

hunter_shoot_path = os.path.join(ASSETS, 'hunter', 'shoot')
HUNTER_SHOOT = get_assets(hunter_shoot_path, 'survivor-shoot')
HUNTER_SHOOT = [scale_for_grid(x, N, "hunter", WIDTH, HEIGHT) for x in HUNTER_SHOOT]

warnings_path = os.path.join(ASSETS, 'warnings')
W_BREEZE = get_assets(warnings_path, 'breeze.png')[0]
W_BREEZE = scale_for_grid(W_BREEZE, N, "warning", WIDTH, HEIGHT)

W_STENCH = get_assets(warnings_path, 'stench.png')[0]
W_STENCH = scale_for_grid(W_STENCH, N, "warning", WIDTH, HEIGHT)

W_BS = get_assets(warnings_path, 'breeze-stench.png')[0]
W_BS = scale_for_grid(W_BS, N, "warning", WIDTH, HEIGHT)

W_GOLD = get_assets(warnings_path, 'gold.png')[0]
W_GOLD = scale_for_grid(W_GOLD, N, "warning", WIDTH, HEIGHT)

wumpus_idle_path = os.path.join(ASSETS, 'wumpus', 'idle')
WUMPUS_IDLE = get_assets(wumpus_idle_path, 'skeleton-idle')
WUMPUS_IDLE = [scale_for_grid(x, N, "wumpus", WIDTH, HEIGHT) for x in WUMPUS_IDLE]
WUMPUS_IDLE = [rotate(x, -90) for x in WUMPUS_IDLE]

wumpus_blood_path = os.path.join(ASSETS, 'wumpus')
WUMPUS_BLOOD = get_assets(wumpus_blood_path, 'blood')

# Load Wumpus scream sound effect
wumpus_scream_path = os.path.join(ASSETS, 'wumpus', 'scream.wav')
WUMPUS_SCREAM_SOUND = None
if os.path.exists(wumpus_scream_path):
    try:
        WUMPUS_SCREAM_SOUND = pygame.mixer.Sound(wumpus_scream_path)
        print(f"Loaded Wumpus scream sound: {wumpus_scream_path}")
    except pygame.error as e:
        print(f"Warning: Could not load Wumpus scream sound: {e}")
else:
    print(f"Warning: Wumpus scream sound file not found: {wumpus_scream_path}")


GOLD = get_assets(ASSETS, 'gold.png')[0]
GOLD = scale_for_grid(GOLD, N, "gold", WIDTH, HEIGHT)

PIT = get_assets(ASSETS, 'pit.png')[0]
PIT = scale_for_grid(PIT, N, "pit", WIDTH, HEIGHT)

EXIT = get_assets(ASSETS, 'exit.png')[0]
EXIT = scale_for_grid(EXIT, N, "exit", WIDTH, HEIGHT)

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Wumpus World CLI Game Interface')
