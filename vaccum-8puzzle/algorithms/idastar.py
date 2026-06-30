from __future__ import annotations

import math
from typing import Callable, FrozenSet, Iterable, List, Tuple

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
    IDA* (Iterative Deepening A*).

    - Moi vong lap dat nguong f = g + h.
    - Duyet DFS va cat nhanh cac node co f > threshold.
    - Neu chua tim duoc goal thi nang threshold len gia tri f vuot nguong nho nhat.
    """
    if max_depth is None:
        max_depth = 40

    root = SearchNode(start_state, parent=None, action="START", depth=0)
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

    threshold = heuristic(start_state)

    while expansions < max_expansions:
        next_threshold = math.inf

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=root,
            frontier=[root],
            reached_order=reached_order,
            formatter=formatter,
            note=f"Starting IDA* iteration with threshold={threshold}",
        )

        def dfs(
            node: SearchNode,
            g_score: int,
            path_nodes: List[SearchNode],
            path_states: FrozenSet[object],
        ) -> SearchNode | None:
            nonlocal expansions
            nonlocal next_threshold

            f_score = g_score + heuristic(node.state)
            if f_score > threshold:
                if f_score < next_threshold:
                    next_threshold = f_score
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=path_nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"Pruned by threshold: f={f_score} > {threshold}",
                )
                return None

            if expansions >= max_expansions:
                return None

            expansions += 1

            if is_goal(node.state):
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=path_nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"GOAL reached by IDA* (f={f_score}, g={g_score}, h={f_score - g_score})",
                )
                return node

            if node.depth >= max_depth:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=path_nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"Depth cutoff in IDA*: depth={node.depth}, max_depth={max_depth}",
                )
                return None

            successors = list(get_successors(node.state))
            has_expandable_successor = False

            for action, child_state in successors:
                if child_state in path_states:
                    continue

                has_expandable_successor = True
                child = SearchNode(
                    state=child_state,
                    parent=node,
                    action=action,
                    depth=node.depth + 1,
                )

                if child_state not in reached_set:
                    reached_set.add(child_state)
                    reached_order.append(child_state)

                path_nodes.append(child)
                found = dfs(
                    child,
                    g_score + 1,
                    path_nodes,
                    path_states | frozenset({child_state}),
                )
                path_nodes.pop()

                if found is not None:
                    return found

                if expansions >= max_expansions:
                    return None

            if has_expandable_successor:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=path_nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"Expanded in IDA* (f={f_score}, g={g_score}, h={f_score - g_score})",
                )
            else:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=path_nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note="Dead-end in IDA* (no non-cyclic successors)",
                )

            return None

        found_node = dfs(root, 0, [root], frozenset({start_state}))

        if found_node is not None:
            path = found_node.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found by IDA*.",
                expansions,
            )

        if expansions >= max_expansions:
            break

        if next_threshold == math.inf:
            return SearchResult(
                False,
                [],
                trace,
                trace_by_state,
                f"No solution for IDA* within max_depth={max_depth}.",
                expansions,
            )

        threshold = int(next_threshold)

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}, max_depth={max_depth}.",
        expansions,
    )
