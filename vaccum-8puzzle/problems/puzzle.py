from __future__ import annotations

import random
from typing import List, Sequence, Tuple


PuzzleState = Tuple[int, ...]


class PuzzleProblem:
    """
    8-Puzzle.

    Quy ước:
    - 0 là ô trống.
    - Goal là:
        1 2 3
        4 5 6
        7 8 _
    """

    SIZE = 3
    GOAL: PuzzleState = (1, 2, 3, 4, 5, 6, 7, 8, 0)
    START: PuzzleState = (1, 5, 2, 7, 0, 3, 8, 4, 6)

    ACTIONS: Sequence[Tuple[str, int, int]] = (
        ("UP", -1, 0),
        ("DOWN", 1, 0),
        ("LEFT", 0, -1),
        ("RIGHT", 0, 1),
    )

    @classmethod
    def is_goal(cls, state: object) -> bool:
        return state == cls.GOAL

    @classmethod
    def successors(cls, state: object) -> List[Tuple[str, object]]:
        puzzle_state = state  # type: ignore[assignment]
        zero_index = puzzle_state.index(0)
        row, col = divmod(zero_index, cls.SIZE)

        result: List[Tuple[str, object]] = []

        for action, dr, dc in cls.ACTIONS:
            nr, nc = row + dr, col + dc

            if 0 <= nr < cls.SIZE and 0 <= nc < cls.SIZE:
                next_index = nr * cls.SIZE + nc
                new_state = list(puzzle_state)
                new_state[zero_index], new_state[next_index] = new_state[next_index], new_state[zero_index]
                result.append((action, tuple(new_state)))

        return result

    @classmethod
    def move_blank(cls, state: PuzzleState, action: str) -> PuzzleState:
        for candidate_action, next_state in cls.successors(state):
            if candidate_action == action:
                return next_state  # type: ignore[return-value]
        return state

    @classmethod
    def click_move(cls, state: PuzzleState, row: int, col: int) -> PuzzleState:
        zero_index = state.index(0)
        zero_row, zero_col = divmod(zero_index, cls.SIZE)

        if abs(row - zero_row) + abs(col - zero_col) != 1:
            return state

        clicked_index = row * cls.SIZE + col
        new_state = list(state)
        new_state[zero_index], new_state[clicked_index] = new_state[clicked_index], new_state[zero_index]

        return tuple(new_state)

    @classmethod
    def random_state(cls, shuffle_steps: int = 10) -> PuzzleState:
        """
        Sinh trạng thái solvable bằng cách shuffle từ GOAL.

        shuffle_steps để mặc định nhỏ nhằm tránh BFS phải mở rộng quá nhiều node.
        Nếu muốn bài khó hơn, tăng giá trị này trong code.
        """
        state = cls.GOAL
        last_action = ""
        opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}

        for _ in range(shuffle_steps):
            candidates = cls.successors(state)

            if last_action:
                candidates = [
                    (action, next_state)
                    for action, next_state in candidates
                    if action != opposite[last_action]
                ]

            action, next_state = random.choice(candidates)
            state = next_state  # type: ignore[assignment]
            last_action = action

        return state

    @classmethod
    def format_state(cls, state: object) -> str:
        values = ["_" if value == 0 else str(value) for value in state]  # type: ignore[union-attr]
        return f"{values[0]}{values[1]}{values[2]}/{values[3]}{values[4]}{values[5]}/{values[6]}{values[7]}{values[8]}"
