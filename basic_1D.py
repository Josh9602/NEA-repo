"""
1D Cellular Automaton - Elementary cellular automata (Rules 0-255)
Displays evolution over time as rows stacked vertically
"""

import tkinter as tk
from collections import Counter
import operator

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("ERROR: PIL/Pillow is required!")
    print("Install with: pip install Pillow")
    exit()

# Global variables
onedim_frame = None
root = None
canvas = None
renderer = None
TOTAL_COLS = 0
CELL_SIZE = 1
VIEWPORT_HEIGHT = 600
CELLS = []
RULES = None
STATE_COLORS = {0: "#ffffff", 1: "#808080"}
STATE_RGB = {0: (255, 255, 255), 1: (128, 128, 128)}
automata = False
toggle = True
back_callback = None


class ImageHistoryRenderer:
    """Renders 1D automaton history as stacked horizontal rows"""
    
    def __init__(self):
        self.history_image = None
        self.photo = None
        self.canvas_image_id = None
        self.image_width = int(TOTAL_COLS/2) * CELL_SIZE
        self.max_rows = 5000  # Maximum rows before trimming
        self.show_grid = True
        self.start_offset = int(TOTAL_COLS / 4)  # Center view
        
    def add_generation(self, generation_data):
        """Add new generation as row at bottom of image"""
        row_height = CELL_SIZE
        row_width = self.image_width
        new_row = Image.new('RGB', (row_width, row_height), STATE_RGB[0])
        draw = ImageDraw.Draw(new_row)
        
        visible_cols = len(generation_data) // 2
        
        # Draw each cell in the row
        for i in range(visible_cols):
            col_index = self.start_offset + i
            if col_index < len(generation_data):
                cell_state = generation_data[col_index]
                
                x1 = i * CELL_SIZE
                y1 = 0
                x2 = x1 + CELL_SIZE - 1
                y2 = row_height - 1
                cell_color = STATE_RGB[cell_state]
                
                draw.rectangle([x1, y1, x2, y2], fill=cell_color)
                
                # Draw grid lines if enabled
                if self.show_grid and CELL_SIZE > 2:
                    grid_color = (0, 0, 0)
                    draw.rectangle([x1, y1, x2, y2], outline=grid_color)
        
        # Append to history image
        if self.history_image is None:
            self.history_image = new_row
        else:
            current_width, current_height = self.history_image.size
            
            # Trim old rows if exceeding max
            if current_height >= self.max_rows * CELL_SIZE:
                rows_to_remove = 100
                crop_height = rows_to_remove * CELL_SIZE
                self.history_image = self.history_image.crop((0, crop_height, current_width, current_height))
                current_height -= crop_height
            
            # Combine old history with new row
            new_height = current_height + row_height
            combined_image = Image.new('RGB', (current_width, new_height), STATE_RGB[0])
            combined_image.paste(self.history_image, (0, 0))
            combined_image.paste(new_row, (0, current_height))
            self.history_image = combined_image
            
        self._update_canvas_display()
        
    def _update_canvas_display(self):
        """Update canvas with current history image"""
        if not self.history_image:
            return
            
        self.photo = ImageTk.PhotoImage(self.history_image)
        
        if self.canvas_image_id:
            canvas.delete(self.canvas_image_id)
            
        self.canvas_image_id = canvas.create_image(0, 0, anchor="nw", image=self.photo)
        
        image_height = self.history_image.size[1]
        canvas.config(scrollregion=(0, 0, self.image_width, image_height))
        canvas.yview_moveto(1.0)  # Scroll to bottom
        
    def clear_history(self):
        """Clear all history"""
        self.history_image = None
        if self.canvas_image_id:
            canvas.delete(self.canvas_image_id)
            self.canvas_image_id = None


def setup_in_frame(root_win, container, back_func, rule_number):
    """Initialize 1D automaton interface"""
    global root, canvas, renderer, TOTAL_COLS, RULES, onedim_frame, back_callback
    
    root = root_win
    back_callback = back_func
    RULES = rule_number
    
    # Hide all other frames
    for widget in container.winfo_children():
        widget.pack_forget()
    
    # Create 1D frame
    onedim_frame = tk.Frame(container)
    onedim_frame.pack(fill="both", expand=True)
    
    TOTAL_COLS = int(root.winfo_screenwidth() * 2)
    canvas = tk.Canvas(onedim_frame, width=int(TOTAL_COLS/2) * CELL_SIZE, height=VIEWPORT_HEIGHT, 
                      scrollregion=(0, 0, int(TOTAL_COLS/2) * CELL_SIZE, 10000))
    canvas.pack(fill="both", expand=True)
    renderer = ImageHistoryRenderer()
    
    # Bind controls
    canvas.bind("<Button-1>", toggle_cell)
    root.bind("<space>", onoff)
    root.bind("<r>", reset)
    root.bind("<Home>", jump_to_start)
    root.bind("<End>", jump_to_end)
    root.bind("<Escape>", go_back)
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    # Start with initial generation
    initialize()


