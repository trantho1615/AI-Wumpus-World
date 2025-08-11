import heapq
from environment import MOVE_COST  

# Penalty constants
UNKNOWN_PENALTY = 5
DANGER_PENALTY = 50

def heuristic(a, b, kb):
    # Khoảng cách Manhattan
    (x1, y1) = a
    (x2, y2) = b
    h = abs(x1 - x2) + abs(y1 - y2)

    # Penalty heuristic nếu ô này có nguy cơ pit
    if ("possible_pit", x1, y1) in kb.facts or ("possible_wumpus", x1, y1) in kb.facts:
        h += DANGER_PENALTY // 10  # chỉ tăng nhẹ heuristic, penalty chính cộng vào cost

    return h

def astar(start, goal, kb, map_size, allow_unknown=True):
    """
    A* tìm đường từ start đến goal.
    - allow_unknown=False: chỉ đi ô safe
    - allow_unknown=True: có thể đi qua ô chưa biết (penalty)
    """
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while frontier:
        current_priority, current = heapq.heappop(frontier)

        if current == goal:
            break

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_pos = (current[0] + dx, current[1] + dy)

            # 1. Check biên bản đồ
            if not (0 <= next_pos[0] < map_size and 0 <= next_pos[1] < map_size):
                continue

            # 2. Xác định cost extra dựa trên trạng thái KB
            if ("safe", next_pos[0], next_pos[1]) in kb.facts:
                extra_cost = 0
            elif allow_unknown and not any(f[0] in ("possible_pit", "possible_wumpus") and f[1] == next_pos[0] and f[2] == next_pos[1] for f in kb.facts):
                extra_cost = UNKNOWN_PENALTY
            else:
                # Nếu là dangerous hoặc unknown khi không cho phép, bỏ qua
                if not allow_unknown:
                    continue
                # Dangerous => penalty rất cao
                extra_cost = DANGER_PENALTY

            # 3. Tính cost mới
            new_cost = cost_so_far[current] + MOVE_COST + extra_cost

            # 4. Cập nhật nếu tìm thấy đường rẻ hơn
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + heuristic(next_pos, goal, kb)
                heapq.heappush(frontier, (priority, next_pos))
                came_from[next_pos] = current

    # Truy ngược path
    if goal not in came_from:
        return None  # Không tìm được đường

    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path