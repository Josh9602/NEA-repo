"""
Pointer-based Cellular Automaton - Similar to Langton's Ant and Turmites
WITH: Extended buffer edges, Wrapping toggle, Undo/Redo, Single-step
Pointers move around the grid, changing cell states based on rules
"""

import tkinter as tk
from collections import Counter
import operator
import random
import time
import copy

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("ERROR: PIL/Pillow is required!")
    print("Install with: pip install Pillow")
    exit()

# Global variables
pointer_frame = None
root = None
canvas = None
TOTAL_ROWS = 0
TOTAL_COLS = 0
CELLS = None
CELL_SIZE = 25
MIN_CELL_SIZE = 4
MAX_CELL_SIZE = 50
ROWS = 0
COLS = 0
row_view = 0
col_view = 0
toggle = True
automata = False
RULES = []
STATE_COLORS = {0: "#ffffff", 1: "#808080"}
STATE_RGB = {0: (255, 255, 255), 1: (128, 128, 128)}
MAX_POINTERS = 1000
pointers = []
generation = 0
density_control = None
cell_rectangles = {}
back_callback = None
show_arrows = False
simulation_speed = 100
use_sparse = False
wrapping_enabled = True


# Edge buffer for non-wrapping mode
EDGE_BUFFER = 100  # Extra cells beyond viewport on each side

# Drag state
is_dragging_left = False
is_dragging_right = False
last_drag_cell = None
drag_start_x = 0
drag_start_y = 0
drag_start_view_row = 0
drag_start_view_col = 0

# Undo/Redo history
history = []
history_index = -1
MAX_HISTORY = 5


class GridState:
    """Stores a snapshot of the grid and pointers for undo/redo"""
    
    def __init__(self, cells, pointers_list, gen):
        if use_sparse:
            self.cells = dict(cells)  # Copy dictionary
        else:
            self.cells = [row[:] for row in cells]  # Deep copy 2D array
        
        # Deep copy pointers
        self.pointers = []
        for p in pointers_list:
            new_p = Pointer(p.row, p.col, p.direction, p.user_created)
            new_p.visible = p.visible
            self.pointers.append(new_p)
        
        self.generation = gen
    
    def restore(self):
        """Restore this state to the global variables"""
        global CELLS, pointers, generation
        
        if use_sparse:
            CELLS = dict(self.cells)
        else:
            CELLS = [row[:] for row in self.cells]
        
        pointers.clear()
        for p in self.pointers:
            new_p = Pointer(p.row, p.col, p.direction, p.user_created)
            new_p.visible = p.visible
            pointers.append(new_p)
        
        generation = self.generation


def save_state():
    """Save current state to history"""
    global history, history_index
    
    # Remove any future states if we're not at the end
    if history_index < len(history) - 1:
        history = history[:history_index + 1]
    
    # Add new state
    state = GridState(CELLS, pointers, generation)
    history.append(state)
    
    # Limit history size
    if len(history) > MAX_HISTORY:
        history.pop(0)
    else:
        history_index += 1


def undo(event=None):
    """Undo to previous state"""
    global history_index
    
    if history_index <= 0:
        show_notification("Cannot undo further")
        return
    
    pause()
    
    history_index -= 1
    history[history_index].restore()
    
    if density_control:
        density_control.update_generation()
        density_control.update_counts()
    
    draw_grid()
    show_notification(f"Undo → Gen {generation}")


def redo(event=None):
    """Redo to next state"""
    global history_index
    
    if history_index >= len(history) - 1:
        show_notification("Cannot redo further")
        return
    
    pause()
    
    history_index += 1
    history[history_index].restore()
    
    if density_control:
        density_control.update_generation()
        density_control.update_counts()
    
    draw_grid()
    show_notification(f"Redo → Gen {generation}")


def single_step(event=None):
    """Execute one generation step"""
    if not automata:
        step_generation()
        show_notification(f"Step +1 → Gen {generation}")


