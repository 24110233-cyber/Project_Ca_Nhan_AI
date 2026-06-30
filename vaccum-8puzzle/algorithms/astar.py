from __future__ import annotations

import heapq
from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


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


def _frontier_nodes(frontier: List[Tuple[int, int, SearchNode, int]]) -> List[SearchNode]:
    return [entry[2] for entry in sorted(frontier)]


def _align_trace_with_path(
    path: List[SearchNode],
    trace: List[TraceEntry],
    trace_by_state: dict,
) -> dict:
    if not path:
        return trace_by_state

    needed_states = {node.state for node in path}
    latest_for_path = {}

    for entry in reversed(trace):
        if entry.state in needed_states and entry.state not in latest_for_path:
            latest_for_path[entry.state] = entry
            if len(latest_for_path) == len(needed_states):
                break

    merged = dict(trace_by_state)
    merged.update(latest_for_path)
    return merged


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
    A* graph-search cho 8-Puzzle và Vacuum.

    - Ưu tiên node có f(n) = g(n) + h(n) nhỏ nhất.
    - g(n): số bước đi từ start (mỗi action cost = 1).
    - h(n):
      - 8-Puzzle: Manhattan distance.
      - Vacuum: số ô bụi còn lại.
      - Trường hợp khác: 0 (thoái hóa về UCS).
    """
    _ = max_depth  # A* không dùng depth limit trong bản này.

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    start_h = _heuristic(start_state)

    counter = 0
    frontier: List[Tuple[int, int, SearchNode, int]] = [(start_h, counter, root, 0)]
    best_g = {start_state: 0}
    reached_set = {start_state}
    reached_order = [start_state]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    while frontier and expansions < max_expansions:
        f_score, _, node, g_score = heapq.heappop(frontier)
        expansions += 1

        current_best_g = best_g.get(node.state)
        if current_best_g is not None and g_score > current_best_g:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=_frontier_nodes(frontier),
                reached_order=reached_order,
                formatter=formatter,
                note=f"Skipped stale node (f={f_score}, g={g_score}, best_g={current_best_g})",
            )
            continue

        if is_goal(node.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=_frontier_nodes(frontier),
                reached_order=reached_order,
                formatter=formatter,
                note=f"GOAL popped from Priority Queue (f={f_score}, g={g_score}, h={f_score - g_score})",
            )
            path = node.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found by A*.",
                expansions,
            )

        for action, child_state in get_successors(node.state):
            child_g = g_score + 1
            known_g = best_g.get(child_state)
            if known_g is not None and child_g >= known_g:
                continue

            child = SearchNode(
                state=child_state,
                parent=node,
                action=action,
                depth=node.depth + 1,
            )
            best_g[child_state] = child_g
            child_h = _heuristic(child_state)

            counter += 1
            heapq.heappush(frontier, (child_g + child_h, counter, child, child_g))

            if child_state not in reached_set:
                reached_set.add(child_state)
                reached_order.append(child_state)

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=_frontier_nodes(frontier),
            reached_order=reached_order,
            formatter=formatter,
            note=f"Expanded by A* (f={f_score}, g={g_score}, h={f_score - g_score})",
        )

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}.",
        expansions,
    )

