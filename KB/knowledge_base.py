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
        for rule in self.rules:
            new_facts = rule(self.facts, self.size)
            self.facts.update(new_facts)

    def get_safe_unvisited(self):
        safe = set()
        visited = set()
        for fact in self.facts:
            if fact[0] == "safe":
                safe.add((fact[1], fact[2]))
            elif fact[0] == "visited":
                visited.add((fact[1], fact[2]))
        return list(safe - visited)


def stench_rule(facts, size):
    new_facts = set()
    for fact in facts:
        if fact[0] == "no_stench":
            x, y = fact[1], fact[2]
            
            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    new_facts.add(("no_wumpus", nx, ny))
        elif fact[0] == "stench":
            x, y = fact[1], fact[2]

            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    new_facts.add(("possible_wumpus", nx, ny))
                    new_facts.add(("stench_nearby", nx, ny))
    return new_facts

def breeze_rule(facts, size):
    new_facts = set()
    for fact in facts:
        if fact[0] == "breeze":
            x, y = fact[1], fact[2]
            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    if ("no_pit", nx, ny) not in facts:
                        new_facts.add(("possible_pit", nx, ny))
        elif fact[0] == "no_breeze":
            x, y = fact[1], fact[2]
            for dx, dy in [(0,1), (1,0), (-1,0), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    new_facts.add(("no_pit", nx, ny))
                    new_facts.add(("safe", nx, ny))
    return new_facts
