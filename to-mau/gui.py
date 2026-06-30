# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import scrolledtext, ttk
from backtracking import backtracking_search
from forward_checking import forward_checking_search
from ac3 import ac3_search
from min_conflicts import min_conflicts_search

# HCMC Data
DISTRICTS = ['CC', 'HM', 'Q12', 'GV', 'BT', 'TD', 'PN', 'TB', 'TP', 'BTan', 'Q1', 'Q3', 'Q10', 'Q11', 'Q5', 'Q6', 'Q4', 'Q8', 'Q7', 'BC', 'NB', 'CG']

NAMES = {
    'CC': 'Củ Chi',
    'HM': 'Hóc Môn',
    'Q12': 'Quận 12',
    'GV': 'Gò Vấp',
    'BT': 'Bình Thạnh',
    'TD': 'Thủ Đức',
    'PN': 'Phú Nhuận',
    'TB': 'Tân Bình',
    'TP': 'Tân Phú',
    'BTan': 'Bình Tân',
    'Q1': 'Quận 1',
    'Q3': 'Quận 3',
    'Q10': 'Quận 10',
    'Q11': 'Quận 11',
    'Q5': 'Quận 5',
    'Q6': 'Quận 6',
    'Q4': 'Quận 4',
    'Q8': 'Quận 8',
    'Q7': 'Quận 7',
    'BC': 'Bình Chánh',
    'NB': 'Nhà Bè',
    'CG': 'Cần Giờ'
}

COORDS = {
    'CC': (150, 70),
    'HM': (210, 140),
    'Q12': (300, 190),
    'GV': (360, 230),
    'BT': (450, 240),
    'TD': (560, 200),
    'PN': (390, 280),
    'TB': (300, 280),
    'TP': (230, 310),
    'BTan': (160, 370),
    'Q3': (360, 330),
    'Q10': (310, 340),
    'Q11': (260, 350),
    'Q1': (420, 330),
    'Q5': (310, 400),
    'Q6': (230, 410),
    'Q4': (440, 390),
    'Q8': (290, 470),
    'Q7': (490, 460),
    'BC': (130, 470),
    'NB': (500, 560),
    'CG': (580, 640)
}

NEIGHBORS = {
    'CC': ['HM'],
    'HM': ['CC', 'BC', 'Q12', 'BTan'],
    'Q12': ['HM', 'GV', 'BT', 'TD', 'BTan', 'TB'],
    'GV': ['Q12', 'BT', 'PN', 'TB'],
    'BT': ['Q12', 'GV', 'PN', 'Q1', 'TD'],
    'TD': ['Q12', 'BT', 'Q1', 'Q4', 'Q7'],
    'PN': ['GV', 'BT', 'TB', 'Q3', 'Q1'],
    'TB': ['Q12', 'GV', 'PN', 'Q3', 'Q10', 'TP'],
    'TP': ['TB', 'Q11', 'Q6', 'BTan'],
    'BTan': ['HM', 'Q12', 'TP', 'Q6', 'Q8', 'BC'],
    'Q1': ['BT', 'PN', 'Q3', 'Q5', 'Q4', 'TD'],
    'Q3': ['PN', 'Q1', 'Q10'],
    'Q10': ['Q3', 'TB', 'Q11', 'Q5'],
    'Q11': ['Q10', 'TB', 'TP', 'Q6', 'Q5'],
    'Q5': ['Q10', 'Q11', 'Q1', 'Q4', 'Q8', 'Q6'],
    'Q6': ['Q11', 'TP', 'BTan', 'Q5', 'Q8'],
    'Q4': ['Q1', 'Q5', 'Q8', 'Q7', 'TD'],
    'Q8': ['BTan', 'BC', 'Q6', 'Q5', 'Q4', 'Q7'],
    'Q7': ['Q8', 'Q4', 'TD', 'NB', 'BC'],
    'BC': ['HM', 'BTan', 'Q8', 'Q7', 'NB'],
    'NB': ['BC', 'Q7', 'CG'],
    'CG': ['NB']
}

COLORS_LIST = ['Đỏ', 'Xanh lá', 'Xanh dương', 'Vàng']
COLOR_MAP = {
    'Đỏ': '#FF4D4D',
    'Xanh lá': '#2ECC71',
    'Xanh dương': '#3498DB',
    'Vàng': '#F1C40F',
    None: '#FFFFFF'
}

class MapColoringGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualizer: Graph Coloring - Ho Chi Minh City (22 Districts)")
        self.root.geometry("1200x750")
        self.root.configure(bg="#F2F4F4")

        # Variables for animation control
        self.current_generator = None
        self.animation_job = None
        self.delay_ms = 500
        
        # State variables
        self.node_colors = {v: None for v in DISTRICTS}
        self.node_domains = {v: list(COLORS_LIST) for v in DISTRICTS}
        self.active_node = None
        
        # Setup UI components
        self.setup_ui()
        self.draw_graph()

    def setup_ui(self):
        # Left Panel (Map Visualizer)
        left_panel = tk.Frame(self.root, bg="#FFFFFF", bd=2, relief=tk.GROOVE)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_left = tk.Label(left_panel, text="BẢN ĐỒ QUAN HỆ GIÁP RANH TP. HỒ CHÍ MINH", 
                              font=("Arial", 12, "bold"), fg="#2C3E50", bg="#FFFFFF")
        title_left.pack(pady=10)

        self.canvas = tk.Canvas(left_panel, bg="#FFFFFF", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right Panel (Algorithm Control & Logs)
        right_panel = tk.Frame(self.root, bg="#F2F4F4", width=450)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        right_panel.pack_propagate(False)

        # Algorithm Controls
        control_frame = tk.LabelFrame(right_panel, text="ĐIỀU KHIỂN THUẬT TOÁN", 
                                      font=("Arial", 10, "bold"), fg="#2C3E50", bg="#FFFFFF", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        lbl_desc = tk.Label(control_frame, text="Số màu mặc định: 4 màu (Đỏ, Xanh lá, Xanh dương, Vàng)", 
                            font=("Arial", 9, "italic"), fg="#7F8C8D", bg="#FFFFFF")
        lbl_desc.pack(anchor=tk.W, pady=(0, 10))

        # Buttons frame
        btn_frame1 = tk.Frame(control_frame, bg="#FFFFFF")
        btn_frame1.pack(fill=tk.X, pady=(0, 5))

        self.btn_backtracking = tk.Button(btn_frame1, text="Backtracking", bg="#E67E22", fg="white", 
                                          font=("Arial", 9, "bold"), relief=tk.FLAT, height=2,
                                          command=self.start_backtracking)
        self.btn_backtracking.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        self.btn_forward = tk.Button(btn_frame1, text="Forward Checking", bg="#3498DB", fg="white", 
                                     font=("Arial", 9, "bold"), relief=tk.FLAT, height=2,
                                     command=self.start_forward_checking)
        self.btn_forward.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        self.btn_ac3 = tk.Button(btn_frame1, text="AC-3 (MAC)", bg="#9B59B6", fg="white", 
                                 font=("Arial", 9, "bold"), relief=tk.FLAT, height=2,
                                 command=self.start_ac3)
        self.btn_ac3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        btn_frame2 = tk.Frame(control_frame, bg="#FFFFFF")
        btn_frame2.pack(fill=tk.X)

        self.btn_min_conflicts = tk.Button(btn_frame2, text="Min-Conflicts", bg="#1ABC9C", fg="white", 
                                            font=("Arial", 9, "bold"), relief=tk.FLAT, height=2,
                                            command=self.start_min_conflicts)
        self.btn_min_conflicts.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        self.btn_stop = tk.Button(btn_frame2, text="Dừng / Reset", bg="#E74C3C", fg="white", 
                                  font=("Arial", 9, "bold"), relief=tk.FLAT, height=2,
                                  command=self.stop_and_reset)
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        # Speed slider
        speed_frame = tk.Frame(control_frame, bg="#FFFFFF", pady=5)
        speed_frame.pack(fill=tk.X, pady=(10, 0))
        lbl_speed = tk.Label(speed_frame, text="Tốc độ trễ (ms):", font=("Arial", 9), bg="#FFFFFF")
        lbl_speed.pack(side=tk.LEFT)
        self.speed_slider = tk.Scale(speed_frame, from_=50, to=2000, orient=tk.HORIZONTAL, bg="#FFFFFF",
                                     highlightthickness=0, command=self.update_speed)
        self.speed_slider.set(self.delay_ms)
        self.speed_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Logs Frame
        log_frame = tk.LabelFrame(right_panel, text="NHẬT KÝ THUẬT TOÁN", 
                                  font=("Arial", 10, "bold"), fg="#2C3E50", bg="#FFFFFF", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, bg="#1E1E1E", fg="#FFFFFF", 
                                                 font=("Consolas", 10), insertbackground="white", bd=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for beautiful logging
        self.log_text.tag_config("step", foreground="#3498DB", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("try", foreground="#E67E22")
        self.log_text.tag_config("conflict", foreground="#E74C3C", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("assign", foreground="#2ECC71")
        self.log_text.tag_config("prune", foreground="#F1C40F")
        self.log_text.tag_config("backtrack", foreground="#95A5A6", font=("Consolas", 10, "italic"))
        self.log_text.tag_config("success", foreground="#2ECC71", font=("Consolas", 11, "bold"))
        self.log_text.tag_config("normal", foreground="#FFFFFF")

    def update_speed(self, val):
        self.delay_ms = int(val)

    def log(self, message, tag="normal"):
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)

    def draw_graph(self):
        self.canvas.delete("all")
        
        # Draw edges first
        drawn_edges = set()
        for u, neighbors in NEIGHBORS.items():
            for v in neighbors:
                edge = tuple(sorted([u, v]))
                if edge not in drawn_edges:
                    drawn_edges.add(edge)
                    x1, y1 = COORDS[u]
                    x2, y2 = COORDS[v]
                    self.canvas.create_line(x1, y1, x2, y2, fill="#BDC3C7", width=1.5)

        # Draw nodes
        for var in DISTRICTS:
            x, y = COORDS[var]
            color = COLOR_MAP[self.node_colors[var]]
            
            # Highlight border if it is the currently evaluated variable
            border_color = "#E74C3C" if var == self.active_node else "#2C3E50"
            border_width = 3 if var == self.active_node else 1.5

            # Draw circle
            r = 18
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=border_color, width=border_width)
            
            # Draw abbreviation text inside
            self.canvas.create_text(x, y, text=var, font=("Arial", 9, "bold"), fill="#2C3E50" if color == "#FFFFFF" else "#FFFFFF")
            
            # Draw label outside above the node
            full_name = NAMES[var]
            self.canvas.create_text(x, y - 28, text=full_name, font=("Arial", 8, "bold"), fill="#2C3E50")

            # Draw domain dots under the node
            domain = self.node_domains[var]
            dot_y = y + 25
            dot_spacing = 6
            num_dots = len(domain)
            start_x = x - ((num_dots - 1) * dot_spacing) / 2
            
            for i, col in enumerate(domain):
                dot_x = start_x + i * dot_spacing
                dot_color = COLOR_MAP[col]
                self.canvas.create_oval(dot_x - 2.5, dot_y - 2.5, dot_x + 2.5, dot_y + 2.5, fill=dot_color, outline="#7F8C8D", width=0.5)

    def stop_and_reset(self):
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        self.current_generator = None
        
        # Reset states
        self.node_colors = {v: None for v in DISTRICTS}
        self.node_domains = {v: list(COLORS_LIST) for v in DISTRICTS}
        self.active_node = None
        
        self.draw_graph()
        self.log_text.delete("1.0", tk.END)
        self.log("--- Hệ thống đã dừng và khôi phục trạng thái ban đầu ---", "normal")

    def start_backtracking(self):
        self.stop_and_reset()
        self.log("BẮT ĐẦU GIẢI BẰNG THUẬT TOÁN BACKTRACKING SEARCH...", "step")
        self.current_generator = backtracking_search(DISTRICTS, {v: list(COLORS_LIST) for v in DISTRICTS}, NEIGHBORS, NAMES)
        self.run_animation()

    def start_forward_checking(self):
        self.stop_and_reset()
        self.log("BẮT ĐẦU GIẢI BẰNG THUẬT TOÁN FORWARD CHECKING...", "step")
        self.current_generator = forward_checking_search(DISTRICTS, {v: list(COLORS_LIST) for v in DISTRICTS}, NEIGHBORS, NAMES)
        self.run_animation()

    def start_ac3(self):
        self.stop_and_reset()
        self.log("BẮT ĐẦU GIẢI BẰNG THUẬT TOÁN AC-3 (MAC)...", "step")
        self.current_generator = ac3_search(DISTRICTS, {v: list(COLORS_LIST) for v in DISTRICTS}, NEIGHBORS, NAMES)
        self.run_animation()

    def start_min_conflicts(self):
        self.stop_and_reset()
        self.log("BẮT ĐẦU GIẢI BẰNG THUẬT TOÁN MIN-CONFLICTS...", "step")
        self.current_generator = min_conflicts_search(DISTRICTS, {v: list(COLORS_LIST) for v in DISTRICTS}, NEIGHBORS, NAMES, max_steps=150)
        self.run_animation()

    def run_animation(self):
        if not self.current_generator:
            return
            
        try:
            # Get next step from the generator
            step_data = next(self.current_generator)
            
            # Parse step_data
            if len(step_data) == 5:
                # Backtracking: (step_type, assignment, current_domains, current_var, current_val, log_message)
                # wait, in backtracking.py we yielded 6 values. Let's make sure.
                # Yes, we yielded 6 values: step_type, assignment, current_domains, var, val, log_message.
                # Oh! Wait, let's look at the yield:
                # "success", assignment.copy(), {v: list(current_domains[v]) for v in variables}, None, None, "Tìm thấy lời giải thành công!"
                # (step_type, assignment, current_domains, var, val, log_message) -> 6 values!
                # Yes!
                step_type, assignment, current_domains, var, val, log_msg = step_data
            else:
                step_type, assignment, current_domains, var, val, log_msg = step_data
                
            self.active_node = var
            self.node_domains = current_domains
            
            # Map assignment to node colors
            self.node_colors = {v: None for v in DISTRICTS}
            for v, c in assignment.items():
                self.node_colors[v] = c
                
            # Log message
            tag = "normal"
            if step_type == "select_var":
                tag = "step"
            elif step_type == "try_val":
                tag = "try"
            elif step_type == "conflict":
                tag = "conflict"
            elif step_type == "assign":
                tag = "assign"
            elif step_type == "prune":
                tag = "prune"
            elif step_type == "backtrack":
                tag = "backtrack"
            elif step_type == "success":
                tag = "success"
                
            self.log(log_msg, tag)
            self.draw_graph()
            
            # Schedule next step
            self.animation_job = self.root.after(self.delay_ms, self.run_animation)
            
        except StopIteration:
            self.active_node = None
            self.draw_graph()
            self.log("--- Thuật toán đã chạy xong! ---", "normal")
            self.animation_job = None
            self.current_generator = None
