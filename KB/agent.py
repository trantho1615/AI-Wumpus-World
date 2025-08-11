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
        self.last_action_was_shoot = False

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
        self.last_action_was_shoot = False
        self.glitter_detected_at = None

    def perceive(self, percepts):
        x, y = self.position
        self.visited.add((x, y))
        self.kb.assert_fact(("visited", x, y))
        self.kb.assert_fact(("safe", x, y))

        if percepts["breeze"]:
            self.kb.assert_fact(("breeze", x, y))
        else:
            self.kb.assert_fact(("no_breeze", x, y))

        if percepts["glitter"] and not self.has_gold:
            self.glitter_detected_at = self.position

        if percepts["stench"]:
            self.kb.assert_fact(("stench", x, y))
        else:
            self.kb.assert_fact(("no_stench", x, y))

        if ("no_breeze", x, y) in self.kb.facts and ("no_stench", x, y) in self.kb.facts:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.env.size and 0 <= ny < self.env.size:
                    if ("safe", nx, ny) not in self.kb.facts:
                        self.kb.assert_fact(("safe", nx, ny))

        dx, dy = self._get_delta(self.direction)
        tx, ty = self.position[0] + dx, self.position[1] + dy

        if self.last_action_was_shoot and percepts.get("scream", False):
            print(f"Scream heard! Eliminating Wumpus along ({dx}, {dy})")
            while 0 <= tx < self.env.size and 0 <= ty < self.env.size:
                self.kb.assert_fact(("no_wumpus", tx, ty))
                self.kb.assert_fact(("safe", tx, ty))
                self.kb.facts.discard(("possible_wumpus", tx, ty))
                tx += dx
                ty += dy
            self.kb.facts = {fact for fact in self.kb.facts if fact[0] != "possible_wumpus"}


        elif self.last_action_was_shoot and self.env.arrow_used:
            print("Missed shot — sweeping and marking as safe from Wumpus.")
            while 0 <= tx < self.env.size and 0 <= ty < self.env.size:
                print(f"Marking ({tx},{ty}) as safe from Wumpus.")
                self.kb.assert_fact(("no_wumpus", tx, ty))
                self.kb.assert_fact(("safe", tx, ty))
                self.kb.facts = {f for f in self.kb.facts if f != ("possible_wumpus", tx, ty)}
                tx += dx
                ty += dy

        if percepts["bump"]:
            print(f"Bump detected at {self.position} facing {self.direction}")
            nx, ny = self.position[0] + dx, self.position[1] + dy
            if 0 <= nx < self.env.size and 0 <= ny < self.env.size:
                self.kb.add_fact(("blocked", nx, ny))
            if self.plan and self.plan[0] == (nx, ny):
                self.plan.pop(0)

        if ("gold_here", x, y) in self.kb.facts and not self.has_gold:
            print(f"Gold detected at {self.position}, grabbing it.")
            self.has_gold = True
            self.plan = []

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
        self.last_action_was_shoot = False

        x, y = self.position

        percepts = self.env.get_percepts(self.position)

        if percepts.get("glitter", False) and not self.has_gold:
            print(f"Gold detected at {self.position}, grabbing it and heading home.")
            self.has_gold = True

            home_path = self._reverse_path_home()  
            actions_home = self._path_to_actions(home_path) if home_path else []

            self.plan = ["grab"] + actions_home + ["climb"]

        if self.has_gold and self.plan:
            return self.plan.pop(0)

        if self.has_gold and self.position == (0, 0):
            return "climb"

        if self.glitter_detected_at and not self.has_gold:
            if self.position != self.glitter_detected_at:
                path = astar(self.position, self.glitter_detected_at, self.kb, self.env.size)
                if path:
                    self.plan = path
                    return self.get_action_towards(self.plan.pop(0))
            else:
                return "grab"

        if percepts.get("stench", False) and not self.env.arrow_used:
            dx, dy = self._get_delta(self.direction)
            tx, ty = self.position[0] + dx, self.position[1] + dy
            if 0 <= tx < self.env.size and 0 <= ty < self.env.size:
                if ("possible_wumpus", tx, ty) in self.kb.facts:
                    print(f"Decided to shoot at ({tx}, {ty}) due to stench!")
                    self.last_action_was_shoot = True
                    return "shoot"

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = self.position[0] + dx, self.position[1] + dy
            if (0 <= nx < self.env.size and 0 <= ny < self.env.size):
                if ("safe", nx, ny) in self.kb.facts and (nx, ny) not in self.visited:
                    print(f"Moving to adjacent unvisited safe cell: ({nx}, {ny})")
                    return self.get_action_towards((nx, ny))

        if self.plan:
            next_move = self.plan[0]

            if next_move == "climb" and self.position != (0, 0):
                self.plan = self._reverse_path_home() + ["climb"]
                next_move = self.plan[0]

            action = self.get_action_towards(next_move)
            if action:
                self.plan.pop(0)
                return action

        for safe_cell in self.kb.get_safe_unvisited():
            if safe_cell != self.position and safe_cell not in self.visited:
                path = astar(self.position, safe_cell, self.kb, self.env.size)
                if path:
                    self.plan = path
                    print(f"Planning to explore: {safe_cell}, path: {path}")
                    return self.get_action_towards(self.plan.pop(0))

        for cell in sorted(self.kb.get_safe_unvisited()):
            if cell not in self.visited:
                path = astar(self.position, cell, self.kb, self.env.size)
                if path:
                    self.plan = path
                    print(f"[Fallback] Planning to explore: {cell}, path: {path}")
                    return self.get_action_towards(self.plan.pop(0))

        unknown_cells = [
            (nx, ny) for nx in range(self.env.size) for ny in range(self.env.size)
            if (nx, ny) not in self.visited
               and ("possible_pit", nx, ny) not in self.kb.facts
               and ("pit", nx, ny) not in self.kb.facts
               and ("possible_wumpus", nx, ny) not in self.kb.facts
        ]

        if unknown_cells:
            
            target = min(unknown_cells, key=lambda c: abs(c[0] - self.position[0]) + abs(c[1] - self.position[1]))
            path = astar(self.position, target, self.kb, self.env.size, allow_unknown=True)
            if path:
                self.plan = path
                return self.get_action_towards(self.plan.pop(0))

        return "wait" 


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

    def _reverse_path_home(self):
        path = astar(self.position, (0, 0), self.kb, self.env.size, allow_unknown=False)
        return path if path else []

    def _path_to_actions(self, path):
        """
        Convert a sequence of positions into a list of turn/move actions.
        """
        actions = []
        current_direction = self.direction
        current_position = self.position

        for next_pos in path:
            dx = next_pos[0] - current_position[0]
            dy = next_pos[1] - current_position[1]

            # Figure out which direction we need to face
            if dx == 1:
                target_dir = "E"
            elif dx == -1:
                target_dir = "W"
            elif dy == 1:
                target_dir = "N"
            elif dy == -1:
                target_dir = "S"
            else:
                continue  # skip invalid

            # Rotate until facing target_dir
            while current_direction != target_dir:
                actions.append("turn_right")
                current_direction = self._turn_right_direction(current_direction)

            # Move forward
            actions.append("move")
            current_position = next_pos

        return actions

    def _turn_right_direction(self, dir):
        order = ["N", "E", "S", "W"]
        return order[(order.index(dir) + 1) % 4]