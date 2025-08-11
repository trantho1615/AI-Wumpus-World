import os
import pygame
import random
from utils import scale, get_assets, rotate, generate_positions, generate_pit_positions, load_map_tiles, scale_for_grid

WIDTH = 800
HEIGHT = 800

pygame.init()

FPS = 30

# Generate random NxN grid size (between 3 and 8 for playability)
# N = random.randint(4, 8)
N = 8
# print(f"Generated {N}x{N} Wumpus World grid")

TILE_MAPS = load_map_tiles()
print(f"Loaded {len(TILE_MAPS)} map tiles: {list(TILE_MAPS.keys())}")

# Pit probability - percentage chance each cell has a pit (excluding starting position)
PIT_PROBABILITY = 0.2  # 20% chance each cell contains a pit
print(f"Pit probability set to {PIT_PROBABILITY * 100}%")

POSITIONS = generate_positions(N)
print(POSITIONS)
pit_pos_index = generate_pit_positions(N, PIT_PROBABILITY)

PIT_POSITIONS = [
    (POSITIONS[row][col]) for col, row in pit_pos_index if (col, row) != (0, 0)
]
# print(f"Generated pits at positions: {PIT_POSITIONS}")

ASSETS = os.path.join(os.path.dirname(
    __file__), 'assets')

FONT = os.path.join(ASSETS, 'Arial.ttf')

LIGHT = get_assets(ASSETS, 'light.png')[0]
LIGHT = scale_for_grid(LIGHT, N, "default", WIDTH, HEIGHT)

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


GOLD = get_assets(ASSETS, 'gold.png')[0]
GOLD = scale_for_grid(GOLD, N, "gold", WIDTH, HEIGHT)

PIT = get_assets(ASSETS, 'pit.png')[0]
PIT = scale_for_grid(PIT, N, "pit", WIDTH, HEIGHT)

EXIT = get_assets(ASSETS, 'exit.png')[0]
EXIT = scale_for_grid(EXIT, N, "exit", WIDTH, HEIGHT)

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Wumpus World CLI Game Interface')
