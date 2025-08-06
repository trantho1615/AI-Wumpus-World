import heapq

def heuristic(state, goal, kb):
    x, y = state
    gx, gy = goal
    base = abs(x - gx) + abs(y - gy)
    penalty = 0
    for dx, dy in [(0,1),(1,0),(-1,0),(0,-1)]:
        nx, ny = x+dx, y+dy
        if ("possible_pit", nx, ny) in kb.facts:
            penalty += 5
    return base + penalty

def astar(start, goal, kb, size=4):
    frontier = [(0, start)]
    came_from = {}
    cost_so_far = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break

        for dx, dy in [(0,1),(1,0),(-1,0),(0,-1)]:
            nx, ny = current[0]+dx, current[1]+dy

            if 0 <= nx < size and 0 <= ny < size:
                if ("safe", nx, ny) not in kb.facts:
                    continue

                new_cost = cost_so_far[current] + 1
                if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                    cost_so_far[(nx, ny)] = new_cost
                    priority = new_cost + heuristic((nx, ny), goal, kb)
                    heapq.heappush(frontier, (priority, (nx, ny)))
                    came_from[(nx, ny)] = current

    if goal not in came_from:
        return None

    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path