def get_state_color(state):
    """Get color for a state"""
    return STATE_COLORS.get(state, "#ffffff")


def toggle_cell(event):
    """Click to toggle cell state in most recent generation"""
    if not toggle or not CELLS:
        return
        
    canvas_x = canvas.canvasx(event.x)
    visible_col = int(canvas_x // CELL_SIZE)
    actual_col = visible_col + int(TOTAL_COLS / 4)
    
    if 0 <= actual_col < TOTAL_COLS:
        # Toggle cell in most recent generation
        CELLS[len(CELLS)-1][actual_col] = (CELLS[len(CELLS)-1][actual_col] + 1) % len(STATE_RGB)
        _redraw_all_history()


def _redraw_all_history():
    """Redraw entire history after edit"""
    renderer.clear_history()
    for generation in CELLS:
        renderer.add_generation(generation)


def pause():
    """Pause simulation"""
    global toggle, automata
    toggle = True
    automata = False


def play():
    """Start continuous simulation"""
    global toggle, automata
    toggle = False
    automata = True
    
    def step_loop():
        if automata:
            step()
            root.after(50, step_loop)
    
    step_loop()

def initialize(): 
    # Initialize with single cell if empty
    if not CELLS:
        new = [0 for _ in range(TOTAL_COLS)]
        new[TOTAL_COLS // 2] = 0
        CELLS.append(new)
        renderer.add_generation(new)
        return

def step():
    """
    Compute next generation using 1D rule
    
    Algorithm:
    For each cell, look at left neighbor, self, right neighbor
    Form 3-bit pattern (e.g. "101")
    Look up pattern in rule table to get next state
    """
    global RULES
    
    # Convert rule number to lookup table (first time only)
    if not isinstance(RULES, list):
        rule_set = ["111", "110", "101", "100", "011", "010", "001", "000"]
        binary = bin(int(RULES))[2:].zfill(8)
        chosen = [int(digit) for digit in binary]
        RULES = []
        for i in range(len(chosen)):
            if chosen[i]:
                RULES.append(rule_set[i])
    
    # Apply rule to get next generation
    prev = CELLS[-1]
    new = [0 for _ in range(TOTAL_COLS)]
    
    for c in range(TOTAL_COLS):
        cent = prev[c]
        left = prev[c - 1] if c > 0 else 0
        right = prev[c + 1] if c < TOTAL_COLS - 1 else 0
        
        # Form 3-bit pattern
        current = f"{left}{cent}{right}"
        
        # Check if pattern is in rule
        new_state = 0
        for rule in RULES:
            if rule == current:
                new_state = 1
                break
                
        new[c] = new_state
        
    CELLS.append(new)
    renderer.add_generation(new)


def reset(event=None):
    """Reset to initial state"""
    global CELLS
    CELLS = [[0 for _ in range(TOTAL_COLS)]]
    CELLS[0][TOTAL_COLS // 2] = 0
    renderer.clear_history()
    renderer.add_generation(CELLS[0])
    pause()


def onoff(event):
    """Toggle play/pause"""
    if automata:
        pause()
    else:
        play()


def _on_mousewheel(event):
    """Handle mouse wheel scrolling"""
    top, bottom = canvas.yview()
    
    # Prevent scrolling past edges
    if event.delta > 0 and top <= 0:
        return
    
    if event.delta < 0 and bottom >= 1.0:
        return
    
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def jump_to_start(event=None):
    """Scroll to first generation"""
    canvas.yview_moveto(0.0)


def jump_to_end(event=None):
    """Scroll to most recent generation"""
    canvas.yview_moveto(1.0)
    

def go_back(event):
    """Return to home screen"""
    global onedim_frame
    reset()
    if onedim_frame:
        onedim_frame.pack_forget()
    back_callback()