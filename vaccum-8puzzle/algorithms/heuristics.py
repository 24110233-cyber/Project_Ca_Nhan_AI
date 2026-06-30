from __future__ import annotations


def manhattan_if_puzzle(state: object) -> int | None:
    if not isinstance(state, tuple) or len(state) != 9:
        return None
    if not all(isinstance(value, int) for value in state):
        return None

    distance = 0
    for index, value in enumerate(state):
        if value == 0:
            continue
        target_index = value - 1
        row, col = divmod(index, 3)
        target_row, target_col = divmod(target_index, 3)
        distance += abs(row - target_row) + abs(col - target_col)

    return distance


def vacuum_score_if_vacuum(state: object) -> int | None:
    if not isinstance(state, tuple) or len(state) != 2:
        return None

    position, grid = state
    if not isinstance(position, tuple) or len(position) != 2:
        return None

    robot_row, robot_col = position
    if not isinstance(robot_row, int) or not isinstance(robot_col, int):
        return None

    if not isinstance(grid, tuple):
        return None

    dirty_positions = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, tuple):
            return None
        for col_index, cell in enumerate(row):
            if cell == 1:
                dirty_positions.append((row_index, col_index))

    if not dirty_positions:
        return 0

    nearest_dirt_distance = min(
        abs(robot_row - dirt_row) + abs(robot_col - dirt_col)
        for dirt_row, dirt_col in dirty_positions
    )

    # Weight dirt count to keep "SUCK" strongly preferable when standing on dirt.
    return len(dirty_positions) * 5 + nearest_dirt_distance


def heuristic(state: object) -> int:
    puzzle_h = manhattan_if_puzzle(state)
    if puzzle_h is not None:
        return puzzle_h

    vacuum_h = vacuum_score_if_vacuum(state)
    if vacuum_h is not None:
        return vacuum_h

    return 0
