from __future__ import annotations

import heapq
from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, append_trace


def _manhattan_if_puzzle(state: object) -> int | None:
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


def _dirty_cells_if_vacuum(state: object) -> int | None:
    if not isinstance(state, tuple) or len(state) != 2:
        return None

    _, grid = state
    if not isinstance(grid, tuple):
        return None

    dirty = 0
    for row in grid:
        if not isinstance(row, tuple):
            return None
        for cell in row:
            if cell == 1:
                dirty += 1

    return dirty


def _heuristic(state: object) -> int:
    puzzle_h = _manhattan_if_puzzle(state)
    if puzzle_h is not None:
        return puzzle_h

    vacuum_h = _dirty_cells_if_vacuum(state)
    if vacuum_h is not None:
        return vacuum_h

    return 0


def _frontier_nodes(frontier: List[Tuple[int, int, SearchNode]]) -> List[SearchNode]:
    return [entry[2] for entry in sorted(frontier)]


def search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    """
    Greedy Best-First Search.

    Theo giả mã:
    - FRONTIER ưu tiên node có h(n) nhỏ nhất.
    - REACHED chứa các state đã pop ra để mở rộng.
    - Nếu state đã có trong FRONTIER hoặc REACHED thì bỏ qua.
    """
    _ = max_depth  # Greedy không dùng depth limit.

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    counter = 0

    frontier: List[Tuple[int, int, SearchNode]] = [(_heuristic(start_state), counter, root)]
    frontier_states = {start_state}

    reached_set = set()
    reached_order: List[object] = []

    trace = []
    trace_by_state = {}
    expansions = 0

    while frontier and expansions < max_expansions:
        h_score, _, node = heapq.heappop(frontier)
        frontier_states.discard(node.state)
        expansions += 1

        if is_goal(node.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=_frontier_nodes(frontier),
                reached_order=reached_order,
                formatter=formatter,
                note=f"GOAL popped from Frontier (h={h_score})",
            )
            return SearchResult(
                True,
                node.path(),
                trace,
                trace_by_state,
                "Goal found by Greedy Best-First Search.",
                expansions,
            )

        reached_set.add(node.state)
        reached_order.append(node.state)

        for action, child_state in get_successors(node.state):
            if child_state in frontier_states or child_state in reached_set:
                continue

            child = SearchNode(
                state=child_state,
                parent=node,
                action=action,
                depth=node.depth + 1,
            )
            child_h = _heuristic(child_state)

            counter += 1
            heapq.heappush(frontier, (child_h, counter, child))
            frontier_states.add(child_state)

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=_frontier_nodes(frontier),
            reached_order=reached_order,
            formatter=formatter,
            note=f"Expanded by Greedy (h={h_score}); skipped duplicates in Frontier/Reached",
        )

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}.",
        expansions,
    )

