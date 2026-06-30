from __future__ import annotations

import random
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


def _remember_state(state: object, reached_set: set, reached_order: List[object]) -> None:
    if state not in reached_set:
        reached_set.add(state)
        reached_order.append(state)


def _randomized_start_state(
    *,
    start_state: object,
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    walk_length: int,
) -> object:
    state = start_state

    for _step_number in range(max(0, walk_length)):
        successors = list(get_successors(state))
        if not successors:
            break

        _action, state = random.choice(successors)

    return state


def _restart_root(
    *,
    start_state: object,
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    restart_index: int,
    max_depth: int,
) -> SearchNode:
    if restart_index == 1:
        return SearchNode(start_state, parent=None, action="START", depth=0)

    walk_length = random.randint(1, max(1, min(max_depth, 10)))
    restart_state = _randomized_start_state(
        start_state=start_state,
        get_successors=get_successors,
        walk_length=walk_length,
    )
    return SearchNode(
        state=restart_state,
        parent=None,
        action=f"RESTART_{restart_index}",
        depth=0,
    )


def search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
    max_restarts: int = 8,
) -> SearchResult:
    """
    Random-Restart Hill Climbing.

    - Moi restart chay Steepest-Ascent Hill Climbing.
    - Restart dau tien bat dau tu Start; cac restart sau sinh ngau nhien bang random walk tu Start.
    - Dung khi tim thay goal, het restart, het depth, hoac het expansion budget.
    """
    if max_depth is None:
        max_depth = 80

    max_restarts = max(1, max_restarts)

    trace: List[TraceEntry] = []
    trace_by_state = {}
    reached_set = set()
    reached_order: List[object] = []
    expansions = 0

    for restart_index in range(1, max_restarts + 1):
        current = _restart_root(
            start_state=start_state,
            get_successors=get_successors,
            restart_index=restart_index,
            max_depth=max_depth,
        )
        current_h = heuristic(current.state)
        _remember_state(current.state, reached_set, reached_order)

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=current,
            frontier=[current],
            reached_order=reached_order,
            formatter=formatter,
            note=f"Restart {restart_index}/{max_restarts} starts (h={current_h})",
        )

        if is_goal(current.state):
            path = current.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found at restart start.",
                expansions,
            )

        while expansions < max_expansions and current.depth < max_depth:
            successors = list(get_successors(current.state))
            neighbor_nodes: List[SearchNode] = []
            improving_neighbors: List[Tuple[SearchNode, int]] = []

            for action, child_state in successors:
                child = SearchNode(
                    state=child_state,
                    parent=current,
                    action=action,
                    depth=current.depth + 1,
                )
                neighbor_nodes.append(child)
                _remember_state(child_state, reached_set, reached_order)

                child_h = heuristic(child_state)
                if child_h < current_h:
                    improving_neighbors.append((child, child_h))

            expansions += 1

            if not improving_neighbors:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=current,
                    frontier=neighbor_nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"Restart {restart_index} stuck at local optimum (h={current_h}); move to next restart",
                )
                break

            best_h = min(candidate_h for _candidate, candidate_h in improving_neighbors)
            best_candidates = [
                candidate for candidate, candidate_h in improving_neighbors
                if candidate_h == best_h
            ]
            next_state = random.choice(best_candidates)

            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=neighbor_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=(
                    f"Restart {restart_index}: choose best improving neighbor "
                    f"{next_state.action} (h: {current_h} -> {best_h})"
                ),
            )

            current = next_state
            current_h = best_h

            if is_goal(current.state):
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=current,
                    frontier=[],
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"GOAL reached by Random-Restart Hill Climbing (restart={restart_index}, h={current_h})",
                )
                path = current.path()
                return SearchResult(
                    True,
                    path,
                    trace,
                    _align_trace_with_path(path, trace, trace_by_state),
                    "Goal found by Random-Restart Hill Climbing.",
                    expansions,
                )

        if expansions >= max_expansions:
            break

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        (
            "Random-Restart Hill Climbing stopped after "
            f"restarts={max_restarts}, expansions={expansions}."
        ),
        expansions,
    )
