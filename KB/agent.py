from knowledge_base import DynamicKB, breeze_rule, stench_rule
from planner import astar
import random

class RandomWumpusAgent:
    def __init__(self, env):
        self.env = env
        self.position = (0, 0)
        self.direction = "E"
        self.has_gold = False
        self.done = False
        self.bump = False
        self.actions = ["move", "turn_left", "turn_right", "shoot", "grab", "climb"]
        self.arrow_used = False

    def perceive(self, percepts):
        
        self.bump = percepts.get("bump", False)

    def choose_action(self):
        if self.has_gold and self.position == (0, 0):
            return "climb"
        if not self.arrow_used and random.random() < 0.1:
            self.arrow_used = True
            return "shoot"
        return random.choice(self.actions)

    def update_position_on_move(self):
        dx, dy = self._get_delta(self.direction)
        nx, ny = self.position[0] + dx, self.position[1] + dy
        if 0 <= nx < self.env.size and 0 <= ny < self.env.size:
            self.position = (nx, ny)

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

class KBWumpusAgent:
    def __init__(self, env):
        self.plan = []
        self.env = env
        self.kb = DynamicKB(size=env.size)
        self.kb.add_rule(breeze_rule)
        self.kb.add_rule(stench_rule)
        self.direction = "E"
        self.position = (0, 0)
        self.visited = set()
        self.has_gold = False
        self.done = False

    def perceive(self, percepts):
        x, y = self.position
        self.visited.add((x, y))
        self.kb.assert_fact(("visited", x, y)) 

        self.kb.assert_fact(("safe", x, y))

        if percepts["breeze"]:
            self.kb.assert_fact(("breeze", x, y))
        else:
            self.kb.assert_fact(("no_breeze", x, y))
        if percepts["glitter"]:
            self.kb.assert_fact(("gold_here", x, y))
        if percepts["stench"]:
            self.kb.assert_fact(("stench", x, y))
        else:
            self.kb.assert_fact(("no_stench", x, y))
        if percepts["scream"]:
            print("Scream")
        if percepts["bump"]:
            print(f"Bump detected at {self.position} facing {self.direction}")

            dx, dy = self._get_delta(self.direction)
            nx, ny = self.position[0] + dx, self.position[1] + dy
            if 0 <= nx < self.env.size and 0 <= ny < self.env.size:
                self.kb.add_fact(("blocked", nx, ny))

            if self.plan and self.plan[0] == (nx, ny):
                self.plan.pop(0)

        self.kb.infer()
        print("KB Facts:", self.kb.facts)
        self.bump = False

    def _get_delta(self, direction):
        return {
            "N": (0, 1),
            "E": (1, 0),
            "S": (0, -1),
            "W": (-1, 0)
        }[direction]

    def _turn_left(self, dir):
        if dir not in ["N", "E", "S", "W"]:
            print(f"Warning: Invalid direction '{dir}' during left turn. Defaulting to 'N'.")
            return "N"
        return {"N": "W", "W": "S", "S": "E", "E": "N"}[dir]

    def _turn_right(self, dir):
        if dir not in ["N", "E", "S", "W"]:
            print(f"Warning: Invalid direction '{dir}' during right turn. Defaulting to 'N'.")
            return "N"
        return {"N": "E", "E": "S", "S": "W", "W": "N"}[dir]


    def choose_action(self):
        x, y = self.position

        if not self.has_gold and ("gold_here", x, y) in self.kb.facts:
            self.has_gold = True
            return "grab"

        if self.has_gold and (x, y) != (0, 0):
            from planner import astar
            path = astar(self.position, (0, 0), self.kb, self.env.size)
            if path:
                self.plan = path

        if self.plan:
            next_move = self.plan.pop(0)
            return self.get_action_towards(next_move)

        for safe_cell in self.kb.get_safe_unvisited():
            if safe_cell != self.position:
                from planner import astar
                path = astar(self.position, safe_cell, self.kb, self.env.size)
                if path:
                    self.plan = path
                    print(f"Planning to explore: {safe_cell}, path: {path}")
                    return self.get_action_towards(self.plan.pop(0))

        if self.position == (0, 0) and self.has_gold:
            return 'climb'

        return "climb"

    def get_action_towards(self, target):
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]

        if dx == 1:
            desired_dir = 'E'
        elif dx == -1:
            desired_dir = 'W'
        elif dy == 1:
            desired_dir = 'N'
        elif dy == -1:
            desired_dir = 'S'
        else:
            return 'wait'

        if self.direction != desired_dir:
            if self._turn_left(self.direction) == desired_dir:
                return 'turn_left'
            else:
                return 'turn_right'

        return 'move'





