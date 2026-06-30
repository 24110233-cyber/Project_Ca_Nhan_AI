from __future__ import annotations

import inspect
import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Tuple

from algorithms import ALGORITHMS
from algorithms.common import SearchNode, SearchResult
from problems.puzzle import PuzzleProblem, PuzzleState
from problems.vacuum import VacuumProblem, VacuumState


PATH_ALGORITHMS = [
    "BFS1",
    "BFS2",
    "DFS1",
    "DFS2",
    "UCS",
    "GREEDY",
    "ASTAR",
    "IDS",
    "IDA*",
    "HILL_SIMPLE",
    "HILL_STEEPEST",
    "HILL_STOCHASTIC",
    "HILL_RANDOM_RESTART",
    "LOCAL_BEAM",
    "SIMULATED_ANNEALING",
    "AND_OR_GRAPH_SEARCH",
]

class AIVisualizerApp(tk.Tk):
    """
    Matrix Lab UI.

    Giao diện này dùng phong cách terminal xanh đen:
    - Sidebar điều khiển bên trái.
    - Board ở giữa.
    - Trace table nằm phía dưới toàn màn hình.
    """

    CELL_SIZE = 116
    GAP = 8

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
        "tile": "#15803D",
        "tile_text": "#ECFDF5",
        "blank": "#030712",
        "clean": "#052E16",
        "dust": "#422006",
        "obstacle": "#1F2937",
    }

    def __init__(self) -> None:
        super().__init__()

        self.title("Matrix Search Control")
        self.geometry("1380x850")
        self.minsize(1280, 760)
        self.configure(bg=self.COLORS["bg"])

        self.mode_var = tk.StringVar(value="8-PUZZLE")
        self.algorithm_var = tk.StringVar(value="BFS1")
        self.max_expansions_var = tk.StringVar(value="6000")
        self.max_depth_var = tk.StringVar(value="12")
        self.beam_width_var = tk.StringVar(value="3")
        self.max_restarts_var = tk.StringVar(value="8")

        self.puzzle_state: PuzzleState = PuzzleProblem.START
        self.vacuum_state: VacuumState = VacuumProblem.start_state()
        self.vacuum_initial_dirt = max(1, VacuumProblem.dirty_count(self.vacuum_state))

        self.search_result: Optional[SearchResult] = None
        self.solution_path: List[SearchNode] = []
        self.current_step = 0

        self.animation_job: Optional[str] = None
        self.is_animating = False
        self.is_searching = False
        self.result_queue: queue.Queue = queue.Queue()

        self._setup_styles()
        self._build_layout()
        self._bind_events()
        self.draw_board()
        self.update_status("SYSTEM ONLINE. Choose algorithm and execute.")

    # ========================================================
    # Styles / Layout
    # ========================================================

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
        style.configure("Panel2.TFrame", background=self.COLORS["panel_2"], relief="solid", borderwidth=1)
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
        style.map(
            "Treeview",
            background=[("selected", "#14532D")],
            foreground=[("selected", "#FFFFFF")],
        )

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text="MATRIX SEARCH CONTROL", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            root,
            text="BFS/DFS visual execution monitor for 8-Puzzle and Vacuum World",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(0, 12))

        top = ttk.Frame(root, style="Root.TFrame")
        top.pack(fill=tk.X)

        self._build_sidebar(top)

        board_panel = ttk.Frame(top, style="Panel.TFrame", padding=14)
        board_panel.pack(side=tk.LEFT, padx=(12, 12))

        self.board_title = tk.Label(
            board_panel,
            text="8-PUZZLE GRID",
            bg=self.COLORS["panel"],
            fg=self.COLORS["primary_2"],
            font=("Consolas", 16, "bold"),
        )
        self.board_title.pack(anchor=tk.W)

        self.board_canvas = tk.Canvas(
            board_panel,
            width=3 * self.CELL_SIZE + 2 * self.GAP + 24,
            height=3 * self.CELL_SIZE + 2 * self.GAP + 24,
            bg=self.COLORS["panel_2"],
            highlightthickness=1,
            highlightbackground=self.COLORS["line"],
        )
        self.board_canvas.pack(pady=(12, 0))
        self.board_canvas.bind("<Button-1>", self.on_board_click)

        self._build_status_panel(top)
        self._build_trace_panel(root)

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        side = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        side.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            side,
            text="[ CONTROL NODE ]",
            bg=self.COLORS["panel"],
            fg=self.COLORS["primary_2"],
            font=("Consolas", 13, "bold"),
        ).pack(anchor=tk.W, pady=(0, 18))

        ttk.Label(side, text="PROBLEM", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Combobox(
            side,
            textvariable=self.mode_var,
            values=["8-PUZZLE", "VACUUM"],
            state="readonly",
            width=16,
        ).pack(fill=tk.X, pady=(5, 14))

        ttk.Label(side, text="ALGORITHM", style="Panel.TLabel").pack(anchor=tk.W)
        self.algorithm_combo = ttk.Combobox(
            side,
            textvariable=self.algorithm_var,
            values=PATH_ALGORITHMS,
            state="readonly",
            width=16,
        )
        self.algorithm_combo.pack(fill=tk.X, pady=(5, 14))

        ttk.Label(side, text="MAX EXPANSIONS", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Entry(side, textvariable=self.max_expansions_var, width=16).pack(fill=tk.X, pady=(5, 14))

        ttk.Label(side, text="DEPTH LIMIT (DFS/IDS/IDA*/LOCAL)", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Entry(side, textvariable=self.max_depth_var, width=16).pack(fill=tk.X, pady=(5, 22))

        ttk.Label(side, text="BEAM WIDTH K", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Entry(side, textvariable=self.beam_width_var, width=16).pack(fill=tk.X, pady=(5, 14))

        ttk.Label(side, text="MAX RESTARTS", style="Panel.TLabel").pack(anchor=tk.W)
        ttk.Entry(side, textvariable=self.max_restarts_var, width=16).pack(fill=tk.X, pady=(5, 22))

        ttk.Button(side, text="EXECUTE", style="Run.TButton", command=self.apply_search).pack(fill=tk.X, pady=4)
        ttk.Button(side, text="HALT", style="Matrix.TButton", command=self.stop_animation).pack(fill=tk.X, pady=4)
        ttk.Button(side, text="GENERATE MAP", style="Matrix.TButton", command=self.shuffle_current_problem).pack(fill=tk.X, pady=4)
        ttk.Button(side, text="RESET", style="Matrix.TButton", command=self.reset_current_problem).pack(fill=tk.X, pady=4)

        guide = (
            "\nMANUAL INPUT\n"
            "W: UP\n"
            "A: LEFT\n"
            "S: DOWN\n"
            "D: RIGHT\n"
            "SPACE: SUCK\n"
            "CLICK: CELL ACTION"
        )
        tk.Label(
            side,
            text=guide,
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            justify=tk.LEFT,
            font=("Consolas", 9),
        ).pack(anchor=tk.W, pady=(22, 0))

        self.mode_var.trace_add("write", lambda *_: self.on_mode_changed())

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
            wraplength=360,
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
            height=12,
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
        widths = {
            "step": 60,
            "action": 90,
            "current": 150,
            "frontier_count": 80,
            "frontier": 760,
            "reached_count": 80,
            "reached": 980,
            "note": 260,
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

    def _bind_events(self) -> None:
        self.bind_all("<KeyPress>", self.on_key_press)

    # ========================================================
    # Drawing
    # ========================================================

    def draw_board(self) -> None:
        self.board_canvas.delete("all")
        if self.mode_var.get() == "8-PUZZLE":
            self.board_title.configure(text="8-PUZZLE GRID")
            self.draw_puzzle()
        else:
            self.board_title.configure(text="VACUUM GRID")
            self.draw_vacuum()
        self.update_stats()

    def draw_puzzle(self) -> None:
        offset = 12
        for index, value in enumerate(self.puzzle_state):
            row, col = divmod(index, 3)
            x1 = offset + col * (self.CELL_SIZE + self.GAP)
            y1 = offset + row * (self.CELL_SIZE + self.GAP)
            x2 = x1 + self.CELL_SIZE
            y2 = y1 + self.CELL_SIZE
            if value == 0:
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=self.COLORS["blank"], outline=self.COLORS["line"], width=2)
                self.board_canvas.create_text((x1+x2)//2, (y1+y2)//2, text="NULL", fill="#14532D", font=("Consolas", 13, "bold"))
            else:
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=self.COLORS["tile"], outline=self.COLORS["primary_2"], width=2)
                self.board_canvas.create_text((x1+x2)//2, (y1+y2)//2, text=str(value), fill=self.COLORS["tile_text"], font=("Consolas", 35, "bold"))

    def draw_vacuum(self) -> None:
        offset = 12
        pos, grid = self.vacuum_state
        for row in range(3):
            for col in range(3):
                x1 = offset + col * (self.CELL_SIZE + self.GAP)
                y1 = offset + row * (self.CELL_SIZE + self.GAP)
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                value = grid[row][col]
                if value == -1:
                    fill, label, color = self.COLORS["obstacle"], "###", self.COLORS["danger"]
                elif value == 1:
                    fill, label, color = self.COLORS["dust"], "DIRT", self.COLORS["warning"]
                else:
                    fill, label, color = self.COLORS["clean"], "000", self.COLORS["primary"]
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=self.COLORS["line"], width=2)
                self.board_canvas.create_text((x1+x2)//2, (y1+y2)//2, text=label, fill=color, font=("Consolas", 14, "bold"))

        rr, rc = pos
        cx = offset + rc * (self.CELL_SIZE + self.GAP) + self.CELL_SIZE // 2
        cy = offset + rr * (self.CELL_SIZE + self.GAP) + self.CELL_SIZE // 2
        self.board_canvas.create_oval(cx-34, cy-34, cx+34, cy+34, fill=self.COLORS["primary"], outline=self.COLORS["primary_2"], width=3)
        self.board_canvas.create_text(cx, cy, text="BOT", fill="#001B0A", font=("Consolas", 17, "bold"))

    # ========================================================
    # Status / Trace
    # ========================================================

    def update_status(self, message: str) -> None:
        self.status_label.configure(text=f"> {message}")

    def update_stats(self) -> None:
        if self.mode_var.get() == "8-PUZZLE":
            solved = PuzzleProblem.is_goal(self.puzzle_state)
            text = (
                f"MODE       : 8-PUZZLE\n"
                f"ALGORITHM  : {self.algorithm_var.get()}\n"
                f"STEP       : {self.current_step if self.solution_path else 0}\n"
                f"GOAL       : 123/456/78_\n"
                f"SOLVED     : {'TRUE' if solved else 'FALSE'}"
            )
        else:
            dirty = VacuumProblem.dirty_count(self.vacuum_state)
            obstacles = VacuumProblem.obstacle_count(self.vacuum_state)
            cleaned = max(0, self.vacuum_initial_dirt - dirty)
            text = (
                f"MODE       : VACUUM\n"
                f"ALGORITHM  : {self.algorithm_var.get()}\n"
                f"STEP       : {self.current_step if self.solution_path else 0}\n"
                f"CLEANED    : {cleaned}/{self.vacuum_initial_dirt}\n"
                f"DIRT LEFT  : {dirty}\n"
                f"OBSTACLES  : {obstacles}"
            )
        self.stats_label.configure(text=text)
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
            current_text = self.current_formatter()(node.state)
            values = (step, node.action, current_text, 0, "", 0, "", "Trace entry was not found.")
        else:
            values = (step, node.action, entry.current_text, entry.frontier_count, entry.frontier_text, entry.reached_count, entry.reached_text, entry.note)
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

    # ========================================================
    # Search / Animation
    # ========================================================

    def apply_search(self) -> None:
        if self.is_searching:
            return
        self.stop_animation()
        self.clear_trace_table()
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.update_stats()

        max_expansions = self.read_max_expansions()
        max_depth = self.read_max_depth()
        self.is_searching = True
        self.update_status("SEARCH THREAD STARTED...")

        start_state = self.current_state()
        algorithm_name = self.algorithm_var.get()
        search_function = ALGORITHMS[algorithm_name]
        search_signature = inspect.signature(search_function)

        if self.mode_var.get() == "8-PUZZLE":
            is_goal, successors, formatter = PuzzleProblem.is_goal, PuzzleProblem.successors, PuzzleProblem.format_state
        else:
            is_goal, successors, formatter = VacuumProblem.is_goal, VacuumProblem.successors, VacuumProblem.format_state

        search_kwargs = {
            "start_state": start_state,
            "is_goal": is_goal,
            "get_successors": successors,
            "formatter": formatter,
            "max_expansions": max_expansions,
            "max_depth": max_depth,
        }
        if "beam_width" in search_signature.parameters:
            search_kwargs["beam_width"] = self.read_beam_width()
        if "max_restarts" in search_signature.parameters:
            search_kwargs["max_restarts"] = self.read_max_restarts()

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
        self.update_status(f"SOLUTION FOUND: moves={len(result.path)-1}, expansions={result.expansions}.")
        self.animate_next_step()

    def animate_next_step(self) -> None:
        if not self.is_animating:
            return
        if self.current_step >= len(self.solution_path):
            self.is_animating = False
            self.current_step = max(0, len(self.solution_path)-1)
            self.update_status("GOAL STATE REACHED.")
            self.draw_board()
            return
        node = self.solution_path[self.current_step]
        self.set_current_state(node.state)
        self.draw_board()
        self.insert_trace_row_for_node(self.current_step, node)
        self.update_status("STEP 0: START" if self.current_step == 0 else f"STEP {self.current_step}: {node.action}")
        self.current_step += 1
        self.animation_job = self.after(700, self.animate_next_step)

    def stop_animation(self) -> None:
        self.is_animating = False
        if self.animation_job is not None:
            try:
                self.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            finally:
                self.animation_job = None
        if not self.is_searching:
            self.update_status("HALTED.")

    # ========================================================
    # Events / State
    # ========================================================

    def on_mode_changed(self) -> None:
        self.stop_animation()
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        self.update_status(f"MODE SWITCHED: {self.mode_var.get()}.")

    def on_key_press(self, event: tk.Event) -> None:
        key_to_action = {"w": "UP", "a": "LEFT", "s": "DOWN", "d": "RIGHT", "space": "SUCK"}
        key = event.keysym.lower()
        if key not in key_to_action:
            return
        action = key_to_action[key]
        self.stop_animation()
        if self.mode_var.get() == "8-PUZZLE":
            if action == "SUCK":
                return
            old_state = self.puzzle_state
            self.puzzle_state = PuzzleProblem.move_blank(self.puzzle_state, action)
            if self.puzzle_state != old_state:
                self.after_manual_change(f"MANUAL ACTION: {action}")
        else:
            old_state = self.vacuum_state
            self.vacuum_state = VacuumProblem.manual_action(self.vacuum_state, action)
            if self.vacuum_state != old_state:
                self.after_manual_change(f"MANUAL ACTION: {action}")

    def on_board_click(self, event: tk.Event) -> None:
        row_col = self.board_cell_at(event.x, event.y)
        if row_col is None:
            return
        row, col = row_col
        self.stop_animation()
        if self.mode_var.get() == "8-PUZZLE":
            old_state = self.puzzle_state
            self.puzzle_state = PuzzleProblem.click_move(self.puzzle_state, row, col)
            if self.puzzle_state != old_state:
                self.after_manual_change("MOUSE MOVE ACCEPTED.")
        else:
            old_state = self.vacuum_state
            self.vacuum_state = VacuumProblem.click_action(self.vacuum_state, row, col)
            if self.vacuum_state != old_state:
                self.after_manual_change("MOUSE ACTION ACCEPTED.")

    def after_manual_change(self, message: str) -> None:
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        self.update_status("GOAL STATE REACHED." if self.current_is_goal() else message)

    def board_cell_at(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        offset = 12
        for row in range(3):
            for col in range(3):
                x1 = offset + col * (self.CELL_SIZE + self.GAP)
                y1 = offset + row * (self.CELL_SIZE + self.GAP)
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return row, col
        return None

    def current_state(self) -> object:
        return self.puzzle_state if self.mode_var.get() == "8-PUZZLE" else self.vacuum_state

    def set_current_state(self, state: object) -> None:
        if self.mode_var.get() == "8-PUZZLE":
            self.puzzle_state = state
        else:
            self.vacuum_state = state

    def current_formatter(self):
        return PuzzleProblem.format_state if self.mode_var.get() == "8-PUZZLE" else VacuumProblem.format_state

    def current_is_goal(self) -> bool:
        return PuzzleProblem.is_goal(self.puzzle_state) if self.mode_var.get() == "8-PUZZLE" else VacuumProblem.is_goal(self.vacuum_state)

    def read_max_expansions(self) -> int:
        try:
            value = int(self.max_expansions_var.get())
        except ValueError:
            value = 6000
        return max(100, min(value, 50000))

    def read_max_depth(self) -> int:
        try:
            value = int(self.max_depth_var.get())
        except ValueError:
            value = 12
        return max(1, min(value, 40))

    def read_beam_width(self) -> int:
        try:
            value = int(self.beam_width_var.get())
        except ValueError:
            value = 3
        return max(1, min(value, 12))

    def read_max_restarts(self) -> int:
        try:
            value = int(self.max_restarts_var.get())
        except ValueError:
            value = 8
        return max(1, min(value, 100))

    def shuffle_current_problem(self) -> None:
        self.stop_animation()
        if self.mode_var.get() == "8-PUZZLE":
            self.puzzle_state = PuzzleProblem.random_state(shuffle_steps=10)
            self.update_status("PUZZLE RANDOMIZED.")
        else:
            self.vacuum_state = VacuumProblem.random_state()
            self.vacuum_initial_dirt = max(1, VacuumProblem.dirty_count(self.vacuum_state))
            self.update_status("VACUUM MAP GENERATED.")
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()

    def reset_current_problem(self) -> None:
        self.stop_animation()
        if self.mode_var.get() == "8-PUZZLE":
            self.puzzle_state = PuzzleProblem.START
        else:
            self.vacuum_state = VacuumProblem.start_state()
            self.vacuum_initial_dirt = max(1, VacuumProblem.dirty_count(self.vacuum_state))
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        self.update_status("RESET COMPLETE.")
