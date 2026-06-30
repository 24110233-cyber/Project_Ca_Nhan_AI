from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, FrozenSet, Iterable, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, append_trace


@dataclass(frozen=True)
class StackItem:
    """Một phần tử trong stack DFS kèm tập state trên đường đi hiện tại."""

    node: SearchNode
    path_states: FrozenSet[object]


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
    DFS dạng 2 có depth limit.

    Đặc điểm dạng 2:
    - Dùng Stack LIFO.
    - Kiểm tra goal ngay khi node con được sinh ra.
    - Có depth limit để tránh DFS đi quá sâu trong 8-Puzzle.
    """
    if max_depth is None:
        max_depth = 12

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    frontier = [StackItem(root, frozenset({start_state}))]

    reached_set = {start_state}
    reached_order = [start_state]

    trace = []
    trace_by_state = {}
    expansions = 0

    if is_goal(start_state):
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=root,
            frontier=[item.node for item in frontier],
            reached_order=reached_order,
            formatter=formatter,
            note="START is goal",
        )
        return SearchResult(True, root.path(), trace, trace_by_state, "Start is already goal.", expansions)

    while frontier and expansions < max_expansions:
        item = frontier.pop()
        node = item.node
        expansions += 1

        if node.depth >= max_depth:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=[frontier_item.node for frontier_item in frontier],
                reached_order=reached_order,
                formatter=formatter,
                note=f"Depth limit reached: depth={node.depth}, max_depth={max_depth}",
            )
            continue

        goal_child = None
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

            if child_state not in reached_set:
                reached_set.add(child_state)
                reached_order.append(child_state)

            if is_goal(child_state):
                goal_child = child
                break

            frontier.append(
                StackItem(
                    node=child,
                    path_states=item.path_states | frozenset({child_state}),
                )
            )

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=[frontier_item.node for frontier_item in frontier],
            reached_order=reached_order,
            formatter=formatter,
            note=f"Expanded node by DFS2; goal checked when child is generated; max_depth={max_depth}",
        )

        if goal_child is not None:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=goal_child,
                frontier=[frontier_item.node for frontier_item in frontier],
                reached_order=reached_order,
                formatter=formatter,
                note="GOAL generated from current node",
            )
            return SearchResult(True, goal_child.path(), trace, trace_by_state, "Goal found when generated.", expansions)

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}, max_depth={max_depth}.",
        expansions,
    )
