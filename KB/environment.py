import random

class Cell:
    def __init__(self):
        self.pit = False
        self.wumpus = False
        self.gold = False

class Environment:
    def __init__(self, size=4, num_wumpus=2, pit_prob=0.2):
        self.size = size
        self.grid = [[Cell() for _ in range(size)] for _ in range(size)]
        self.agent_position = (0, 0)
        self.agent_direction = "E"  
        self.arrow_used = False
        self.scream = False
        self.gold_found = False
        self.place_pit_and_wumpus(num_wumpus, pit_prob)
        self.place_gold()

    def place_pit_and_wumpus(self, num_wumpus, pit_prob):
        candidates = [(x, y) for x in range(self.size) for y in range(self.size) if (x, y) != (0, 0)]
        random.shuffle(candidates)

        for _ in range(num_wumpus):
            if candidates:
                x, y = candidates.pop()
                self.grid[x][y].wumpus = True

        for x in range(self.size):
            for y in range(self.size):
                if (x, y) != (0, 0) and not self.grid[x][y].wumpus and random.random() < pit_prob:
                    self.grid[x][y].pit = True

    def place_gold(self):
        while True:
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if not self.grid[x][y].pit and not self.grid[x][y].wumpus and x != 0 and y != 0:
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

        if action == "grab":
            if self.grid[x][y].gold:
                self.grid[x][y].gold = False
                agent.has_gold = True

        elif action == "climb":
            if (x, y) == (0, 0) and agent.has_gold:
                agent.done = True


        elif action == "move":
            dx, dy = self._get_delta(agent.direction)
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                agent.position = (nx, ny)
                agent.bump = False
                self.check_dead(agent)
            else:
                agent.bump = True 


        elif action == "turn_left":
            agent.direction = self._turn_left(agent.direction)

        elif action == "turn_right":
            agent.direction = self._turn_right(agent.direction)

        elif action == "shoot":
            if self.arrow_used:
                return
            self.arrow_used = True
            dx, dy = self._get_delta(agent.direction)
            tx, ty = x + dx, y + dy
            while 0 <= tx < self.size and 0 <= ty < self.size:
                if self.grid[tx][ty].wumpus:
                    self.grid[tx][ty].wumpus = False
                    self.scream = True
                    break
                tx += dx
                ty += dy

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


