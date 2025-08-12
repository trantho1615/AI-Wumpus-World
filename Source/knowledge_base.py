# Dynamic Knowledge Base
class DynamicKB:
    def __init__(self, size=4):
        self.size = size
        self.facts = set()
        self.rules = []

    def assert_fact(self, fact):
        self.facts.add(fact)

    def add_rule(self, rule_fn):
        self.rules.append(rule_fn)

    def infer(self):
        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                new_facts = rule(self.facts, self.size)
                for f in new_facts:
                    if f not in self.facts:
                        self.facts.add(f)
                        changed = True

            combo_new = set()
            for x in range(self.size):
                for y in range(self.size):
                    if ("no_pit", x, y) in self.facts and ("no_wumpus", x, y) in self.facts:
                        if ("safe", x, y) not in self.facts:
                            combo_new.add(("safe", x, y))
            for f in combo_new:
                if f not in self.facts:
                    self.facts.add(f)
                    changed = True


    def get_safe_unvisited(self):
        safe_unvisited = []
        for fact in self.facts:
            if fact[0] == "safe":
                x, y = fact[1], fact[2]
                if ("visited", x, y) not in self.facts:
                    safe_unvisited.append((x, y))
        return safe_unvisited

# Stench Rule
def stench_rule(facts, size):
    new_facts = set()

    for fact in facts:
        if fact[0] == "stench":
            x, y = fact[1], fact[2]
            adj_unknown = []
            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    if ("no_pit", nx, ny) in facts and ("possible_wumpus", nx, ny) not in facts and (
                    "wumpus", nx, ny) not in facts:
                        new_facts.add(("possible_wumpus", nx, ny))
            # If only one possible Wumpus location remains, mark it as wumpus
            if len(adj_unknown) == 1:
                wx, wy = adj_unknown[0]
                new_facts.add(("wumpus", wx, wy))
        elif fact[0] == "no_stench":
            x, y = fact[1], fact[2]
            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    new_facts.add(("no_wumpus", nx, ny))
                    # Mark safe if also no pit
                    if ("no_pit", nx, ny) in facts:
                        new_facts.add(("safe", nx, ny))

    return new_facts

# Breeze Rule
def breeze_rule(facts, size):
    new_facts = set()
    possible_pit_candidates = []

    for fact in facts:
        if fact[0] == "breeze":
            x, y = fact[1], fact[2]
            adj_unknown = []
            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    if ("no_pit", nx, ny) in facts and ("possible_wumpus", nx, ny) not in facts and (
                            "wumpus", nx, ny) not in facts:
                        adj_unknown.append((nx, ny))
                        new_facts.add(("possible_pit", nx, ny))
            # If only one possible pit location remains, mark it as pit
            if len(adj_unknown) == 1:
                pit_cell = adj_unknown[0]
                new_facts.add(("pit", pit_cell[0], pit_cell[1]))
        elif fact[0] == "no_breeze":
            x, y = fact[1], fact[2]
            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    new_facts.add(("no_pit", nx, ny))
                    new_facts.add(("safe", nx, ny))
    return new_facts