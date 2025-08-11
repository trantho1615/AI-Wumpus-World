import random

MOVE_COST = 1

class Cell:
    def __init__(self):
        self.pit = False
        self.wumpus = False
        self.gold = False

class Environment:
    def __init__(self, size=4, num_wumpus=2, pit_prob=0.2):
        self.size = size
        self.score = 0
        self.grid = [[Cell() for _ in range(size)] for _ in range(size)]
        self.agent_position = (0, 0)
        self.agent_direction = "E"  
        self.arrow_used = False
        self.scream = False
        self.gold_found = False
        # Advanced: Moving Wumpus Module
        self.action_count = 0
        self.wumpus_positions = []  # Track wumpus positions for movement
        self.place_pit_and_wumpus(num_wumpus, pit_prob)
        self.place_gold()
        self.wall = False

    def place_pit_and_wumpus(self, num_wumpus, pit_prob):
        candidates = [(x, y) for x in range(self.size) for y in range(self.size) if (x, y) != (0, 0)]
        random.shuffle(candidates)

        for _ in range(num_wumpus):
            if candidates:
                x, y = candidates.pop()
                self.grid[x][y].wumpus = True
                self.wumpus_positions.append((x, y))  # Track wumpus positions

        for x in range(self.size):
            for y in range(self.size):
                if (x, y) != (0, 0) and not self.grid[x][y].wumpus and random.random() < pit_prob:
                    self.grid[x][y].pit = True

    def place_gold(self):
        while True:
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if not self.grid[x][y].pit and not self.grid[x][y].wumpus and (x, y) != (0, 0):
                self.grid[x][y].gold = True
                break


    def get_percepts(self, pos, bump=False):
        x, y = pos
        stench = breeze = glitter = False
        if self.grid[x][y].gold:
            glitter = True
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if self.grid[nx][ny].wumpus:
                    stench = True
                if self.grid[nx][ny].pit:
                    breeze = True
        return {
            "stench": stench,
            "breeze": breeze,
            "glitter": glitter,
            "bump": bump,
            "scream": self.scream
        }

    def apply_action(self, agent, action):
        x, y = agent.position
        self.scream = False
        
        # Count actions for Moving Wumpus Module
        self.action_count += 1

        if action == "grab":
            if self.grid[x][y].gold:
                self.grid[x][y].gold = False
                self.score += 10
                agent.has_gold = True


        elif action == "climb":

            if (x, y) == (0, 0):

                if agent.has_gold:
                    self.score += 1000

                agent.done = True



        elif action == "move":
            self.score -= 1
            dx, dy = self._get_delta(agent.direction)
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                agent.position = (nx, ny)
                agent.bump = False
                self.check_dead(agent)
            else:
                agent.bump = True



        elif action == "turn_left":
            self.score -= 1
            agent.direction = self._turn_left(agent.direction)

        elif action == "turn_right":
            self.score -= 1
            agent.direction = self._turn_right(agent.direction)

        elif action == "shoot":
            self.score -= 10
            if self.arrow_used:
                return
            self.arrow_used = True
            dx, dy = self._get_delta(agent.direction)
            tx, ty = x + dx, y + dy
            while 0 <= tx < self.size and 0 <= ty < self.size:
                if self.grid[tx][ty].wumpus:
                    self.grid[tx][ty].wumpus = False
                    # Remove from wumpus_positions when killed
                    if (tx, ty) in self.wumpus_positions:
                        self.wumpus_positions.remove((tx, ty))
                    self.scream = True
                    print(f">>> Wumpus at ({tx},{ty}) has been eliminated!")
                    break
                tx += dx
                ty += dy
        
        # Move Wumpus after every 5 actions
        if self.action_count % 5 == 0:
            self.move_wumpus(agent)
            

    def _get_delta(self, direction):
        return {
            "N": (0, 1),
            "E": (1, 0),
            "S": (0, -1),
            "W": (-1, 0)
        }[direction]

    def _turn_left(self, dir):
        return {"N": "W", "W": "S", "S": "E", "E": "N"}[dir]

    def _turn_right(self, dir):
        return {"N": "E", "E": "S", "S": "W", "W": "N"}[dir]

    def check_dead(self, agent):
        x, y = agent.position
        cell = self.grid[x][y]
        if cell.pit:
            print(f"Fell into pit at ({x},{y})!")
        if cell.wumpus:
            print(f"Killed by Wumpus at ({x},{y})!")
        if cell.pit or cell.wumpus:
            self.score -= 1000
            agent.done = True

    def print_state(self, agent):
        print("Map View:")
        wall_row = "# " * (self.size + 2)
        print(wall_row)
        for y in range(self.size - 1, -1, -1):
            row = "# "  # left wall
            for x in range(self.size):
                cell = self.grid[x][y]
                if (x, y) == agent.position:
                    row += "A "
                elif cell.wumpus:
                    row += "W "
                elif cell.pit:
                    row += "P "
                elif cell.gold:
                    row += "G "
                else:
                    row += ". "
            row += "#"
            print(row)
        print(wall_row)

    def place_walls(self, positions):
        for x, y in positions:
            if (x, y) != (0, 0):  
                self.grid[x][y].wall = True

    def move_wumpus(self, agent):
        """Move each Wumpus to a random adjacent cell after every 5 actions"""
        print(f">>> Moving Wumpus (after {self.action_count} actions)...")
        
        new_wumpus_positions = []
        
        for i, (wx, wy) in enumerate(self.wumpus_positions):
            # Get valid adjacent cells for Wumpus movement
            adjacent_cells = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # N, S, E, W
                new_x, new_y = wx + dx, wy + dy
                
                # Check bounds
                if 0 <= new_x < self.size and 0 <= new_y < self.size:
                    # Check if cell is valid (no pit, no other wumpus)
                    if (not self.grid[new_x][new_y].pit and 
                        (new_x, new_y) not in self.wumpus_positions and
                        (new_x, new_y) not in new_wumpus_positions):
                        adjacent_cells.append((new_x, new_y))
            
            # Include current position as an option (stay in place)
            adjacent_cells.append((wx, wy))
            
            # Choose random cell
            if adjacent_cells:
                new_pos = random.choice(adjacent_cells)
                new_x, new_y = new_pos
                
                # Move wumpus in grid
                self.grid[wx][wy].wumpus = False
                self.grid[new_x][new_y].wumpus = True
                new_wumpus_positions.append((new_x, new_y))
                
                if (new_x, new_y) != (wx, wy):
                    print(f">>> Wumpus moved from ({wx},{wy}) to ({new_x},{new_y})")
                
                # Check collision with agent
                if (new_x, new_y) == agent.position:
                    print(f">>> Wumpus moved into agent's position! Agent killed!")
                    agent.done = True
                    self.score -= 1000
            else:
                # No valid moves, stay in place
                new_wumpus_positions.append((wx, wy))
        
        # Update wumpus positions
        self.wumpus_positions = new_wumpus_positions