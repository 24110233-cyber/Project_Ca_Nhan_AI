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
    BFS dạng 1.

    Đặc điểm:
    - Dùng Queue FIFO.
    - Lấy node ra khỏi Frontier trước.
    - Kiểm tra goal sau khi lấy node ra.
    - Nếu chưa phải goal thì mới sinh node con.
    """
    _ = max_depth  # BFS không dùng depth limit.

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    frontier = deque([root])
    reached_set = {start_state}
    reached_order = [start_state]

    trace = []
    trace_by_state = {}
    expansions = 0

    while frontier and expansions < max_expansions:
        node = frontier.popleft()
        expansions += 1

        if is_goal(node.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=list(frontier),
                reached_order=reached_order,
                formatter=formatter,
                note="GOAL popped from Frontier",
            )
            return SearchResult(True, node.path(), trace, trace_by_state, "Goal found.", expansions)

        for action, child_state in get_successors(node.state):
            if child_state in reached_set:
                continue

            child = SearchNode(
                state=child_state,
                parent=node,
                action=action,
                depth=node.depth + 1,
            )
            frontier.append(child)
            reached_set.add(child_state)
            reached_order.append(child_state)

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=list(frontier),
            reached_order=reached_order,
            formatter=formatter,
            note="Expanded node; goal checked when popped",
        )

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}.",
        expansions,
    )
