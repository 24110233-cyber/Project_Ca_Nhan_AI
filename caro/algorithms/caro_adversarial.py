from __future__ import annotations

from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace
from problems.caro import CaroProblem


INF = 10**12


def _depth_limit(max_depth: int | None) -> int:
    if max_depth is None:
        return 2
    return max(1, min(max_depth, 4))


def _children(
    node: SearchNode,
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
) -> List[SearchNode]:
    return [
        SearchNode(state=child_state, parent=node, action=action, depth=node.depth + 1)
        for action, child_state in get_successors(node.state)
    ]


def _align_trace_with_path(
    path: List[SearchNode],
    trace: List[TraceEntry],
    trace_by_state: dict,
) -> dict:
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


def _one_move_path(line: List[SearchNode]) -> List[SearchNode]:
    if len(line) > 1:
        return line[:2]
    return line


def _failure(message: str) -> SearchResult:
    return SearchResult(False, [], [], {}, message, 0)


def _finish(
    *,
    algorithm_name: str,
    root: SearchNode,
    line: List[SearchNode],
    score: int,
    depth_limit: int,
    trace: List[TraceEntry],
    trace_by_state: dict,
    expansions: int,
    cutoff: bool,
) -> SearchResult:
    path = _one_move_path(line)
    if len(path) == 1 and not CaroProblem.is_goal(root.state):
        return SearchResult(False, [], trace, trace_by_state, f"{algorithm_name} found no legal move.", expansions)

    if len(path) > 1:
        message = f"{algorithm_name} selected {path[-1].action} (score={score}, depth={depth_limit})."
    else:
        message = f"{algorithm_name}: game is already finished."

    if cutoff:
        message += " Search stopped at max_expansions."

    return SearchResult(
        True,
        path,
        trace,
        _align_trace_with_path(path, trace, trace_by_state),
        message,
        expansions,
    )


def minimax_search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    if not CaroProblem.is_caro_state(start_state):
        return _failure("Minimax is available only for Caro.")

    depth_limit = _depth_limit(max_depth)
    root_state = start_state  # type: ignore[assignment]
    root_player = CaroProblem.current_player(root_state)
    root = SearchNode(root_state, parent=None, action="START", depth=0)

    trace: List[TraceEntry] = []
    trace_by_state = {}
    reached_set = {start_state}
    reached_order = [start_state]
    expansions = 0
    cutoff = False

    def record(node: SearchNode, frontier: List[SearchNode], note: str) -> bool:
        nonlocal expansions, cutoff
        if expansions >= max_expansions:
            cutoff = True
            return False
        expansions += 1
        if node.state not in reached_set:
            reached_set.add(node.state)
            reached_order.append(node.state)
        for child in frontier:
            if child.state not in reached_set:
                reached_set.add(child.state)
                reached_order.append(child.state)
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=frontier,
            reached_order=reached_order,
            formatter=formatter,
            note=note,
        )
        return True

    def solve(node: SearchNode, depth_left: int) -> Tuple[int, List[SearchNode]]:
        nonlocal cutoff
        state = node.state  # type: ignore[assignment]
        score = CaroProblem.evaluate(state, root_player)

        if depth_left == 0 or is_goal(node.state):
            record(node, [], f"Leaf evaluated by Minimax: score={score}, depth_left={depth_left}")
            return score, [node]

        child_nodes = _children(node, get_successors)
        if not child_nodes:
            record(node, [], f"Terminal/no-move node: score={score}")
            return score, [node]

        maximizing = CaroProblem.current_player(state) == root_player
        mode = "MAX" if maximizing else "MIN"
        if not record(node, child_nodes, f"Minimax {mode} node; depth_left={depth_left}; children={len(child_nodes)}"):
            return score, [node]

        best_score = -INF if maximizing else INF
        best_line = [node]

        for child in child_nodes:
            child_score, child_line = solve(child, depth_left - 1)
            if maximizing and child_score > best_score:
                best_score = child_score
                best_line = [node] + child_line
            elif not maximizing and child_score < best_score:
                best_score = child_score
                best_line = [node] + child_line

            if cutoff:
                break

        return int(best_score), best_line

    score, line = solve(root, depth_limit)
    return _finish(
        algorithm_name="Minimax",
        root=root,
        line=line,
        score=score,
        depth_limit=depth_limit,
        trace=trace,
        trace_by_state=trace_by_state,
        expansions=expansions,
        cutoff=cutoff,
    )


