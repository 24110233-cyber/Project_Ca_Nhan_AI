from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


@dataclass(frozen=True)
class PlanOutcome:
    node: SearchNode
    plan: "ConditionalPlan"


@dataclass(frozen=True)
class ConditionalPlan:
    action: Optional[str]
    outcomes: Tuple[PlanOutcome, ...] = ()


def _group_result_states(
    successors: Iterable[Tuple[str, object]],
) -> List[Tuple[str, List[object]]]:
    grouped: List[Tuple[str, List[object]]] = []
    action_to_index: Dict[str, int] = {}

    for action, state in successors:
        if action not in action_to_index:
            action_to_index[action] = len(grouped)
            grouped.append((action, []))

        states = grouped[action_to_index[action]][1]
        if state not in states:
            states.append(state)

    return grouped


def _demo_length(plan: ConditionalPlan) -> int:
    if plan.action is None or not plan.outcomes:
        return 0
    return 1 + min(_demo_length(outcome.plan) for outcome in plan.outcomes)


def _extract_demo_path(root: SearchNode, plan: ConditionalPlan) -> List[SearchNode]:
    path = [root]
    current_plan = plan

    while current_plan.action is not None and current_plan.outcomes:
        outcome = min(current_plan.outcomes, key=lambda item: _demo_length(item.plan))
        path.append(outcome.node)
        current_plan = outcome.plan

    return path


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


def _plan_summary(plan: ConditionalPlan, formatter: StateFormatter, depth: int = 0) -> str:
    if plan.action is None:
        return "[]"
    if depth >= 2:
        return f"{plan.action} -> ..."

    branches = ", ".join(
        f"{formatter(outcome.node.state)}: {_plan_summary(outcome.plan, formatter, depth + 1)}"
        for outcome in plan.outcomes[:3]
    )
    if len(plan.outcomes) > 3:
        branches += ", ..."
    return f"{plan.action} -> {{{branches}}}"


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
    AND-OR graph search for conditional planning.

    The project exposes successors as (action, next_state). To model the
    AND-OR pseudocode, states produced by the same action are grouped into that
    action's possible result states. Current deterministic problems therefore
    have one outcome per action, while future nondeterministic problems can
    expose multiple outcomes by returning the same action more than once.
    """
    if max_depth is None:
        max_depth = 20

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    trace: List[TraceEntry] = []
    trace_by_state = {}
    reached_set = {start_state}
    reached_order: List[object] = [start_state]
    expansions = 0
    limit_hit = False

    def or_search(node: SearchNode, path_states: Tuple[object, ...]) -> Optional[ConditionalPlan]:
        nonlocal expansions, limit_hit

        if expansions >= max_expansions:
            limit_hit = True
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note=f"OR_SEARCH stopped: max_expansions={max_expansions}",
            )
            return None

        expansions += 1

        if is_goal(node.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note="OR_SEARCH success: state satisfies goal; return empty plan []",
            )
            return ConditionalPlan(action=None)

        if node.state in path_states:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note="OR_SEARCH failure: repeated state on current path",
            )
            return None

        if node.depth >= max_depth:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note=f"OR_SEARCH cutoff: depth={node.depth}, max_depth={max_depth}",
            )
            return None

        grouped_actions = _group_result_states(get_successors(node.state))
        if not grouped_actions:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note="OR_SEARCH failure: no available action",
            )
            return None

        for action, result_states in grouped_actions:
            result_nodes = [
                SearchNode(state=state, parent=node, action=action, depth=node.depth + 1)
                for state in result_states
            ]

            for state in result_states:
                _remember_state(state, reached_set, reached_order)

            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=result_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=(
                    f"OR_SEARCH tries action={action}; AND_SEARCH must solve "
                    f"{len(result_nodes)} result state(s)"
                ),
            )

            branch_plans = and_search(result_nodes, path_states + (node.state,))
            if branch_plans is None:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=result_nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"OR_SEARCH rejects action={action}: at least one AND branch failed",
                )
                continue

            plan = ConditionalPlan(
                action=action,
                outcomes=tuple(
                    PlanOutcome(result_node, branch_plans[result_node.state])
                    for result_node in result_nodes
                ),
            )
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=result_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=f"OR_SEARCH selects action={action}; plan={_plan_summary(plan, formatter)}",
            )
            return plan

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=[],
            reached_order=reached_order,
            formatter=formatter,
            note="OR_SEARCH failure: every action failed",
        )
        return None

    def and_search(
        nodes: List[SearchNode],
        path_states: Tuple[object, ...],
    ) -> Optional[Dict[object, ConditionalPlan]]:
        plans: Dict[object, ConditionalPlan] = {}

        for child in nodes:
            plan = or_search(child, path_states)
            if plan is None:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=child,
                    frontier=nodes,
                    reached_order=reached_order,
                    formatter=formatter,
                    note="AND_SEARCH failure: this result state has no plan",
                )
                return None

            plans[child.state] = plan
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=child,
                frontier=nodes,
                reached_order=reached_order,
                formatter=formatter,
                note="AND_SEARCH stored plan for this result state",
            )

        return plans

    plan = or_search(root, ())
    if plan is None:
        reason = f"No conditional plan within max_expansions={max_expansions}, max_depth={max_depth}."
        if limit_hit:
            reason = f"Expansion limit reached: max_expansions={max_expansions}, max_depth={max_depth}."
        return SearchResult(False, [], trace, trace_by_state, reason, expansions)

    demo_path = _extract_demo_path(root, plan)
    return SearchResult(
        True,
        demo_path,
        trace,
        _align_trace_with_path(demo_path, trace, trace_by_state),
        f"Conditional plan found: {_plan_summary(plan, formatter)}",
        expansions,
    )
