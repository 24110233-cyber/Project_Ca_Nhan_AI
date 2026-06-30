from __future__ import annotations

import math
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


def _acceptance_probability(delta: int, temperature: float) -> float:
    if temperature <= 0:
        return 0.0
    return math.exp(-delta / temperature)


def search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
    initial_temperature: float = 20.0,
    minimum_temperature: float = 0.01,
    cooling_rate: float = 0.95,
) -> SearchResult:
    """
    Simulated Annealing.

    - Randomly choose one neighbor from the current state.
    - Always accept a better neighbor where delta = h(next) - h(current) < 0.
    - Sometimes accept a worse/equal neighbor with probability exp(-delta / T).
    - Cool the temperature with T = alpha * T after each sampled neighbor.
    """
    _ = max_depth  # Simulated Annealing stops by temperature and expansion budget.

    temperature = max(0.000001, float(initial_temperature))
    minimum_temperature = max(0.0, float(minimum_temperature))
    cooling_rate = min(0.999, max(0.001, float(cooling_rate)))

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

    while temperature > minimum_temperature and expansions < max_expansions:
        successors = list(get_successors(current.state))
        if not successors:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note=f"Dead-end reached (T={temperature:.4f}, h={current_h}); no successor",
            )
            break

        action, next_state = random.choice(successors)
        next_node = SearchNode(
            state=next_state,
            parent=current,
            action=action,
            depth=current.depth + 1,
        )
        next_h = heuristic(next_state)
        delta = next_h - current_h
        expansions += 1
        _remember_state(next_state, reached_set, reached_order)

        if delta < 0:
            accept = True
            probability = 1.0
            roll_text = "not needed"
        else:
            probability = _acceptance_probability(delta, temperature)
            roll = random.random()
            accept = roll < probability
            roll_text = f"{roll:.4f}"

        decision = "accepted" if accept else "rejected"
        reason = "better neighbor" if delta < 0 else f"p={probability:.4f}, random={roll_text}"

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=current,
            frontier=[next_node],
            reached_order=reached_order,
            formatter=formatter,
            note=(
                f"Random neighbor {action} {decision}; delta={delta}, "
                f"h: {current_h} -> {next_h}, T={temperature:.4f}, {reason}"
            ),
        )

        if accept:
            current = next_node
            current_h = next_h

            if is_goal(current.state):
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=current,
                    frontier=[],
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"GOAL reached by Simulated Annealing (T={temperature:.4f}, h={current_h})",
                )
                path = current.path()
                return SearchResult(
                    True,
                    path,
                    trace,
                    _align_trace_with_path(path, trace, trace_by_state),
                    "Goal found by Simulated Annealing.",
                    expansions,
                )

        temperature *= cooling_rate

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        (
            "Simulated Annealing stopped after "
            f"expansions={expansions}, T={temperature:.4f}, depth={current.depth}, h={current_h}."
        ),
        expansions,
    )