def alpha_beta_search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    if not CaroProblem.is_caro_state(start_state):
        return _failure("Alpha-Beta is available only for Caro.")

    depth_limit = _depth_limit(max_depth)
    root_state = start_state  # type: ignore[assignment]
    root_player = CaroProblem.current_player(root_state)
    root = SearchNode(root_state, parent=None, action="START", depth=0)

    trace: List[TraceEntry] = []
    trace_by_state = {}
    reached_set = {start_state}
    reached_order = [start_state]
    expansions = 0
    cutoff = False

    def record(node: SearchNode, frontier: List[SearchNode], note: str) -> bool:
        nonlocal expansions, cutoff
        if expansions >= max_expansions:
            cutoff = True
            return False
        expansions += 1
        if node.state not in reached_set:
            reached_set.add(node.state)
            reached_order.append(node.state)
        for child in frontier:
            if child.state not in reached_set:
                reached_set.add(child.state)
                reached_order.append(child.state)
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=frontier,
            reached_order=reached_order,
            formatter=formatter,
            note=note,
        )
        return True

    def prune_trace(node: SearchNode, remaining: List[SearchNode], alpha: int, beta: int) -> None:
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=remaining,
            reached_order=reached_order,
            formatter=formatter,
            note=f"Alpha-Beta prune: alpha={alpha}, beta={beta}, skipped={len(remaining)}",
        )

    def solve(node: SearchNode, depth_left: int, alpha: int, beta: int) -> Tuple[int, List[SearchNode]]:
        nonlocal cutoff
        state = node.state  # type: ignore[assignment]
        score = CaroProblem.evaluate(state, root_player)

        if depth_left == 0 or is_goal(node.state):
            record(node, [], f"Leaf evaluated by Alpha-Beta: score={score}, alpha={alpha}, beta={beta}")
            return score, [node]

        child_nodes = _children(node, get_successors)
        if not child_nodes:
            record(node, [], f"Terminal/no-move node: score={score}")
            return score, [node]

        maximizing = CaroProblem.current_player(state) == root_player
        mode = "MAX" if maximizing else "MIN"
        if not record(
            node,
            child_nodes,
            f"Alpha-Beta {mode} node; depth_left={depth_left}; alpha={alpha}; beta={beta}; children={len(child_nodes)}",
        ):
            return score, [node]

        best_line = [node]

        if maximizing:
            best_score = -INF
            for index, child in enumerate(child_nodes):
                child_score, child_line = solve(child, depth_left - 1, alpha, beta)
                if child_score > best_score:
                    best_score = child_score
                    best_line = [node] + child_line
                alpha = max(alpha, int(best_score))
                if cutoff:
                    break
                if beta <= alpha:
                    prune_trace(node, child_nodes[index + 1 :], alpha, beta)
                    break
            return int(best_score), best_line

        best_score = INF
        for index, child in enumerate(child_nodes):
            child_score, child_line = solve(child, depth_left - 1, alpha, beta)
            if child_score < best_score:
                best_score = child_score
                best_line = [node] + child_line
            beta = min(beta, int(best_score))
            if cutoff:
                break
            if beta <= alpha:
                prune_trace(node, child_nodes[index + 1 :], alpha, beta)
                break
        return int(best_score), best_line

    score, line = solve(root, depth_limit, -INF, INF)
    return _finish(
        algorithm_name="Alpha-Beta",
        root=root,
        line=line,
        score=score,
        depth_limit=depth_limit,
        trace=trace,
        trace_by_state=trace_by_state,
        expansions=expansions,
        cutoff=cutoff,
    )


def expectimax_search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    if not CaroProblem.is_caro_state(start_state):
        return _failure("Expectimax is available only for Caro.")

    depth_limit = _depth_limit(max_depth)
    root_state = start_state  # type: ignore[assignment]
    root_player = CaroProblem.current_player(root_state)
    root = SearchNode(root_state, parent=None, action="START", depth=0)

    trace: List[TraceEntry] = []
    trace_by_state = {}
    reached_set = {start_state}
    reached_order = [start_state]
    expansions = 0
    cutoff = False

    def record(node: SearchNode, frontier: List[SearchNode], note: str) -> bool:
        nonlocal expansions, cutoff
        if expansions >= max_expansions:
            cutoff = True
            return False
        expansions += 1
        if node.state not in reached_set:
            reached_set.add(node.state)
            reached_order.append(node.state)
        for child in frontier:
            if child.state not in reached_set:
                reached_set.add(child.state)
                reached_order.append(child.state)
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=frontier,
            reached_order=reached_order,
            formatter=formatter,
            note=note,
        )
        return True

    def solve(node: SearchNode, depth_left: int) -> Tuple[int, List[SearchNode]]:
        nonlocal cutoff
        state = node.state  # type: ignore[assignment]
        score = CaroProblem.evaluate(state, root_player)

        if depth_left == 0 or is_goal(node.state):
            record(node, [], f"Leaf evaluated by Expectimax: score={score}, depth_left={depth_left}")
            return score, [node]

        child_nodes = _children(node, get_successors)
        if not child_nodes:
            record(node, [], f"Terminal/no-move node: score={score}")
            return score, [node]

        maximizing = CaroProblem.current_player(state) == root_player
        node_type = "MAX" if maximizing else "EXPECT"
        if not record(node, child_nodes, f"Expectimax {node_type} node; depth_left={depth_left}; children={len(child_nodes)}"):
            return score, [node]

        if maximizing:
            best_score = -INF
            best_line = [node]
            for child in child_nodes:
                child_score, child_line = solve(child, depth_left - 1)
                if child_score > best_score:
                    best_score = child_score
                    best_line = [node] + child_line
                if cutoff:
                    break
            return int(best_score), best_line

        total = 0
        sampled = 0
        first_line: List[SearchNode] | None = None
        for child in child_nodes:
            child_score, child_line = solve(child, depth_left - 1)
            if first_line is None:
                first_line = [node] + child_line
            total += child_score
            sampled += 1
            if cutoff:
                break

        if sampled == 0:
            return score, [node]
        return int(total / sampled), (first_line if first_line is not None else [node])

    score, line = solve(root, depth_limit)
    return _finish(
        algorithm_name="Expectimax",
        root=root,
        line=line,
        score=score,
        depth_limit=depth_limit,
        trace=trace,
        trace_by_state=trace_by_state,
        expansions=expansions,
        cutoff=cutoff,
    )
