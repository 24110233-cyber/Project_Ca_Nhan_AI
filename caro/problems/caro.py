from __future__ import annotations

import random
from typing import List, Tuple


CaroBoard = Tuple[int, ...]
CaroState = Tuple[CaroBoard, int]


class CaroProblem:
    """
    Caro/Gomoku board used by adversarial search algorithms.

    State = (board, player_to_move)
    - board: flat tuple with SIZE * SIZE cells
    - 0: empty, 1: X, 2: O
    - X is the human/default first player, O is the AI/default second player
    """

    SIZE = 7
    WIN_LENGTH = 5

    EMPTY = 0
    HUMAN = 1
    AI = 2

    START: CaroState = (tuple([EMPTY] * (SIZE * SIZE)), HUMAN)
    DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))
    SYMBOLS = {
        EMPTY: ".",
        HUMAN: "X",
        AI: "O",
    }

    @classmethod
    def start_state(cls) -> CaroState:
        return cls.START

    @classmethod
    def is_caro_state(cls, state: object) -> bool:
        if not isinstance(state, tuple) or len(state) != 2:
            return False
        board, player = state
        return (
            isinstance(board, tuple)
            and len(board) == cls.SIZE * cls.SIZE
            and all(cell in (cls.EMPTY, cls.HUMAN, cls.AI) for cell in board)
            and player in (cls.HUMAN, cls.AI)
        )

    @classmethod
    def opponent(cls, player: int) -> int:
        return cls.AI if player == cls.HUMAN else cls.HUMAN

    @classmethod
    def player_label(cls, player: int) -> str:
        return cls.SYMBOLS.get(player, "?")

    @classmethod
    def index(cls, row: int, col: int) -> int:
        return row * cls.SIZE + col

    @classmethod
    def in_bounds(cls, row: int, col: int) -> bool:
        return 0 <= row < cls.SIZE and 0 <= col < cls.SIZE

    @classmethod
    def current_player(cls, state: CaroState) -> int:
        return state[1]

    @classmethod
    def board(cls, state: CaroState) -> CaroBoard:
        return state[0]

    @classmethod
    def is_goal(cls, state: object) -> bool:
        if not cls.is_caro_state(state):
            return False
        caro_state = state  # type: ignore[assignment]
        return cls.winner(caro_state) != cls.EMPTY or cls.is_draw(caro_state)

    @classmethod
    def is_draw(cls, state: CaroState) -> bool:
        return cls.winner(state) == cls.EMPTY and all(cell != cls.EMPTY for cell in state[0])

    @classmethod
    def winner(cls, state: CaroState) -> int:
        board = state[0]
        for row in range(cls.SIZE):
            for col in range(cls.SIZE):
                player = board[cls.index(row, col)]
                if player == cls.EMPTY:
                    continue
                for dr, dc in cls.DIRECTIONS:
                    if cls._has_line_from(board, row, col, dr, dc, player):
                        return player
        return cls.EMPTY

    @classmethod
    def _has_line_from(
        cls,
        board: CaroBoard,
        row: int,
        col: int,
        dr: int,
        dc: int,
        player: int,
    ) -> bool:
        end_row = row + (cls.WIN_LENGTH - 1) * dr
        end_col = col + (cls.WIN_LENGTH - 1) * dc
        if not cls.in_bounds(end_row, end_col):
            return False
        for step in range(cls.WIN_LENGTH):
            rr = row + step * dr
            cc = col + step * dc
            if board[cls.index(rr, cc)] != player:
                return False
        return True

    @classmethod
    def successors(cls, state: object) -> List[Tuple[str, object]]:
        if not cls.is_caro_state(state):
            return []
        caro_state = state  # type: ignore[assignment]
        if cls.is_goal(caro_state):
            return []

        board, player = caro_state
        result: List[Tuple[str, object]] = []
        for row, col in cls.candidate_moves(board, player, limit=12):
            result.append((cls.action_label(player, row, col), cls.apply_move(caro_state, row, col)))
        return result

    @classmethod
    def apply_move(cls, state: CaroState, row: int, col: int) -> CaroState:
        board, player = state
        if cls.is_goal(state) or not cls.in_bounds(row, col):
            return state
        index = cls.index(row, col)
        if board[index] != cls.EMPTY:
            return state

        new_board = list(board)
        new_board[index] = player
        return tuple(new_board), cls.opponent(player)

    @classmethod
    def click_move(cls, state: CaroState, row: int, col: int) -> CaroState:
        return cls.apply_move(state, row, col)

    @classmethod
    def candidate_moves(
        cls,
        board: CaroBoard,
        player: int,
        *,
        limit: int = 12,
        radius: int = 2,
    ) -> List[Tuple[int, int]]:
        occupied = [
            (row, col)
            for row in range(cls.SIZE)
            for col in range(cls.SIZE)
            if board[cls.index(row, col)] != cls.EMPTY
        ]

        if not occupied:
            center = cls.SIZE // 2
            return [(center, center)]

        candidates = set()
        for row, col in occupied:
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    rr = row + dr
                    cc = col + dc
                    if cls.in_bounds(rr, cc) and board[cls.index(rr, cc)] == cls.EMPTY:
                        candidates.add((rr, cc))

        scored = [
            (cls._move_priority(board, row, col, player), row, col)
            for row, col in candidates
        ]
        center = cls.SIZE // 2
        scored.sort(key=lambda item: (-item[0], abs(item[1] - center) + abs(item[2] - center), item[1], item[2]))
        return [(row, col) for _, row, col in scored[:limit]]

    @classmethod
    def _move_priority(cls, board: CaroBoard, row: int, col: int, player: int) -> int:
        opponent = cls.opponent(player)
        player_line = cls._best_line_after_move(board, row, col, player)
        opponent_line = cls._best_line_after_move(board, row, col, opponent)
        center = cls.SIZE // 2
        center_bonus = (cls.SIZE - (abs(row - center) + abs(col - center))) * 3

        if player_line >= cls.WIN_LENGTH:
            return 1_000_000 + center_bonus
        if opponent_line >= cls.WIN_LENGTH:
            return 900_000 + center_bonus
        return player_line * 10_000 + opponent_line * 8_000 + center_bonus

    @classmethod
    def _best_line_after_move(cls, board: CaroBoard, row: int, col: int, player: int) -> int:
        best = 1
        for dr, dc in cls.DIRECTIONS:
            count = 1
            count += cls._count_direction(board, row, col, dr, dc, player)
            count += cls._count_direction(board, row, col, -dr, -dc, player)
            best = max(best, count)
        return best

    @classmethod
    def _count_direction(
        cls,
        board: CaroBoard,
        row: int,
        col: int,
        dr: int,
        dc: int,
        player: int,
    ) -> int:
        count = 0
        rr = row + dr
        cc = col + dc
        while cls.in_bounds(rr, cc) and board[cls.index(rr, cc)] == player:
            count += 1
            rr += dr
            cc += dc
        return count

    @classmethod
    def evaluate(cls, state: CaroState, perspective: int = AI) -> int:
        winner = cls.winner(state)
        if winner == perspective:
            return 1_000_000
        if winner == cls.opponent(perspective):
            return -1_000_000
        if cls.is_draw(state):
            return 0

        board, turn = state
        score = cls._line_score(board, perspective) - cls._line_score(board, cls.opponent(perspective))
        if turn == perspective:
            score += 25
        return score

    @classmethod
    def _line_score(cls, board: CaroBoard, player: int) -> int:
        opponent = cls.opponent(player)
        score = 0
        weights = {1: 10, 2: 120, 3: 1_500, 4: 25_000, 5: 1_000_000}

        for row in range(cls.SIZE):
            for col in range(cls.SIZE):
                for dr, dc in cls.DIRECTIONS:
                    end_row = row + (cls.WIN_LENGTH - 1) * dr
                    end_col = col + (cls.WIN_LENGTH - 1) * dc
                    if not cls.in_bounds(end_row, end_col):
                        continue

                    player_count = 0
                    opponent_count = 0
                    for step in range(cls.WIN_LENGTH):
                        rr = row + step * dr
                        cc = col + step * dc
                        value = board[cls.index(rr, cc)]
                        if value == player:
                            player_count += 1
                        elif value == opponent:
                            opponent_count += 1

                    if player_count and opponent_count == 0:
                        score += weights[player_count]

        return score

    @classmethod
    def random_state(cls, move_count: int = 7) -> CaroState:
        state = cls.start_state()
        moves = random.randint(4, max(4, move_count))

        for _ in range(moves):
            board, player = state
            candidates = cls.candidate_moves(board, player, limit=16)
            if not candidates:
                break

            row, col = random.choice(candidates[: min(8, len(candidates))])
            next_state = cls.apply_move(state, row, col)
            if cls.winner(next_state) != cls.EMPTY:
                break
            state = next_state

        return state

    @classmethod
    def action_label(cls, player: int, row: int, col: int) -> str:
        col_label = chr(ord("A") + col)
        return f"{cls.player_label(player)} {col_label}{row + 1}"

    @classmethod
    def format_state(cls, state: object) -> str:
        if not cls.is_caro_state(state):
            return "<invalid-caro-state>"
        board, player = state  # type: ignore[misc]
        rows = []
        for row in range(cls.SIZE):
            values = []
            for col in range(cls.SIZE):
                values.append(cls.SYMBOLS[board[cls.index(row, col)]])
            rows.append("".join(values))
        return "/".join(rows) + f" turn={cls.player_label(player)}"
