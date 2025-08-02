import random
from typing import List, Tuple, Set
from config import (
    GRID_SIZE, PIT_PROB, NUM_WUMPUS, START_POS, START_FACING,
    ACTION_COST, SHOOT_COST, GOLD_REWARD, DEATH_PENALTY, WARNING_TYPES, GAME_OBJECTS
)

git
class Position:

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, Position) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def adjacent_cells(self) -> List['Position']:
        """Return a list of adjacent cells (north, south, east, west)."""
        return [
            Position(self.x, self.y + 1),  # North
            Position(self.x, self.y - 1),  # South
            Position(self.x + 1, self.y),  # East
            Position(self.x - 1, self.y)  # West
        ]


class Entity:
    """Base class for all entities"""

    def __init__(self, pos: Position, obj_type: str):
        self.pos = pos
        self.obj_type = obj_type  # Type of object (hunter, wumpus, pit, gold, exit)

    def move_to(self, pos: Position):
        self.pos = pos


class Player(Entity):
    """Class to represent the player (Hunter) in the Wumpus World."""
    def __init__(self, pos: Position, facing: str = START_FACING):
        super().__init__(pos, GAME_OBJECTS['HUNTER'])
        self.facing = facing  # Can be 'up', 'down', 'left', 'right'
        self.state = 'idle'  # Current state: idle, move, shoot
        self.has_arrow = True
        self.has_gold = False
        self.is_alive = True
        self.score = 0
        self.action_count = 0  # Track number of actions for moving Wumpus (advanced setting)

    def move_forward(self, world: 'WumpusWorld') -> Tuple[bool, str]:
        """Move foward based on current facing direction"""
        self.action_count += 1
        self.score += ACTION_COST
        self.state = 'move'
        new_pos = self._get_forward_position()
        if world.in_bounds(new_pos) and not world.is_wall(new_pos):
            self.move_to(new_pos)
            self.state = 'idle'
            return True, ""
        self.state = 'idle'
        return False, "Bump: Hit a wall!"

    def turn_left(self):
        """Turn the player 90 degrees to the left."""
        self.action_count += 1
        self.score += ACTION_COST
        self.state = 'idle'
        dirs = ["up", "left", "down", "right"]
        idx = dirs.index(self.facing)
        self.facing = dirs[(idx + 1) % 4]

    def turn_right(self):
        """Turn the player 90 degrees to the right."""
        self.action_count += 1
        self.score += ACTION_COST
        self.state = 'idle'
        dirs = ["up", "right", "down", "left"]
        idx = dirs.index(self.facing)
        self.facing = dirs[(idx + 1) % 4]

    def grab_gold(self, world: 'WumpusWorld') -> str:
        """Grab the gold if present in the current cell."""
        self.action_count += 1
        self.score += ACTION_COST
        self.state = 'idle'
        if world.is_gold(self.pos):
            world.gold.is_taken = True
            self.has_gold = True
            self.score += GOLD_REWARD
            return "Success: Grabbed the gold!"
        return "Warning: No gold to grab here!"

    def shoot(self, world: 'WumpusWorld') -> str:
        """Shoot an arrow in the current facing direction."""
        self.action_count += 1
        self.score += SHOOT_COST
        self.state = 'shoot'
        if not self.has_arrow:
            self.state = 'idle'
            return "Warning: No arrows left!"
        self.has_arrow = False
        path = self._get_shooting_path(world)
        for pos in path:
            for wumpus in world.wumpus:
                if wumpus.pos == pos and wumpus.is_alive:
                    wumpus.is_alive = False
                    wumpus.state = 'dead'
                    self.state = 'idle'
                    return "Scream: Wumpus killed!"
        self.state = 'idle'
        return "Warning: Arrow missed!"

    def climb(self, world: 'WumpusWorld') -> Tuple[bool, str]:
        """Climb out if at (0,0) and has gold."""
        self.action_count += 1
        self.score += ACTION_COST
        self.state = 'idle'
        if self.pos == Position(0, 0) and self.has_gold:
            return True, "Winner: Escaped with the gold!"
        return False, "Warning: Cannot climb out yet!"

    def _get_forward_position(self) -> Position:
        """Calculate the position in front based on facing direction."""
        if self.facing == "up":
            return Position(self.pos.x, self.pos.y + 1)
        elif self.facing == "down":
            return Position(self.pos.x, self.pos.y - 1)
        elif self.facing == "right":
            return Position(self.pos.x + 1, self.pos.y)
        elif self.facing == "left":
            return Position(self.pos.x - 1, self.pos.y)

    def _get_shooting_path(self, world: 'WumpusWorld') -> List[Position]:
        """Calculate the path of the arrow based on facing direction."""
        path = []
        current = self.pos
        while world.in_bounds(current) and not world.is_wall(current):
            path.append(current)
            if self.facing == "up":
                current = Position(current.x, current.y + 1)
            elif self.facing == "down":
                current = Position(current.x, current.y - 1)
            elif self.facing == "right":
                current = Position(current.x + 1, current.y)
            elif self.facing == "left":
                current = Position(current.x - 1, current.y)
        return path


