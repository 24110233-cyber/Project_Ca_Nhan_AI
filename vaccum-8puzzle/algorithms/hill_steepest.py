from __future__ import annotations

from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace
from algorithms.heuristics import heuristic


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
    Steepest-Ascent Hill Climbing.

    - Danh gia toan bo neighbor.
    - Chon neighbor co heuristic thap nhat.
    - Dung khi khong con neighbor tot hon.
    """
    if max_depth is None:
        max_depth = 80

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    current = root
    current_h = heuristic(start_state)

    reached_set = {start_state}
    reached_order = [start_state]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    if is_goal(start_state):
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=root,
            frontier=[root],
            reached_order=reached_order,
            formatter=formatter,
            note="START is goal",
        )
        return SearchResult(True, root.path(), trace, trace_by_state, "Start is already goal.", expansions)

    while expansions < max_expansions:
        if current.depth >= max_depth:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[current],
                reached_order=reached_order,
                formatter=formatter,
                note=f"Stop at max_depth={max_depth} (current h={current_h})",
            )
            break

        successors = list(get_successors(current.state))
        neighbor_nodes: List[SearchNode] = []

        best_neighbor: SearchNode | None = None
        best_h = current_h

        for action, child_state in successors:
            child = SearchNode(
                state=child_state,
                parent=current,
                action=action,
                depth=current.depth + 1,
            )
            neighbor_nodes.append(child)

            child_h = heuristic(child_state)
            if best_neighbor is None or child_h < best_h:
                best_neighbor = child
                best_h = child_h

        expansions += 1

        if best_neighbor is None:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=neighbor_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=f"Dead-end reached (h={current_h}); no successor",
            )
            break

        if best_h >= current_h:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=neighbor_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=f"Local optimum reached (h={current_h}); best neighbor has h={best_h}",
            )
            break

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=current,
            frontier=neighbor_nodes,
            reached_order=reached_order,
            formatter=formatter,
            note=f"Move to steepest neighbor: {best_neighbor.action} (h: {current_h} -> {best_h})",
        )

        current = best_neighbor
        current_h = best_h

        if current.state not in reached_set:
            reached_set.add(current.state)
            reached_order.append(current.state)

        if is_goal(current.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note=f"GOAL reached by Steepest-Ascent Hill Climbing (h={current_h})",
            )
            path = current.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found by Steepest-Ascent Hill Climbing.",
                expansions,
            )

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"Steepest-Ascent Hill Climbing stopped after expansions={expansions}, depth={current.depth}, h={current_h}.",
        expansions,
    )
