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


def _randomized_beam_state(
    *,
    start_state: object,
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    beam_index: int,
    max_depth: int,
) -> SearchNode:
    state = start_state
    walk_length = random.randint(0, max(1, min(max_depth, 10)))

    for _step_number in range(walk_length):
        successors = list(get_successors(state))
        if not successors:
            break

        _action, state = random.choice(successors)

    action = "START" if beam_index == 1 and state == start_state else f"BEAM_{beam_index}"
    return SearchNode(state=state, parent=None, action=action, depth=0)


def _initial_beam(
    *,
    start_state: object,
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    beam_width: int,
    max_depth: int,
) -> List[SearchNode]:
    beam: List[SearchNode] = [SearchNode(start_state, parent=None, action="START", depth=0)]
    seen_states = {start_state}
    attempts = 0
    max_attempts = max(beam_width * 8, 8)

    while len(beam) < beam_width and attempts < max_attempts:
        attempts += 1
        candidate = _randomized_beam_state(
            start_state=start_state,
            get_successors=get_successors,
            beam_index=len(beam) + 1,
            max_depth=max_depth,
        )
        if candidate.state in seen_states:
            continue

        seen_states.add(candidate.state)
        beam.append(candidate)

    return beam


def _ranked_nodes(nodes: List[SearchNode], formatter: StateFormatter) -> List[SearchNode]:
    return sorted(
        nodes,
        key=lambda node: (
            heuristic(node.state),
            node.depth,
            formatter(node.state),
        ),
    )


def search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
    beam_width: int = 3,
) -> SearchResult:
    """
    Local Beam Search(k).

    - Khoi tao k trang thai ung vien tu Start.
    - Sinh tat ca neighbor cua ca chum hien tai.
    - Neu gap Goal thi dung ngay.
    - Neu chua gap Goal thi giu lai k neighbor co heuristic tot nhat.
    """
    if max_depth is None:
        max_depth = 80

    beam_width = max(1, beam_width)
    current_beam = _initial_beam(
        start_state=start_state,
        get_successors=get_successors,
        beam_width=beam_width,
        max_depth=max_depth,
    )

    trace: List[TraceEntry] = []
    trace_by_state = {}
    reached_set = set()
    reached_order: List[object] = []

    for node in current_beam:
        _remember_state(node.state, reached_set, reached_order)

    expansions = 0
    beam_signatures = {frozenset(node.state for node in current_beam)}
    best_current = _ranked_nodes(current_beam, formatter)[0]

    for beam_position, node in enumerate(current_beam, start=1):
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=current_beam,
            reached_order=reached_order,
            formatter=formatter,
            note=f"Initial beam k={beam_width}; member={beam_position}/{len(current_beam)}",
        )

    for node in current_beam:
        if is_goal(node.state):
            path = node.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found in initial beam.",
                expansions,
            )

    while expansions < max_expansions:
        expandable_nodes = [node for node in current_beam if node.depth < max_depth]
        if not expandable_nodes:
            break

        neighbor_nodes: List[SearchNode] = []
        neighbor_states = set()

        for node in expandable_nodes:
            if expansions >= max_expansions:
                break

            for action, child_state in get_successors(node.state):
                if child_state in neighbor_states:
                    continue

                child = SearchNode(
                    state=child_state,
                    parent=node,
                    action=action,
                    depth=node.depth + 1,
                )
                neighbor_states.add(child_state)
                neighbor_nodes.append(child)
                _remember_state(child_state, reached_set, reached_order)

            expansions += 1

        if not neighbor_nodes:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=best_current,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note="Beam stopped because no neighbor was generated",
            )
            break

        goal_node = next((node for node in neighbor_nodes if is_goal(node.state)), None)
        ranked_neighbors = _ranked_nodes(neighbor_nodes, formatter)
        next_beam = ranked_neighbors[:beam_width]
        next_signature = frozenset(node.state for node in next_beam)
        best_current = next_beam[0]

        selected_scores = ", ".join(
            f"{formatter(node.state)}:h={heuristic(node.state)}"
            for node in next_beam
        )
        repeated_note = "; repeated beam, stop" if next_signature in beam_signatures else ""

        for beam_position, node in enumerate(next_beam, start=1):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=neighbor_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=(
                    f"Generated {len(neighbor_nodes)} neighbors; selected top "
                    f"{len(next_beam)} member={beam_position}/{len(next_beam)} "
                    f"[{selected_scores}]{repeated_note}"
                ),
            )

        if goal_node is not None:
            path = goal_node.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found by Local Beam Search.",
                expansions,
            )

        if next_signature in beam_signatures:
            break

        beam_signatures.add(next_signature)
        current_beam = next_beam

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"Local Beam Search stopped after expansions={expansions}, beam_width={beam_width}.",
        expansions,
    )
