from __future__ import annotations

from collections import deque
from typing import Callable, Iterable, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, append_trace


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
    BFS dạng 2.

    Đặc điểm:
    - Dùng Queue FIFO.
    - Kiểm tra goal ngay khi node con được sinh ra.
    - Nếu node con là goal thì dừng ngay, không cần chờ goal bị pop ra khỏi Frontier.
    """
    _ = max_depth  # BFS không dùng depth limit.

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    frontier = deque([root])
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
            frontier=list(frontier),
            reached_order=reached_order,
            formatter=formatter,
            note="START is goal",
        )
        return SearchResult(True, root.path(), trace, trace_by_state, "Start is already goal.", expansions)

    while frontier and expansions < max_expansions:
        node = frontier.popleft()
        expansions += 1
        goal_child = None

        for action, child_state in get_successors(node.state):
            if child_state in reached_set:
                continue

            child = SearchNode(
                state=child_state,
                parent=node,
                action=action,
                depth=node.depth + 1,
            )

            reached_set.add(child_state)
            reached_order.append(child_state)

            if is_goal(child_state):
                goal_child = child
                break

            frontier.append(child)

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=list(frontier),
            reached_order=reached_order,
            formatter=formatter,
            note="Expanded node; goal checked when child is generated",
        )

        if goal_child is not None:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=goal_child,
                frontier=list(frontier),
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
        f"No solution within max_expansions={max_expansions}.",
        expansions,
    )
