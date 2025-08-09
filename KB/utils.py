import os
import pygame
import random

ASSETS = os.path.join(os.path.dirname(
    __file__), 'assets')


def scale(image, width: int = 30, height: int = 15):
    """Scale the image to the specified width and height."""
    image = pygame.transform.scale(image, (width, height))
    return image


def rotate(image, angle):
    """Rotate the image to the specified angle."""
    image = pygame.transform.rotate(image, angle)
    return image


def get_assets(folder: str = None, files: str = ''):
    """get all assets with name starting with files... from the specified folder"""
    if folder:
        assets_path = os.path.join(ASSETS, folder)
    else:
        assets_path = ASSETS

    assets_files = os.listdir(assets_path)
    assets_files = sorted(assets_files, key=lambda x: (len(x), x))

    assets = []
    for file in assets_files:
        if files in file:
            elem = pygame.image.load(os.path.join(assets_path, file))
            assets.append(elem)
    return assets

# Generate pit positions based on probability
def generate_pit_positions(grid_size, pit_probability):
    """Generate random pit positions based on probability, avoiding starting position (0,0)"""
    pit_positions = []
    for row in range(grid_size):
        for col in range(grid_size):
            # Skip starting position (0,0)
            if row == 0 and col == 0:
                continue
            # Random chance for pit based on probability
            if random.random() < pit_probability:
                pit_positions.append((col, row))  # Use (col, row) format
    return pit_positions


# Calculate positions dynamically based on grid size
def generate_positions(grid_size, width=800, height=800):
    """Generate positions for an NxN grid within the given width and height"""
    # Calculate margins - no margins to fill entire window
    margin_percent = 0.0  # 0% margin = full window utilization
    margin_x = int(width * margin_percent)
    margin_y = int(height * margin_percent)
    
    # Available space for the grid
    available_width = width - (2 * margin_x)
    available_height = height - (2 * margin_y)
    
    # Calculate cell dimensions with proper spacing
    if grid_size == 1:
        # Special case for 1x1 grid - center it
        cell_width = available_width
        cell_height = available_height
    else:
        # Use float division for more precise calculations
        cell_width = available_width / grid_size
        cell_height = available_height / grid_size
    
    positions = []
    for row in range(grid_size):
        row_positions = []
        for col in range(grid_size):
            # Calculate center position of each cell
            x = margin_x + (col * cell_width) + (cell_width / 2)
            y = margin_y + (row * cell_height) + (cell_height / 2)
            
            # Convert to integers for pixel positions
            x = int(x)
            y = int(y)
            
            # Flip Y coordinate for Wumpus World convention (0,0 at bottom-left)
            # Row 0 should be at bottom, row (grid_size-1) at top
            flipped_y = height - y
            
            row_positions.append((x, flipped_y))
        positions.append(row_positions)
    
    return tuple(positions)

def debug_positions(grid_size, width=800, height=800):
    """Debug function to visualize grid positions"""
    positions = generate_positions(grid_size, width, height)
    print(f"Grid: {grid_size}x{grid_size}, Canvas: {width}x{height}")
    print("Position matrix (x, y) - Wumpus World convention (0,0) at bottom-left:")
    
    # Print grid from top to bottom (visually correct)
    for row in range(grid_size-1, -1, -1):
        row_str = f"Row {row}: "
        for col in range(grid_size):
            x, y = positions[row][col]
            row_str += f"({x:3},{y:3}) "
        print(row_str)
    
    # Print spacing information
    margin_x = int(width * 0.05)  # Match the reduced margin
    margin_y = int(height * 0.05)
    available_width = width - (2 * margin_x)
    available_height = height - (2 * margin_y)
    cell_width = available_width / grid_size
    cell_height = available_height / grid_size
    
    print(f"\nSpacing info:")
    print(f"  Margins: {margin_x}px horizontal, {margin_y}px vertical")
    print(f"  Cell size: {cell_width:.1f}x{cell_height:.1f} pixels")
    print(f"  Available area: {available_width}x{available_height} pixels")
    
    return positions

def load_map_tiles():
    """Load all 9 map tiles and return as dictionary"""
    tiles = {}
    tile_mapping = {
        'map11': '11', # bottom-left corner
        'map12': '12',  # left edge
        'map13': '13',  # top-left corner
        'map21': '21',  # bottom edge
        'map22': '22',  # center/inside
        'map23': '23',  # top edge
        'map31': '31',  # top-right corner
        'map32': '32',  # right edge
        'map33': '33'  # bottom-right corner
    }

    for filename, tile_id in tile_mapping.items():
        try:
            tile_path = os.path.join(ASSETS, f'{filename}.png')
            if os.path.exists(tile_path):
                tiles[filename] = pygame.image.load(tile_path)
            else:
                print(f"Warning: Tile {filename}.png not found")
        except Exception as e:
            print(f"Error loading tile {filename}: {e}")

    return tiles

def load_map(map_name, grid_size=4, width=800, height=800):
    """Load and scale map tile for the given grid size"""
    MAP = get_assets(files=f'{map_name}.png')[0]
    # Scale tiles to fit grid cells perfectly
    return scale_for_grid(MAP, grid_size, "tile", width, height)

def calculate_scaling_factor(grid_size, width=800, height=800):
    """Calculate optimal scaling factor based on grid size and cell dimensions"""
    # Calculate cell dimensions
    margin_x = int(width * 0.0)  # No margins
    margin_y = int(height * 0.0)
    available_width = width - (2 * margin_x)
    available_height = height - (2 * margin_y)
    cell_width = available_width / grid_size
    cell_height = available_height / grid_size
    
    # Base scaling factors for different grid sizes
    # Smaller grids = larger assets, larger grids = smaller assets
    base_scale = min(cell_width, cell_height) / 100  # Base reference: 100px
    
    # Clamp scaling between reasonable bounds
    min_scale = 0.2
    max_scale = 2.0
    scale_factor = max(min_scale, min(max_scale, base_scale))
    
    return scale_factor, cell_width, cell_height

def scale_for_grid(image, grid_size, asset_type="default", width=800, height=800):
    """Scale image optimally for the given grid size"""
    scale_factor, cell_width, cell_height = calculate_scaling_factor(grid_size, width, height)
    
    # Different asset types need different scaling approaches
    scaling_multipliers = {
        "hunter": 0.6,      # Hunter should be prominent but not fill entire cell
        "wumpus": 0.7,      # Wumpus slightly larger than hunter
        "gold": 0.4,        # Gold smaller and more delicate
        "pit": 0.8,         # Pit should fill most of the cell
        "warning": 0.3,     # Warning icons small and in corner
        "tile": 1.0,        # Tiles fill entire cell
        "default": 0.5      # Default moderate size
    }
    
    multiplier = scaling_multipliers.get(asset_type, 0.5)
    
    # Calculate target size based on cell dimensions
    target_size = min(cell_width, cell_height) * multiplier
    
    # Get original dimensions
    original_width = image.get_width()
    original_height = image.get_height()
    
    # Calculate scale to fit target size while maintaining aspect ratio
    scale_x = target_size / original_width
    scale_y = target_size / original_height
    final_scale = min(scale_x, scale_y)
    
    # Apply scaling
    new_width = int(original_width * final_scale)
    new_height = int(original_height * final_scale)
    
    return scale(image, new_width, new_height)