def step_generation():
    """Execute one generation (called by both play loop and single-step)"""
    global generation
    
    for pointer in pointers:
        if pointer.visible:
            pointer.step(RULES)
    
    generation += 1
    save_state()
    
    if density_control:
        density_control.update_generation()
        density_control.update_counts()
    
    draw_grid()


def show_notification(message):
    """Show temporary notification on canvas"""
    # Clear any existing notification
    canvas.delete("notification")
    
    canvas_width = canvas.winfo_width()
    
    # Create text
    text_id = canvas.create_text(
        canvas_width // 2, 30,
        text=message,
        font=("Arial", 16, "bold"),
        fill="white",
        tags="notification"
    )
    
    # Create background rectangle
    bbox = canvas.bbox(text_id)
    if bbox:
        bg_id = canvas.create_rectangle(
            bbox[0] - 10, bbox[1] - 5,
            bbox[2] + 10, bbox[3] + 5,
            fill="black", outline="white", width=2,
            tags="notification"
        )
        canvas.tag_lower(bg_id, text_id)
    
    # Auto-remove after 1 second
    root.after(1000, lambda: canvas.delete("notification"))


def get_cell(row, col):
    """Get cell state - works for both sparse and dense"""
    if use_sparse:
        return CELLS.get((row, col), 0)
    else:
        if 0 <= row < TOTAL_ROWS and 0 <= col < TOTAL_COLS:
            return CELLS[row][col]
        return 0


def set_cell(row, col, state):
    """Set cell state - works for both sparse and dense"""
    if use_sparse:
        if state == 0:
            if (row, col) in CELLS:
                del CELLS[(row, col)]
        else:
            CELLS[(row, col)] = state
    else:
        if 0 <= row < TOTAL_ROWS and 0 <= col < TOTAL_COLS:
            CELLS[row][col] = state


