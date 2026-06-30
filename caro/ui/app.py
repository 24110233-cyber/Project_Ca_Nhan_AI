from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Tuple

from algorithms import ALGORITHMS
from algorithms.common import SearchNode, SearchResult
from problems.caro import CaroProblem, CaroState


CARO_ALGORITHMS = ["MINIMAX", "ALPHA_BETA", "EXPECTIMAX"]


class CaroApp(tk.Tk):
    CELL_SIZE = 58
    GAP = 4

    COLORS = {
        "bg": "#020617",
        "panel": "#06120B",
        "panel_2": "#081C10",
        "line": "#14532D",
        "primary": "#22C55E",
        "primary_2": "#86EFAC",
        "text": "#DCFCE7",
        "muted": "#86EFAC",
        "warning": "#FACC15",
        "danger": "#F87171",
        "blank": "#030712",
    }

    def __init__(self) -> None:
        super().__init__()

        self.title("Caro Adversarial AI")
        self.geometry("1180x800")
        self.minsize(1080, 720)
        self.configure(bg=self.COLORS["bg"])

        self.algorithm_var = tk.StringVar(value="ALPHA_BETA")
        self.max_expansions_var = tk.StringVar(value="3000")
        self.max_depth_var = tk.StringVar(value="2")

        self.caro_state: CaroState = CaroProblem.start_state()
        self.search_result: Optional[SearchResult] = None
        self.solution_path: List[SearchNode] = []
        self.current_step = 0

        self.animation_job: Optional[str] = None
        self.is_animating = False
        self.is_searching = False
        self.result_queue: queue.Queue = queue.Queue()

        self._setup_styles()
        self._build_layout()
        self.draw_board()
        self.update_status("HUMAN TURN: click an empty cell. AI will reply automatically.")

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            ".",
            background=self.COLORS["bg"],
            foreground=self.COLORS["text"],
            fieldbackground=self.COLORS["panel_2"],
            font=("Consolas", 10),
        )
        style.configure("Root.TFrame", background=self.COLORS["bg"])
        style.configure("Panel.TFrame", background=self.COLORS["panel"], relief="solid", borderwidth=1)
        style.configure(
            "Title.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["primary_2"],
            font=("Consolas", 25, "bold"),
        )
        style.configure(
            "Panel.TLabel",
            background=self.COLORS["panel"],
            foreground=self.COLORS["primary_2"],
            font=("Consolas", 11, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["muted"],
            font=("Consolas", 9),
        )
        style.configure(
            "Run.TButton",
            background=self.COLORS["primary"],
            foreground="#001B0A",
            font=("Consolas", 11, "bold"),
            padding=8,
            borderwidth=0,
        )
        style.map("Run.TButton", background=[("active", self.COLORS["primary_2"])])
        style.configure(
            "Matrix.TButton",
            background=self.COLORS["panel_2"],
            foreground=self.COLORS["text"],
            font=("Consolas", 10, "bold"),
            padding=8,
            borderwidth=1,
        )
        style.map("Matrix.TButton", background=[("active", "#14532D")])
        style.configure(
            "Treeview",
            background="#020617",
            foreground=self.COLORS["text"],
            fieldbackground="#020617",
            rowheight=32,
            font=("Consolas", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=self.COLORS["panel_2"],
            foreground=self.COLORS["primary_2"],
            font=("Consolas", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#14532D")], foreground=[("selected", "#FFFFFF")])

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text="CARO ADVERSARIAL AI", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(root, text="Minimax, Alpha-Beta, and Expectimax on a 7x7 Caro board", style="Muted.TLabel").pack(
            anchor=tk.W,
            pady=(0, 12),
        )

        top = ttk.Frame(root, style="Root.TFrame")
        top.pack(fill=tk.X)

        self._build_sidebar(top)
        self._build_board(top)
        self._build_status_panel(top)
        self._build_trace_panel(root)

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        side = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        side.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            side,
            text="[ CARO CONTROL ]",
            bg=self.COLORS["panel"],
            fg=self.COLORS["primary_2"],
            font=("Consolas", 13, "bold"),
        ).pack(anchor=tk.W, pady=(0, 18))

        ttk.Label(side, text="ALGORITHM", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Combobox(
            side,
            textvariable=self.algorithm_var,
            values=CARO_ALGORITHMS,
            state="readonly",
            width=16,
        ).pack(fill=tk.X, pady=(5, 14))

        ttk.Label(side, text="MAX EXPANSIONS", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Entry(side, textvariable=self.max_expansions_var, width=16).pack(fill=tk.X, pady=(5, 14))

        ttk.Label(side, text="DEPTH LIMIT", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Entry(side, textvariable=self.max_depth_var, width=16).pack(fill=tk.X, pady=(5, 22))

        ttk.Button(side, text="FORCE AI MOVE", style="Run.TButton", command=self.apply_search).pack(fill=tk.X, pady=4)
        ttk.Button(side, text="HALT", style="Matrix.TButton", command=self.stop_animation).pack(fill=tk.X, pady=4)
        ttk.Button(side, text="GENERATE BOARD", style="Matrix.TButton", command=self.generate_board).pack(fill=tk.X, pady=4)
        ttk.Button(side, text="RESET", style="Matrix.TButton", command=self.reset_board).pack(fill=tk.X, pady=4)

        guide = "\nHUMAN VS AI\nCLICK: HUMAN X MOVE\nAI O: AUTO REPLY\nBUTTON: FORCE AI TURN"
        tk.Label(
            side,
            text=guide,
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            justify=tk.LEFT,
            font=("Consolas", 9),
        ).pack(anchor=tk.W, pady=(22, 0))

    def _build_board(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        panel.pack(side=tk.LEFT, padx=(12, 12))

        self.board_title = tk.Label(
            panel,
            text="CARO 7x7 GRID",
            bg=self.COLORS["panel"],
            fg=self.COLORS["primary_2"],
            font=("Consolas", 16, "bold"),
        )
        self.board_title.pack(anchor=tk.W)

        canvas_size = CaroProblem.SIZE * self.CELL_SIZE + (CaroProblem.SIZE - 1) * self.GAP + 24
        self.board_canvas = tk.Canvas(
            panel,
            width=canvas_size,
            height=canvas_size,
            bg=self.COLORS["panel_2"],
            highlightthickness=1,
            highlightbackground=self.COLORS["line"],
        )
        self.board_canvas.pack(pady=(12, 0))
        self.board_canvas.bind("<Button-1>", self.on_board_click)

    def _build_status_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            panel,
            text="[ LIVE METRICS ]",
            bg=self.COLORS["panel"],
            fg=self.COLORS["primary_2"],
            font=("Consolas", 13, "bold"),
        ).pack(anchor=tk.W)

        self.stats_label = tk.Label(
            panel,
            text="",
            bg=self.COLORS["panel"],
            fg=self.COLORS["text"],
            justify=tk.LEFT,
            anchor="nw",
            font=("Consolas", 11, "bold"),
            padx=4,
            pady=10,
        )
        self.stats_label.pack(fill=tk.X, pady=(10, 10))

        self.status_label = tk.Label(
            panel,
            text="",
            bg="#020617",
            fg=self.COLORS["primary_2"],
            justify=tk.LEFT,
            anchor="nw",
            font=("Consolas", 10),
            padx=10,
            pady=10,
            wraplength=340,
        )
        self.status_label.pack(fill=tk.X)

        tk.Label(
            panel,
            text="[ SELECTED TRACE DETAIL ]",
            bg=self.COLORS["panel"],
            fg=self.COLORS["primary_2"],
            font=("Consolas", 13, "bold"),
        ).pack(anchor=tk.W, pady=(18, 8))

        self.detail_text = ScrolledText(
            panel,
            height=11,
            bg="#020617",
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief=tk.FLAT,
            font=("Consolas", 9),
            wrap=tk.NONE,
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_text.configure(state=tk.DISABLED)

    def _build_trace_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=10)
        panel.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        header = tk.Frame(panel, bg=self.COLORS["panel"])
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="[ FULL SEARCH TRACE ]",
            bg=self.COLORS["panel"],
            fg=self.COLORS["primary_2"],
            font=("Consolas", 13, "bold"),
        ).pack(side=tk.LEFT)

        self.step_counter_label = tk.Label(
            header,
            text="0/0",
            bg=self.COLORS["panel"],
            fg=self.COLORS["warning"],
            font=("Consolas", 11, "bold"),
        )
        self.step_counter_label.pack(side=tk.RIGHT)

        table_frame = ttk.Frame(panel, style="Panel.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        columns = ("step", "action", "current", "frontier_count", "frontier", "reached_count", "reached", "note")
        widths = {
            "step": 60,
            "action": 110,
            "current": 180,
            "frontier_count": 80,
            "frontier": 760,
            "reached_count": 80,
            "reached": 980,
            "note": 280,
        }
        headings = {
            "step": "STEP",
            "action": "ACTION",
            "current": "CURRENT NODE",
            "frontier_count": "F.COUNT",
            "frontier": "FRONTIER - FULL",
            "reached_count": "R.COUNT",
            "reached": "REACHED - FULL",
            "note": "NOTE",
        }

        self.trace_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.trace_tree.heading(col, text=headings[col])
            self.trace_tree.column(col, width=widths[col], minwidth=widths[col], stretch=False, anchor=tk.W)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.trace_tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.trace_tree.xview)
        self.trace_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.trace_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.trace_tree.bind("<<TreeviewSelect>>", self.on_trace_selected)

    def draw_board(self) -> None:
        self.board_canvas.delete("all")
        offset = 12
        board, _player = self.caro_state
        winner = CaroProblem.winner(self.caro_state)

        for row in range(CaroProblem.SIZE):
            for col in range(CaroProblem.SIZE):
                x1 = offset + col * (self.CELL_SIZE + self.GAP)
                y1 = offset + row * (self.CELL_SIZE + self.GAP)
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                value = board[CaroProblem.index(row, col)]
                fill = self.COLORS["blank"] if value == CaroProblem.EMPTY else self.COLORS["panel"]
                outline = self.COLORS["warning"] if winner != CaroProblem.EMPTY and value == winner else self.COLORS["line"]
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=2)

                if value != CaroProblem.EMPTY:
                    color = self.COLORS["danger"] if value == CaroProblem.HUMAN else self.COLORS["primary_2"]
                    self.board_canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=CaroProblem.player_label(value),
                        fill=color,
                        font=("Consolas", 29, "bold"),
                    )

        self.update_stats()

    def update_status(self, message: str) -> None:
        self.status_label.configure(text=f"> {message}")

    def update_stats(self) -> None:
        board, player = self.caro_state
        winner = CaroProblem.winner(self.caro_state)
        empty_cells = sum(cell == CaroProblem.EMPTY for cell in board)
        if winner != CaroProblem.EMPTY:
            status = f"{CaroProblem.player_label(winner)} WINS"
        elif CaroProblem.is_draw(self.caro_state):
            status = "DRAW"
        else:
            status = "RUNNING"
        self.stats_label.configure(
            text=(
                f"MODE       : CARO 7x7\n"
                f"ALGORITHM  : {self.algorithm_var.get()}\n"
                f"STEP       : {self.current_step if self.solution_path else 0}\n"
                f"TURN       : {CaroProblem.player_label(player)}\n"
                f"EMPTY      : {empty_cells}\n"
                f"STATUS     : {status}"
            )
        )
        total = max(0, len(self.solution_path) - 1)
        self.step_counter_label.configure(text=f"{min(self.current_step, total)}/{total}")

    def clear_trace_table(self) -> None:
        for item in self.trace_tree.get_children():
            self.trace_tree.delete(item)
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.configure(state=tk.DISABLED)

    def insert_trace_row_for_node(self, step: int, node: SearchNode) -> None:
        entry = self.search_result.trace_by_state.get(node.state) if self.search_result else None
        if entry is None:
            values = (step, node.action, CaroProblem.format_state(node.state), 0, "", 0, "", "Trace entry was not found.")
        else:
            values = (
                step,
                node.action,
                entry.current_text,
                entry.frontier_count,
                entry.frontier_text,
                entry.reached_count,
                entry.reached_text,
                entry.note,
            )
        item_id = self.trace_tree.insert("", tk.END, values=values)
        self.trace_tree.see(item_id)
        self.trace_tree.selection_set(item_id)
        self.show_trace_detail(values)

    def on_trace_selected(self, _event: tk.Event) -> None:
        selected = self.trace_tree.selection()
        if selected:
            self.show_trace_detail(self.trace_tree.item(selected[0], "values"))

    def show_trace_detail(self, values) -> None:
        if not values:
            return
        step, action, current, frontier_count, frontier, reached_count, reached, note = values
        content = (
            f"STEP: {step}\nACTION: {action}\nCURRENT NODE:\n{current}\n\n"
            f"FRONTIER COUNT: {frontier_count}\nFRONTIER FULL:\n{frontier if frontier else '-'}\n\n"
            f"REACHED COUNT: {reached_count}\nREACHED FULL:\n{reached if reached else '-'}\n\nNOTE:\n{note}\n"
        )
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, content)
        self.detail_text.configure(state=tk.DISABLED)

    def apply_search(self, *, auto: bool = False) -> None:
        if self.is_searching or self.is_animating:
            return
        if CaroProblem.is_goal(self.caro_state):
            self.update_status(self.terminal_message())
            return
        if CaroProblem.current_player(self.caro_state) != CaroProblem.AI:
            self.update_status("HUMAN TURN: click an empty cell before AI moves.")
            return

        self.stop_animation(silent=auto)
        self.clear_trace_table()
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.update_stats()

        algorithm_name = self.algorithm_var.get()
        search_function = ALGORITHMS[algorithm_name]
        self.is_searching = True
        self.update_status(f"AI THINKING WITH {algorithm_name}...")

        search_kwargs = {
            "start_state": self.caro_state,
            "is_goal": CaroProblem.is_goal,
            "get_successors": CaroProblem.successors,
            "formatter": CaroProblem.format_state,
            "max_expansions": self.read_max_expansions(),
            "max_depth": self.read_max_depth(),
        }

        def worker() -> None:
            try:
                result = search_function(**search_kwargs)
                self.result_queue.put(("success", result))
            except Exception as exc:
                self.result_queue.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self.poll_search_result)

    def poll_search_result(self) -> None:
        try:
            kind, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self.poll_search_result)
            return

        self.is_searching = False
        if kind == "error":
            self.update_status(f"SEARCH ERROR: {payload}")
            return

        result: SearchResult = payload
        self.search_result = result
        if not result.found:
            self.update_status(f"{result.message} EXPANSIONS={result.expansions}.")
            return

        self.solution_path = result.path
        self.current_step = 0
        self.is_animating = True
        self.update_status(f"{result.message} EXPANSIONS={result.expansions}.")
        self.animate_next_step()

    def animate_next_step(self) -> None:
        if not self.is_animating:
            return
        if self.current_step >= len(self.solution_path):
            self.is_animating = False
            self.current_step = max(0, len(self.solution_path) - 1)
            self.update_status(
                self.terminal_message()
                if CaroProblem.is_goal(self.caro_state)
                else "AI MOVE APPLIED. HUMAN TURN: click an empty cell."
            )
            self.draw_board()
            return

        node = self.solution_path[self.current_step]
        self.caro_state = node.state  # type: ignore[assignment]
        self.draw_board()
        self.insert_trace_row_for_node(self.current_step, node)
        self.update_status("STEP 0: START" if self.current_step == 0 else f"STEP {self.current_step}: {node.action}")
        self.current_step += 1
        self.animation_job = self.after(650, self.animate_next_step)

    def stop_animation(self, *, silent: bool = False) -> None:
        self.is_animating = False
        if self.animation_job is not None:
            try:
                self.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            finally:
                self.animation_job = None
        if not silent and not self.is_searching:
            self.update_status("HALTED.")

    def on_board_click(self, event: tk.Event) -> None:
        if self.is_searching or self.is_animating:
            return
        if CaroProblem.is_goal(self.caro_state):
            self.update_status(self.terminal_message())
            return
        if CaroProblem.current_player(self.caro_state) != CaroProblem.HUMAN:
            self.update_status("AI TURN: wait for AI or press FORCE AI MOVE.")
            return

        row_col = self.board_cell_at(event.x, event.y)
        if row_col is None:
            return
        self.stop_animation(silent=True)
        row, col = row_col
        old_state = self.caro_state
        self.caro_state = CaroProblem.click_move(self.caro_state, row, col)
        if self.caro_state != old_state:
            self.after_human_move()

    def board_cell_at(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        offset = 12
        for row in range(CaroProblem.SIZE):
            for col in range(CaroProblem.SIZE):
                x1 = offset + col * (self.CELL_SIZE + self.GAP)
                y1 = offset + row * (self.CELL_SIZE + self.GAP)
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return row, col
        return None

    def after_human_move(self) -> None:
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        if CaroProblem.is_goal(self.caro_state):
            self.update_status(self.terminal_message())
            return

        self.update_status("HUMAN MOVE ACCEPTED. AI is thinking...")
        self.after(150, lambda: self.apply_search(auto=True))

    def terminal_message(self) -> str:
        winner = CaroProblem.winner(self.caro_state)
        if winner != CaroProblem.EMPTY:
            return f"CARO GAME OVER: {CaroProblem.player_label(winner)} WINS."
        if CaroProblem.is_draw(self.caro_state):
            return "CARO GAME OVER: DRAW."
        return "CARO GAME STILL RUNNING."

    def read_max_expansions(self) -> int:
        try:
            value = int(self.max_expansions_var.get())
        except ValueError:
            value = 3000
        return max(100, min(value, 50000))

    def read_max_depth(self) -> int:
        try:
            value = int(self.max_depth_var.get())
        except ValueError:
            value = 2
        return max(1, min(value, 4))

    def generate_board(self) -> None:
        self.stop_animation()
        self.caro_state = CaroProblem.random_state()
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        self.update_status("CARO BOARD GENERATED.")

    def reset_board(self) -> None:
        self.stop_animation()
        self.caro_state = CaroProblem.start_state()
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        self.update_status("RESET COMPLETE.")
