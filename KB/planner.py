import heapq

MOVE_COST = -1
TURN_COST = -1
GRAB_REWARD = 10
SHOOT_COST = -10
DEATH_COST = -1000
CLIMB_REWARD_WITH_GOLD = 1000

def heuristic(state, goal, kb):
    x, y = state
    gx, gy = goal
    base = abs(x - gx) + abs(y - gy)
    penalty = 0
    for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
        nx, ny = x + dx, y + dy
        if ("possible_pit", nx, ny) in kb.facts:
            penalty += 5  
    return base + penalty


def get_direction(from_pos, to_pos):
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]
    if dx == 1:
        return 'E'
    elif dx == -1:
        return 'W'
    elif dy == 1:
        return 'N'
    elif dy == -1:
        return 'S'
    return None


def direction_cost(prev_dir, new_dir):
    if prev_dir is None or prev_dir == new_dir:
        return 0
    return TURN_COST


def astar(start, goal, kb, size=4):
    
    frontier = [(0, start, None)]  # heap: (priority, position, current_direction)
    came_from = {}
    cost_so_far = {start: 0}
    dir_so_far = {start: None}

    while frontier:
        _, current, current_dir = heapq.heappop(frontier)

        if current == goal:
            break

        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = current[0] + dx, current[1] + dy
            next_pos = (nx, ny)

            if 0 <= nx < size and 0 <= ny < size:
                if ("safe", nx, ny) not in kb.facts:
                    continue

                new_dir = get_direction(current, next_pos)
                move_cost = MOVE_COST + direction_cost(current_dir, new_dir)
                new_cost = cost_so_far[current] + move_cost

                if next_pos not in cost_so_far or new_cost > cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = -new_cost + heuristic(next_pos, goal, kb)
                    heapq.heappush(frontier, (priority, next_pos, new_dir))
                    came_from[next_pos] = current
                    dir_so_far[next_pos] = new_dir

    if goal not in came_from:
        return None  
        

    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path
