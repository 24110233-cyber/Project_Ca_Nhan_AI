from __future__ import annotations

import random
from typing import List, Sequence, Tuple


Position = Tuple[int, int]
VacuumGrid = Tuple[Tuple[int, ...], ...]
VacuumState = Tuple[Position, VacuumGrid]


class VacuumProblem:
    """
    Vacuum World 3x3.

    Quy ước grid:
    - -1 = vật cản
    -  0 = sạch
    -  1 = bụi
    """

    ROWS = 3
    COLS = 3

    START_POS: Position = (0, 0)
    START_GRID: VacuumGrid = (
        (0, 0, 1),
        (1, -1, 1),
        (0, 1, 0),
    )

    ACTIONS: Sequence[Tuple[str, int, int]] = (
        ("UP", -1, 0),
        ("DOWN", 1, 0),
        ("LEFT", 0, -1),
        ("RIGHT", 0, 1),
    )

    @classmethod
    def start_state(cls) -> VacuumState:
        return cls.START_POS, cls.START_GRID

    @classmethod
    def is_goal(cls, state: object) -> bool:
        _, grid = state  # type: ignore[misc]
        return all(cell != 1 for row in grid for cell in row)

    @classmethod
    def dirty_count(cls, state: VacuumState) -> int:
        _, grid = state
        return sum(cell == 1 for row in grid for cell in row)

    @classmethod
    def obstacle_count(cls, state: VacuumState) -> int:
        _, grid = state
        return sum(cell == -1 for row in grid for cell in row)

    @classmethod
    def successors(cls, state: object) -> List[Tuple[str, object]]:
        (row, col), grid = state  # type: ignore[misc]
        result: List[Tuple[str, object]] = []

        # Nếu ô hiện tại có bụi thì cho phép hành động hút bụi.
        if grid[row][col] == 1:
            new_grid = [list(item) for item in grid]
            new_grid[row][col] = 0
            result.append(("SUCK", ((row, col), tuple(tuple(item) for item in new_grid))))

        for action, dr, dc in cls.ACTIONS:
            nr, nc = row + dr, col + dc

            if 0 <= nr < cls.ROWS and 0 <= nc < cls.COLS and grid[nr][nc] != -1:
                result.append((action, ((nr, nc), grid)))

        return result

    @classmethod
    def manual_action(cls, state: VacuumState, action: str) -> VacuumState:
        (row, col), grid = state

        if action == "SUCK":
            if grid[row][col] != 1:
                return state

            new_grid = [list(item) for item in grid]
            new_grid[row][col] = 0
            return (row, col), tuple(tuple(item) for item in new_grid)

        for candidate_action, dr, dc in cls.ACTIONS:
            if action != candidate_action:
                continue

            nr, nc = row + dr, col + dc

            if 0 <= nr < cls.ROWS and 0 <= nc < cls.COLS and grid[nr][nc] != -1:
                return (nr, nc), grid

        return state

    @classmethod
    def click_action(cls, state: VacuumState, row: int, col: int) -> VacuumState:
        (robot_row, robot_col), grid = state

        if grid[row][col] == -1:
            return state

        if (row, col) == (robot_row, robot_col):
            return cls.manual_action(state, "SUCK")

        if abs(row - robot_row) + abs(col - robot_col) == 1:
            return (row, col), grid

        return state

    @classmethod
    def random_state(cls) -> VacuumState:
        while True:
            grid: List[List[int]] = []

            for _ in range(cls.ROWS):
                row: List[int] = []

                for _ in range(cls.COLS):
                    roll = random.random()

                    if roll < 0.12:
                        row.append(-1)
                    elif roll < 0.58:
                        row.append(1)
                    else:
                        row.append(0)

                grid.append(row)

            free_cells = [
                (r, c)
                for r in range(cls.ROWS)
                for c in range(cls.COLS)
                if grid[r][c] != -1
            ]

            dirty_cells = [
                (r, c)
                for r in range(cls.ROWS)
                for c in range(cls.COLS)
                if grid[r][c] == 1
            ]

            if not free_cells or not dirty_cells:
                continue

            robot_pos = random.choice(free_cells)
            return robot_pos, tuple(tuple(row) for row in grid)

    @classmethod
    def format_state(cls, state: object) -> str:
        (robot_row, robot_col), grid = state  # type: ignore[misc]

        rows = []
        for row in range(cls.ROWS):
            values = []

            for col in range(cls.COLS):
                if (row, col) == (robot_row, robot_col):
                    values.append("R")
                elif grid[row][col] == -1:
                    values.append("X")
                elif grid[row][col] == 1:
                    values.append("1")
                else:
                    values.append("0")

            rows.append("".join(values))

        return "/".join(rows)
