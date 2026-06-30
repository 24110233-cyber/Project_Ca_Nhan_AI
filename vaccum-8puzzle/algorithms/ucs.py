from __future__ import annotations

import heapq
from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


def _frontier_nodes(frontier: List[Tuple[int, int, SearchNode]]) -> List[SearchNode]:
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
    Uniform-Cost Search (Dijkstra với cost cạnh = 1).

    - Frontier là Priority Queue theo g(n) nhỏ nhất.
    - Goal được kiểm tra khi node bị pop khỏi Frontier.
    """
    _ = max_depth  # UCS không dùng depth limit trong bản này.

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    counter = 0

    frontier: List[Tuple[int, int, SearchNode]] = [(0, counter, root)]
    best_cost = {start_state: 0}
    reached_set = {start_state}
    reached_order = [start_state]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    while frontier and expansions < max_expansions:
        cost, _, node = heapq.heappop(frontier)
        expansions += 1

        current_best = best_cost.get(node.state)
        if current_best is not None and cost > current_best:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=_frontier_nodes(frontier),
                reached_order=reached_order,
                formatter=formatter,
                note=f"Skipped stale node (g={cost}, best_g={current_best})",
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
                note=f"GOAL popped from Priority Queue (g={cost})",
            )
            path = node.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found by UCS.",
                expansions,
            )

        for action, child_state in get_successors(node.state):
            child_cost = cost + 1
            known_cost = best_cost.get(child_state)
            if known_cost is not None and child_cost >= known_cost:
                continue

            child = SearchNode(
                state=child_state,
                parent=node,
                action=action,
                depth=node.depth + 1,
            )
            best_cost[child_state] = child_cost

            counter += 1
            heapq.heappush(frontier, (child_cost, counter, child))

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
            note=f"Expanded by UCS (g={cost})",
        )

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}.",
        expansions,
    )

