from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence


StateFormatter = Callable[[object], str]


@dataclass(frozen=True)
class SearchNode:
    """Một node trong cây/đồ thị tìm kiếm."""

    state: object
    parent: Optional["SearchNode"]
    action: str
    depth: int

    def path(self) -> List["SearchNode"]:
        """Trả về danh sách node từ start đến node hiện tại."""
        nodes: List[SearchNode] = []
        current: Optional[SearchNode] = self

        while current is not None:
            nodes.append(current)
            current = current.parent

        nodes.reverse()
        return nodes


@dataclass(frozen=True)
class TraceEntry:
    """
    Một dòng trace đầy đủ của thuật toán.

    Lưu ý:
    - frontier_text không bị cắt ngắn.
    - reached_text không bị cắt ngắn.
    - GUI có thanh cuộn ngang và khung chi tiết để xem toàn bộ nội dung.
    """

    trace_step: int
    state: object
    action: str
    depth: int
    current_text: str
    frontier_count: int
    frontier_text: str
    reached_count: int
    reached_text: str
    note: str


@dataclass(frozen=True)
class SearchResult:
    found: bool
    path: List[SearchNode]
    trace: List[TraceEntry]
    trace_by_state: dict
    message: str
    expansions: int


def states_to_text(states: Iterable[object], formatter: StateFormatter) -> str:
    """Chuyển toàn bộ danh sách state sang chuỗi, không rút gọn."""
    return "  |  ".join(formatter(state) for state in states)


def frontier_to_text(frontier: Sequence[SearchNode], formatter: StateFormatter) -> str:
    """Chuyển toàn bộ Frontier sang chuỗi, không rút gọn."""
    return "  |  ".join(formatter(node.state) for node in frontier)


def make_trace_entry(
    *,
    trace_step: int,
    node: SearchNode,
    frontier: Sequence[SearchNode],
    reached_order: Sequence[object],
    formatter: StateFormatter,
    note: str,
) -> TraceEntry:
    """Tạo một dòng trace đầy đủ."""
    return TraceEntry(
        trace_step=trace_step,
        state=node.state,
        action=node.action,
        depth=node.depth,
        current_text=formatter(node.state),
        frontier_count=len(frontier),
        frontier_text=frontier_to_text(frontier, formatter),
        reached_count=len(reached_order),
        reached_text=states_to_text(reached_order, formatter),
        note=note,
    )


def append_trace(
    *,
    trace: List[TraceEntry],
    trace_by_state: dict,
    node: SearchNode,
    frontier: Sequence[SearchNode],
    reached_order: Sequence[object],
    formatter: StateFormatter,
    note: str,
) -> None:
    """Thêm trace vào danh sách và ánh xạ state -> trace."""
    entry = make_trace_entry(
        trace_step=len(trace),
        node=node,
        frontier=frontier,
        reached_order=reached_order,
        formatter=formatter,
        note=note,
    )

    trace.append(entry)

    # Giữ trace đầu tiên của state để đồng bộ với bước di chuyển trên lời giải.
    trace_by_state.setdefault(node.state, entry)
