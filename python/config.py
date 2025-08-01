# Grid dimensions
GRID_SIZE = 8
GRID_WIDTH = GRID_SIZE
GRID_HEIGHT = GRID_SIZE

# Game settings
PIT_PROB = 0.2  # Probability of a pit in each cell
NUM_WUMPUS = 2  # Number of Wumpus
START_POS = (0, 0)  # Starting position of the player
START_FACING = "right"  # Starting direction of the player

# Scoring rules
ACTION_COST = -1  # Cost for move, turn, grab, climb
SHOOT_COST = -10  # Cost for shooting
GOLD_REWARD = 1000  # Reward for grabbing gold
DEATH_PENALTY = -1000  # Penalty for dying (Wumpus or pit)

# Game entities and states
HUNTER_STATES = ['idle', 'move', 'shoot']
WUMPUS_STATES = ['idle', 'dead']

# Warning types
WARNING_TYPES = {
    'BREEZE': 'breeze',      # Indicates pit nearby
    'STENCH': 'stench',      # Indicates wumpus nearby
    'BREEZE_STENCH': 'both', # Both warnings present
    'GOLD': 'gold'           # Gold present
}

# Game objects
GAME_OBJECTS = {
    'HUNTER': 'hunter',
    'WUMPUS': 'wumpus',
    'GOLD': 'gold',
    'PIT': 'pit',
    'EXIT': 'exit'
}