class Wumpus(Entity):
    """Class to represent a Wumpus in the Wumpus World."""

    def __init__(self, pos: Position):
        super().__init__(pos, GAME_OBJECTS['WUMPUS'])
        self.is_alive = True
        self.state = 'idle'  # idle or dead

    def move(self, world: 'WumpusWorld'):
        """Move to a random adjacent cell if possible (advanced setting)."""
        if not self.is_alive:
            return
        valid_moves = [
            pos for pos in self.pos.adjacent_cells()
            if (world.in_bounds(pos) and not world.is_wall(pos) and
                not world.is_pit(pos) and not any(w.pos == pos for w in world.wumpus if w.is_alive))
        ]
        if valid_moves:
            new_pos = random.choice(valid_moves)
            if world.player.pos == new_pos:
                world.player.is_alive = False
                world.player.score += DEATH_PENALTY
            else:
                self.move_to(new_pos)


class Pit(Entity):
    """Class to represent a Pit in the Wumpus World."""

    def __init__(self, pos: Position):
        super().__init__(pos, GAME_OBJECTS['PIT'])


class Gold(Entity):
    """Class to represent the Gold in the Wumpus World."""

    def __init__(self, pos: Position):
        super().__init__(pos, GAME_OBJECTS['GOLD'])
        self.is_taken = False


class WumpusWorld:
    """Class to represent the Wumpus World environment."""

    def __init__(self, size: int = GRID_SIZE, num_wumpus: int = NUM_WUMPUS, pit_prob: float = PIT_PROB):
        self.size = size
        self.num_wumpus = num_wumpus
        self.pit_prob = pit_prob
        self.player = None
        self.wumpus = []
        self.pits = []
        self.gold = None
        self.exit = Position(0, 0)  # Exit position
        self.walls = self._generate_walls()

    def _generate_walls(self) -> Set[Position]:
        """Generate walls surrounding the grid."""
        walls = set()
        for x in range(-1, self.size + 1):
            walls.add(Position(x, -1))
            walls.add(Position(x, self.size))
        for y in range(self.size):
            walls.add(Position(-1, y))
            walls.add(Position(self.size, y))
        return walls

    def initialize(self):
        """Randomly initialize the environment."""
        self.player = Player(Position(*START_POS))
        available_cells = [
            Position(x, y) for x in range(self.size) for y in range(self.size)
            if
            Position(x, y) != Position(*START_POS) and Position(x, y) != Position(1, 0) and Position(x, y) != Position(
                0, 1)
        ]
        # Place Wumpus
        wumpus_positions = random.sample(available_cells, self.num_wumpus)
        self.wumpus = [Wumpus(pos) for pos in wumpus_positions]
        available_cells = [pos for pos in available_cells if pos not in wumpus_positions]
        # Place Gold
        gold_pos = random.choice(available_cells)
        self.gold = Gold(gold_pos)
        available_cells.remove(gold_pos)
        # Place Pits
        self.pits = [
            Pit(pos) for pos in available_cells
            if random.random() < self.pit_prob
        ]

    def is_wall(self, pos: Position) -> bool:
        return pos in self.walls

    def is_pit(self, pos: Position) -> bool:
        return any(pit.pos == pos for pit in self.pits)

    def is_wumpus(self, pos: Position) -> bool:
        return any(w.pos == pos and w.is_alive for w in self.wumpus)

    def is_gold(self, pos: Position) -> bool:
        return self.gold and self.gold.pos == pos and not self.gold.is_taken

    def is_exit(self, pos: Position) -> bool:
        return pos == self.exit

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.x < self.size and 0 <= pos.y < self.size

    def get_percepts(self) -> List[str]:
        """Return percepts as a list of warning types."""
        percepts = []
        stench = any(w.pos in self.player.pos.adjacent_cells() and w.is_alive for w in self.wumpus)
        breeze = any(pit.pos in self.player.pos.adjacent_cells() for pit in self.pits)
        glitter = self.is_gold(self.player.pos)
        bump = not self.in_bounds(self.player._get_forward_position()) or self.is_wall(
            self.player._get_forward_position())
        scream = any(not w.is_alive for w in self.wumpus)

        if stench and breeze:
            percepts.append(WARNING_TYPES['BREEZE_STENCH'])
        else:
            if stench:
                percepts.append(WARNING_TYPES['STENCH'])
            if breeze:
                percepts.append(WARNING_TYPES['BREEZE'])
        if glitter:
            percepts.append(WARNING_TYPES['GOLD'])
        if bump:
            percepts.append('bump')
        if scream:
            percepts.append('scream')
        return percepts

    def update_wumpus_movement(self):
        """Move each Wumpus after every 5 actions (advanced setting)."""
        if self.player.action_count % 5 == 0:
            for wumpus in self.wumpus:
                wumpus.move(self)

    def check_collisions(self) -> str:
        """Check if player hits a Wumpus or pit."""
        if self.is_wumpus(self.player.pos):
            self.player.is_alive = False
            self.player.score += DEATH_PENALTY
            return "Game Over: Wumpus killed you!"
        if self.is_pit(self.player.pos):
            self.player.is_alive = False
            self.player.score += DEATH_PENALTY
            return "Game Over: You fell into a pit!"
        return ""

