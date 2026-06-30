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
    DFS dạng 1 có depth limit.

    Vì sao cần depth limit?
    - 8-Puzzle là không gian trạng thái có chu trình.
    - DFS thuần có thể đi rất sâu trước khi gặp goal, dù goal thực tế ở gần.
    - Với start mặc định, DFS graph-search thuần có thể cần hơn 100.000 expansion.
    - GUI sẽ rất nặng nếu vừa DFS quá sâu vừa lưu full Frontier/Reached.

    Đặc điểm dạng 1:
    - Dùng Stack LIFO.
    - Kiểm tra goal khi node được pop ra khỏi stack.
    - Sinh node con nếu chưa vượt max_depth.
    """
    if max_depth is None:
        max_depth = 12

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    frontier = [StackItem(root, frozenset({start_state}))]

    # reached_set/order dùng để hiển thị bảng Reached đầy đủ.
    # DFS vẫn dùng path_states để tránh lặp vòng trên đường đi hiện tại.
    reached_set = {start_state}
    reached_order = [start_state]

    trace = []
    trace_by_state = {}
    expansions = 0

    while frontier and expansions < max_expansions:
        item = frontier.pop()
        node = item.node
        expansions += 1

        frontier_nodes = [frontier_item.node for frontier_item in frontier]

        if is_goal(node.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=frontier_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note="GOAL popped from Stack",
            )
            return SearchResult(True, node.path(), trace, trace_by_state, "Goal found.", expansions)

        if node.depth >= max_depth:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=frontier_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=f"Depth limit reached: depth={node.depth}, max_depth={max_depth}",
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

        frontier_nodes = [frontier_item.node for frontier_item in frontier]

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=frontier_nodes,
            reached_order=reached_order,
            formatter=formatter,
            note=f"Expanded node by DFS1; max_depth={max_depth}; stack top is the rightmost item",
        )

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}, max_depth={max_depth}.",
        expansions,
    )