def setup_in_frame(root_win, container, back_func, min_cell_size=4, max_cell_size=50, 
                   sparse_mode=False, wrapping=True):
    """Initialize pointer automaton interface"""
    global root, canvas, TOTAL_ROWS, TOTAL_COLS, CELLS, CELL_SIZE, ROWS, COLS
    global row_view, col_view, toggle, automata, pointers, density_control
    global MIN_CELL_SIZE, MAX_CELL_SIZE, back_callback, pointer_frame
    global use_sparse, wrapping_enabled, history, history_index
    
    root = root_win
    back_callback = back_func
    MIN_CELL_SIZE = min_cell_size
    MAX_CELL_SIZE = max_cell_size
    CELL_SIZE = max_cell_size
    use_sparse = sparse_mode
    wrapping_enabled = wrapping
    
    # Clear history
    history.clear()
    history_index = -1
    
    for widget in container.winfo_children():
        widget.pack_forget()
    
    pointer_frame = tk.Frame(container)
    pointer_frame.pack(fill="both", expand=True)
    
    # CALCULATE GRID SIZE WITH PROPER BUFFER
    viewport_rows = root.winfo_screenheight() // MIN_CELL_SIZE
    viewport_cols = root.winfo_screenwidth() // MIN_CELL_SIZE
    
    if wrapping_enabled:
        # Normal size for wrapping mode
        TOTAL_ROWS = viewport_rows
        TOTAL_COLS = viewport_cols
    else:
        # Extended size with buffer for non-wrapping mode
        TOTAL_ROWS = viewport_rows + (2 * EDGE_BUFFER)
        TOTAL_COLS = viewport_cols + (2 * EDGE_BUFFER)
    
    # Initialize storage based on mode
    if use_sparse:
        CELLS = {}
    else:
        CELLS = [[0 for _ in range(TOTAL_COLS)] for _ in range(TOTAL_ROWS)]

    ROWS = (root.winfo_screenheight() // CELL_SIZE) + 1
    COLS = (root.winfo_screenwidth() // CELL_SIZE) + 1

    # Set initial view position
    if wrapping_enabled:
        # Center view in grid
        row_view = (TOTAL_ROWS - ROWS) // 2
        col_view = (TOTAL_COLS - COLS) // 2
    else:
        # Start view at buffer edge (buffer is initially off-screen)
        row_view = EDGE_BUFFER
        col_view = EDGE_BUFFER

    canvas = tk.Canvas(pointer_frame, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE, bg="white")
    canvas.pack()
    
    # Place initial pointer at center of VIEWPORT (not grid)
    initial_row = row_view + ROWS // 2
    initial_col = col_view + COLS // 2
    initial_pointer = Pointer(initial_row, initial_col, user_created=True)
    pointers.append(initial_pointer)
    
    # Save initial state
    save_state()
    
    density_control = DensityControl(root, canvas)
    density_control.update_states()
    
    # Drag painting and panning bindings
    canvas.bind("<Button-1>", on_left_press)
    canvas.bind("<B1-Motion>", on_left_drag)
    canvas.bind("<ButtonRelease-1>", on_left_release)
    
    canvas.bind("<Button-3>", on_right_press)
    canvas.bind("<B3-Motion>", on_right_drag)
    canvas.bind("<ButtonRelease-3>", on_right_release)
    
    root.bind("<MouseWheel>", zoom)
    root.bind("<Button-5>", zoom)
    root.bind("<Button-4>", zoom)
    root.bind("<Up>", move)
    root.bind("<Down>", move)
    root.bind("<Left>", move)
    root.bind("<Right>", move)
    root.bind("<space>", onoff)
    root.bind("<r>", reset)
    root.bind("<Escape>", go_back)
    
    # Undo/Redo/Step bindings
    root.bind("<Control-z>", undo)
    root.bind("<Control-y>", redo)
    root.bind("<period>", single_step)
    root.bind("<greater>", single_step)


class Pointer:
    """Represents a pointer that moves around the grid"""
    
    def __init__(self, row, col, direction=0, user_created=False):
        self.row = row
        self.col = col
        self.direction = direction
        self.user_created = user_created
        self.visible = True
        self.arrow_id = None
    
    def step(self, rules):
        """Execute one step: apply rules then move forward"""
        current_state = get_cell(self.row, self.col)
        
        applicable_rules = [r for r in rules if r["current_state"] == current_state]
        
        for rule in applicable_rules:
            if rule["type"] == "rotation":
                self.direction = (self.direction + rule["angle"]) % 360
            
            elif rule["type"] == "face":
                self.direction = rule["direction"]
            
            elif rule["type"] == "movement":
                if rule["relative"]:
                    dx = rule["x"]
                    dy = rule["y"]
                    if wrapping_enabled:
                        self.row = (self.row + dy) % TOTAL_ROWS
                        self.col = (self.col + dx) % TOTAL_COLS
                    else:
                        self.row = max(0, min(TOTAL_ROWS - 1, self.row + dy))
                        self.col = max(0, min(TOTAL_COLS - 1, self.col + dx))
                else:
                    if wrapping_enabled:
                        self.row = rule["y"] % TOTAL_ROWS
                        self.col = rule["x"] % TOTAL_COLS
                    else:
                        self.row = max(0, min(TOTAL_ROWS - 1, rule["y"]))
                        self.col = max(0, min(TOTAL_COLS - 1, rule["x"]))
            
            elif rule["type"] == "clone":
                # CHECK LIMIT BEFORE CREATING
                if len(pointers) < MAX_POINTERS:
                    new_pointer = Pointer(self.row, self.col, self.direction)
                    pointers.append(new_pointer)
                else:
                    pause()
                    show_notification(f"Pointer limit reached ({MAX_POINTERS}) - simulation paused")
            
            if rule["next_state"] is not None:
                set_cell(self.row, self.col, rule["next_state"])
        
        # Move forward in current direction
        direction_map = {
            0: (0, -1),
            90: (1, 0),
            180: (0, 1),
            270: (-1, 0),
            45: (1, -1),
            135: (1, 1),
            225: (-1, 1),
            315: (-1, -1)
        }
        
        if self.direction in direction_map:
            dc, dr = direction_map[self.direction]
        else:
            closest = min(direction_map.keys(), key=lambda x: abs(x - self.direction))
            dc, dr = direction_map[closest]
        
        # Apply movement with wrapping check
        if wrapping_enabled:
            self.row = (self.row + dr) % TOTAL_ROWS
            self.col = (self.col + dc) % TOTAL_COLS
        else:
            # Clamp to grid bounds (including buffer zone)
            self.row = max(0, min(TOTAL_ROWS - 1, self.row + dr))
            self.col = max(0, min(TOTAL_COLS - 1, self.col + dc))
    
    def rotate(self):
        self.direction = (self.direction + 45) % 360
        if self.direction == 0:
            self.visible = False
    
    def draw_arrow(self):
        """Draw arrow on canvas with tag for easy deletion"""
        if not self.visible or not show_arrows:
            return
        
        if not (row_view <= self.row < row_view + ROWS and 
                col_view <= self.col < col_view + COLS):
            return
        
        x = (self.col - col_view) * CELL_SIZE + CELL_SIZE // 2
        y = (self.row - row_view) * CELL_SIZE + CELL_SIZE // 2
        
        arrow_length = min(CELL_SIZE/2, 30)
        arrow_width = arrow_length * 0.3
        
        import math
        angle_rad = math.radians(self.direction)
        
        tip_x = x + arrow_length * math.sin(angle_rad)
        tip_y = y - arrow_length * math.cos(angle_rad)
        
        base_angle1 = angle_rad + math.radians(150)
        base_angle2 = angle_rad - math.radians(150)
        
        base1_x = x + arrow_width * math.sin(base_angle1)
        base1_y = y - arrow_width * math.cos(base_angle1)
        
        base2_x = x + arrow_width * math.sin(base_angle2)
        base2_y = y - arrow_width * math.cos(base_angle2)
        
        # Draw filled triangle with tag for easy deletion
        self.arrow_id = canvas.create_polygon(
            tip_x, tip_y,
            base1_x, base1_y,
            base2_x, base2_y,
            fill="red", outline="darkred", width=2,
            tags="pointer_arrow"  # Add tag so all arrows can be deleted at once
        )


class DensityControl:
    """UI panel for monitoring state counts and managing pointers"""
    
    def __init__(self, root, canvas):
        self.root = root
        self.canvas = canvas
        self.generation = 0
        self.is_collapsed = False
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        self.toggle_button = tk.Button(root, text="<", font=("Arial", 12, "bold"), 
                                       command=self.toggle_panel, width=2, height=1,
                                       bg="#d0d0d0", relief="raised")
        self.toggle_button.place(x=screen_width-300, y=10)
        
        self.panel_frame = tk.Frame(root, bg="#f0f0f0", relief="raised", borderwidth=2)
        self.panel_frame.place(x=screen_width-280, y=10, width=270)
        
        self.top_frame = tk.Frame(self.panel_frame, bg="#f0f0f0")
        self.top_frame.pack(fill="x", side="top")
        
        gen_frame = tk.Frame(self.top_frame, bg="#f0f0f0")
        gen_frame.pack(fill="x", pady=(5, 5))
        
        gen_label = tk.Label(gen_frame, text="Generation:", font=("Arial", 11, "bold"), bg="#f0f0f0")
        gen_label.pack(side="left", padx=5)
        
        self.generation_label = tk.Label(gen_frame, text="0", font=("Arial", 11), bg="#f0f0f0", fg="#0066cc")
        self.generation_label.pack(side="left")
        
        pointer_frame = tk.Frame(self.top_frame, bg="#f0f0f0")
        pointer_frame.pack(fill="x", pady=(0, 5))
        
        pointer_label = tk.Label(pointer_frame, text="Pointers:", font=("Arial", 11, "bold"), bg="#f0f0f0")
        pointer_label.pack(side="left", padx=5)
        
        self.pointer_label = tk.Label(pointer_frame, text="1", font=("Arial", 11), bg="#f0f0f0", fg="#0066cc")
        self.pointer_label.pack(side="left")
        
        sep1 = tk.Frame(self.top_frame, height=2, bg="#cccccc")
        sep1.pack(fill="x", pady=5)
        
        title = tk.Label(self.top_frame, text="State Counter", font=("Arial", 10, "bold"), bg="#f0f0f0")
        title.pack(pady=(5, 5))
        
        self.middle_frame = tk.Frame(self.panel_frame, bg="#f0f0f0")
        self.middle_frame.pack(fill="both", expand=True, side="top")
        
        self.scroll_canvas = tk.Canvas(self.middle_frame, bg="#f0f0f0", highlightthickness=0)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        
        self.scrollbar = tk.Scrollbar(self.middle_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scroll_canvas.bind("<MouseWheel>", lambda e: "break")
        self.scrollbar.bind("<MouseWheel>", lambda e: "break")
        
        self.scrollable_frame = tk.Frame(self.scroll_canvas, bg="#f0f0f0")
        self.scroll_window = self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.entries_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.entries_frame.pack(pady=5, fill="both", expand=True)
        
        self.state_count_labels = {}
        
        self.buttons_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.buttons_frame.pack(fill="x", pady=10)
        
        clear_btn = tk.Button(self.buttons_frame, text="Clear All", command=self.clear_grid,
                             bg="#f44336", fg="white", font=("Arial", 9, "bold"))
        clear_btn.pack(fill="x", padx=10, pady=5)
        
        self.max_screen_height = screen_height - 20
        self.panel_height = 0
        
        self.scrollable_frame.bind("<Configure>", self.update_scroll_region)
    
    def toggle_panel(self):
        screen_width = self.root.winfo_screenwidth()
        
        if self.is_collapsed:
            self.panel_frame.place(x=screen_width-280, y=10, width=270, height=self.panel_height)
            self.toggle_button.place(x=screen_width-300, y=10)
            self.toggle_button.config(text="<")
            self.is_collapsed = False
        else:
            self.panel_frame.place_forget()
            self.toggle_button.place(x=screen_width-20, y=10)
            self.toggle_button.config(text=">")
            self.is_collapsed = True
    
    def calculate_optimal_sizes(self, num_states):
        self.root.update_idletasks()
        top_height = self.top_frame.winfo_reqheight()
        buttons_height = 100
        available_height = self.max_screen_height - top_height - buttons_height - 40
        
        height_per_state = available_height / num_states if num_states > 0 else available_height
        
        if height_per_state >= 35:
            return {'font_size': 9, 'label_font_size': 9, 'count_font_size': 9, 
                   'pady': 3, 'entry_width': 5, 'use_scrollbar': False}
        elif height_per_state >= 25:
            return {'font_size': 8, 'label_font_size': 8, 'count_font_size': 8, 
                   'pady': 2, 'entry_width': 4, 'use_scrollbar': False}
        elif height_per_state >= 18:
            return {'font_size': 7, 'label_font_size': 7, 'count_font_size': 7, 
                   'pady': 1, 'entry_width': 4, 'use_scrollbar': False}
        else:
            return {'font_size': 7, 'label_font_size': 7, 'count_font_size': 7, 
                   'pady': 1, 'entry_width': 4, 'use_scrollbar': True}
    
    def update_states(self):
        for widget in self.entries_frame.winfo_children():
            widget.destroy()
        self.state_count_labels.clear()
        
        states = sorted(STATE_COLORS.keys())
        num_states = len(states)
        
        sizes = self.calculate_optimal_sizes(num_states)
        
        if sizes['use_scrollbar']:
            self.scrollbar.pack(side="right", fill="y")
        else:
            self.scrollbar.pack_forget()
        
        for state in states:
            state_frame = tk.Frame(self.entries_frame, bg="#f0f0f0")
            state_frame.pack(fill="x", pady=sizes['pady'], padx=5)
            
            color = STATE_COLORS.get(state, "#ffffff")
            color_label = tk.Label(state_frame, text="  ", bg=color, relief="solid", borderwidth=1)
            color_label.pack(side="left", padx=2)
            
            label = tk.Label(state_frame, text=f"S{state}:", bg="#f0f0f0", width=3, 
                           font=("Arial", sizes['label_font_size']))
            label.pack(side="left")
            
            count_label = tk.Label(state_frame, text="0", bg="#f0f0f0", width=6, 
                                  font=("Arial", sizes['count_font_size']), fg="#666666")
            count_label.pack(side="left", padx=2)
            self.state_count_labels[state] = count_label
        
        self.resize_panel()
    
    def resize_panel(self):
        self.root.update_idletasks()
        
        top_height = self.top_frame.winfo_reqheight()
        content_height = self.scrollable_frame.winfo_reqheight()
        
        min_height = top_height + 150
        total_required = top_height + content_height + 10
        final_height = max(min_height, min(total_required, self.max_screen_height))
        
        screen_width = self.root.winfo_screenwidth()
        self.panel_frame.place(x=screen_width-280, y=10, width=270, height=final_height)
        self.panel_height = final_height
        
        self.update_scroll_region()
    
    def update_scroll_region(self, event=None):
        self.scroll_canvas.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
    
    def update_counts(self):
        state_counts = Counter()
        
        if use_sparse:
            for state in CELLS.values():
                state_counts[state] += 1
        else:
            for row in CELLS:
                for cell in row:
                    state_counts[cell] += 1
        
        for state, label in self.state_count_labels.items():
            count = state_counts.get(state, 0)
            label.config(text=str(count))
        
        self.pointer_label.config(text=str(len(pointers)))
    
    def update_generation(self):
        self.generation_label.config(text=str(generation))
    
    def reset_generation(self):
        global generation
        generation = 0
        self.generation_label.config(text="0")
    
    def clear_grid(self):
        global automata, CELLS, pointers, generation
        was_running = automata
        pause()
        
        if use_sparse:
            CELLS.clear()
        else:
            CELLS = [[0 for _ in range(TOTAL_COLS)] for _ in range(TOTAL_ROWS)]
        
        generation = 0
        
        # Place pointer at center of screen
        initial_row = row_view + ROWS // 2
        initial_col = col_view + COLS // 2
        initial_pointer = Pointer(initial_row, initial_col, user_created=True)
        pointers.clear()
        pointers.append(initial_pointer)
        
        # Reset history
        history.clear()
        history_index = -1
        save_state()
        
        self.reset_generation()
        self.update_counts()
        draw_grid()


def get_state_color(state):
    return STATE_COLORS.get(state, "#ffffff")


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def update_state_rgb():
    global STATE_RGB
    STATE_RGB = {}
    
    for state, color_hex in STATE_COLORS.items():
        STATE_RGB[state] = hex_to_rgb(color_hex)


def draw_grid():
    """TKINTER LAZY RENDERING - only draw non-zero cells as rectangles"""
    global cell_rectangles
    
    if root is None:
        return
    
    # Set background to state 0 color
    canvas.config(bg=STATE_COLORS.get(0, "#ffffff"))
    
    # Clear all existing rectangles
    for rect_id in cell_rectangles.values():
        canvas.delete(rect_id)
    cell_rectangles.clear()
    
    # CRITICAL FIX: Delete ALL arrow objects from canvas, not just tracked ones
    canvas.delete("pointer_arrow")
    
    # Also clear arrow_id references in all pointers
    for pointer in pointers:
        pointer.arrow_id = None
    
    # LAZY RENDERING: Collect only non-zero cells in viewport
    if use_sparse:
        cells_to_draw = {(r, c): s for (r, c), s in CELLS.items()
                        if row_view <= r < row_view + ROWS and col_view <= c < col_view + COLS and s != 0}
    else:
        # Dense mode: still only draw non-zero visible cells
        cells_to_draw = {}
        for r in range(row_view, min(row_view + ROWS, TOTAL_ROWS)):
            for c in range(col_view, min(col_view + COLS, TOTAL_COLS)):
                state = CELLS[r][c]
                if state != 0:
                    cells_to_draw[(r, c)] = state
    
    # Draw only non-zero cells using tkinter rectangles
    for (r, c), cell_state in cells_to_draw.items():
        x = (c - col_view) * CELL_SIZE
        y = (r - row_view) * CELL_SIZE
        
        cell_color = STATE_COLORS.get(cell_state, STATE_COLORS.get(0, "#ffffff"))
        
        x1, y1 = x, y
        x2, y2 = x + CELL_SIZE, y + CELL_SIZE
        
        # Use tkinter canvas rectangles for lazy rendering
        rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill=cell_color, outline="")
        cell_rectangles[(r, c)] = rect_id
    
    # Draw pointer arrows
    for pointer in pointers:
        pointer.draw_arrow()
    
    root.update_idletasks()


# Left click drag to paint cells
def on_left_press(event):
    """Start left drag painting"""
    global is_dragging_left, last_drag_cell
    
    if toggle == False:
        return
    
    row = row_view + int(event.y // CELL_SIZE)
    col = col_view + int(event.x // CELL_SIZE)
    
    if 0 <= row < TOTAL_ROWS and 0 <= col < TOTAL_COLS:
        num_states = len(STATE_RGB)
        current_state = get_cell(row, col)
        new_state = (current_state + 1) % num_states
        set_cell(row, col, new_state)
        
        last_drag_cell = (row, col)
        is_dragging_left = True
        
        if density_control:
            density_control.update_counts()
        draw_grid()


def on_left_drag(event):
    """Continue left drag painting"""
    global last_drag_cell
    
    if not is_dragging_left or toggle == False:
        return
    
    row = row_view + int(event.y // CELL_SIZE)
    col = col_view + int(event.x // CELL_SIZE)
    
    if (row, col) != last_drag_cell and 0 <= row < TOTAL_ROWS and 0 <= col < TOTAL_COLS:
        num_states = len(STATE_RGB)
        current_state = get_cell(row, col)
        new_state = (current_state + 1) % num_states
        set_cell(row, col, new_state)
        
        last_drag_cell = (row, col)
        
        if density_control:
            density_control.update_counts()
        draw_grid()


def on_left_release(event):
    """End left drag painting"""
    global is_dragging_left, last_drag_cell
    is_dragging_left = False
    last_drag_cell = None


# Right click drag to pan
def on_right_press(event):
    """Start right drag panning"""
    global is_dragging_right, drag_start_x, drag_start_y, drag_start_view_row, drag_start_view_col
    
    is_dragging_right = True
    drag_start_x = event.x
    drag_start_y = event.y
    drag_start_view_row = row_view
    drag_start_view_col = col_view


def on_right_drag(event):
    """Pan viewport with right drag"""
    global row_view, col_view
    
    if not is_dragging_right:
        return
    
    dx_pixels = event.x - drag_start_x
    dy_pixels = event.y - drag_start_y
    
    dx_cells = int(-dx_pixels // CELL_SIZE)
    dy_cells = int(-dy_pixels // CELL_SIZE)
    
    new_view_row = drag_start_view_row + dy_cells
    new_view_col = drag_start_view_col + dx_cells
    
    row_view = max(0, min(TOTAL_ROWS - ROWS, new_view_row))
    col_view = max(0, min(TOTAL_COLS - COLS, new_view_col))
    
    draw_grid()


def on_right_release(event):
    """End right drag - if minimal movement, treat as click"""
    global is_dragging_right
    
    dx = abs(event.x - drag_start_x)
    dy = abs(event.y - drag_start_y)
    
    # If movement was minimal, treat as click for pointer placement
    if dx < 5 and dy < 5:
        if toggle == False:
            is_dragging_right = False
            return
        
        row = row_view + int(event.y // CELL_SIZE)
        col = col_view + int(event.x // CELL_SIZE)
        
        if 0 <= row < TOTAL_ROWS and 0 <= col < TOTAL_COLS:
            existing_pointer = None
            for pointer in pointers:
                if pointer.row == row and pointer.col == col:
                    existing_pointer = pointer
                    break
            
            if existing_pointer:
                if not existing_pointer.visible:
                    existing_pointer.visible = True
                    existing_pointer.direction = 0
                else:
                    existing_pointer.rotate()
            else:
                new_pointer = Pointer(row, col, direction=0, user_created=True)
                pointers.append(new_pointer)
            
            draw_grid()
    
    is_dragging_right = False


def pause():
    global toggle, automata
    toggle = True
    automata = False


def play():
    global toggle, automata
    toggle = False
    automata = True
    
    def step_loop():
        if automata:
            start_time = time.time()
            
            step_generation()
            
            elapsed = time.time() - start_time
            target_delay_sec = simulation_speed / 1000.0
            remaining = max(1, int((target_delay_sec - elapsed) * 1000))
            
            root.after(remaining, step_loop)

    step_loop()


def zoom(event):
    global CELL_SIZE, ROWS, COLS, row_view, col_view

    center_row = row_view + ROWS // 2
    center_col = col_view + COLS // 2

    if event.num == 5 or event.delta < 0:
        if CELL_SIZE > MIN_CELL_SIZE:
            CELL_SIZE -= 3
            if CELL_SIZE < MIN_CELL_SIZE:
                CELL_SIZE = MIN_CELL_SIZE
    elif event.num == 4 or event.delta > 0:
        if CELL_SIZE < MAX_CELL_SIZE:
            CELL_SIZE += 3
            if CELL_SIZE > MAX_CELL_SIZE:
                CELL_SIZE = MAX_CELL_SIZE

    ROWS = int(root.winfo_screenheight() // CELL_SIZE) + 1
    COLS = int(root.winfo_screenwidth() // CELL_SIZE) + 1

    row_view = max(0, min(TOTAL_ROWS - ROWS, center_row - ROWS // 2))
    col_view = max(0, min(TOTAL_COLS - COLS, center_col - COLS // 2))

    canvas.config(width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE)
    draw_grid()


def move(event):
    global row_view, col_view
    
    if event.keysym == "Up":
        row_view = max(0, row_view - 1)
    elif event.keysym == "Down":
        row_view = min(TOTAL_ROWS - ROWS, row_view + 1)
    elif event.keysym == "Left":
        col_view = max(0, col_view - 1)
    elif event.keysym == "Right":
        col_view = min(TOTAL_COLS - COLS, col_view + 1)
    
    draw_grid()


def onoff(event):
    if automata:
        pause()
    else:
        play()


def reset(event):
    global CELLS, pointers, generation, history, history_index
    
    if use_sparse:
        CELLS.clear()
    else:
        CELLS = [[0 for _ in range(TOTAL_COLS)] for _ in range(TOTAL_ROWS)]
    
    generation = 0
    
    # Place pointer at center of screen
    initial_row = row_view + ROWS // 2
    initial_col = col_view + COLS // 2
    initial_pointer = Pointer(initial_row, initial_col, user_created=True)
    pointers.clear()
    pointers.append(initial_pointer)
    
    # Reset history
    history.clear()
    history_index = -1
    save_state()
    
    if density_control:
        density_control.reset_generation()
        density_control.update_counts()
    
    pause()
    draw_grid()


def change_rules(rules, colors):
    global RULES, STATE_COLORS
    
    if not rules:
        print("Warning: No rules provided")
        return
    
    try:
        RULES = rules
        STATE_COLORS = {int(k) if isinstance(k, str) else k: v for k, v in colors.items()}
        update_state_rgb()
        
        if canvas:
            canvas.config(bg=STATE_COLORS.get(0, "#ffffff"))
        
        if density_control:
            density_control.update_states()
            
    except Exception as e:
        print(f"Error changing rules: {e}")


def set_simulation_speed(speed):
    global simulation_speed
    simulation_speed = max(10, min(5000, speed))


def go_back(event):
    global pointer_frame, pointers, CELLS, generation, automata, history, history_index
    if pointer_frame:
        pointer_frame.pack_forget()
    if density_control:
        density_control.toggle_button.place_forget()
        density_control.panel_frame.place_forget()
    
    pointers.clear()
    automata = False
    generation = 0
    history.clear()
    history_index = -1
    
    if use_sparse:
        CELLS.clear()
    else:
        CELLS = None
    
    import PSettings
    import PSettings_Pannel
    import shared_state
    
    PSettings.rule_set.clear()
    PSettings.count = 0
    PSettings.state.clear()
    PSettings_Pannel.state_managers.clear()
    shared_state.shared.total = 0
    
    back_callback()