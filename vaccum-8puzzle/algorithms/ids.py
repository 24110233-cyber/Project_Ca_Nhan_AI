from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, FrozenSet, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


@dataclass(frozen=True)
class StackItem:
    """Một phần tử stack của IDS kèm tập state trên đường đi hiện tại."""

    node: SearchNode
    path_states: FrozenSet[object]


def _frontier_nodes(frontier: List[StackItem]) -> List[SearchNode]:
    return [item.node for item in frontier]


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
    Iterative Deepening Search (IDS).

    - Lặp depth-limit từ 0 đến max_depth.
    - Mỗi lượt chạy Depth-Limited DFS bằng stack LIFO.
    - Goal được kiểm tra khi node bị pop khỏi stack.
    """
    if max_depth is None:
        max_depth = 20

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

    for limit in range(max_depth + 1):
        frontier = [StackItem(root, frozenset({start_state}))]

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=root,
            frontier=_frontier_nodes(frontier),
            reached_order=reached_order,
            formatter=formatter,
            note=f"Starting IDS iteration with depth limit={limit}",
        )

        while frontier and expansions < max_expansions:
            item = frontier.pop()
            node = item.node
            expansions += 1

            if is_goal(node.state):
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=_frontier_nodes(frontier),
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"GOAL popped from Stack in IDS iteration limit={limit}",
                )
                path = node.path()
                return SearchResult(
                    True,
                    path,
                    trace,
                    _align_trace_with_path(path, trace, trace_by_state),
                    f"Goal found by IDS at depth={node.depth}, limit={limit}.",
                    expansions,
                )

            if node.depth >= limit:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=_frontier_nodes(frontier),
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"Cutoff in IDS iteration: depth={node.depth}, limit={limit}",
                )
                continue

            successors = list(get_successors(node.state))

            # Đảo thứ tự push để action đầu tiên trong successors được pop ra trước.
            for action, child_state in reversed(successors):
                if child_state in item.path_states:
                    continue

                child = SearchNode(
                    state=child_state,
                    parent=node,
                    action=action,
                    depth=node.depth + 1,
                )
                frontier.append(
                    StackItem(
                        node=child,
                        path_states=item.path_states | frozenset({child_state}),
                    )
                )

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
                note=f"Expanded in IDS iteration limit={limit}; stack top is the rightmost item",
            )

        if expansions >= max_expansions:
            break

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}, max_depth={max_depth}.",
        expansions,
    )

