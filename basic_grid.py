"""
basic_grid.py - Neighborhood-Based Cellular Automata Implementation
WITH: Undo/Redo, Bounding Box Optimization, Drag Painting/Panning, Cell Glow

Implements neighborhood-based cellular automata (like Conway's Game of Life, Brian's Brain)
with optimized grid evolution using NumPy vectorization and interactive visualization using PIL.
"""

import tkinter as tk
from tkinter import filedialog
from collections import Counter
import operator
import random
import numpy as np
import time
import keybind_settings
import pickle
from Spinbox_validation import validate_spinbox_integer
from Spinbox_validation import create_spinbox_fixer

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("ERROR: PIL/Pillow is required!")
    print("Install with: pip install Pillow")
    exit()

# Global variables
grid_frame = None
root = None
canvas = None
renderer = None
controller = None
automaton = None
density_control = None
back_callback = None
TOTAL_ROWS = 0
TOTAL_COLS = 0
use_sparse_grid = False
wrapping_enabled = True
min_cell_size = 4
max_cell_size = 25


class GenerationHistory:
    """Store last 5 grid states for undo/redo"""
    
    def __init__(self, max_history=5):
        self.history = []
        self.max_history = max_history
        self.current_index = -1
    
    def save_state(self, grid):
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        self.history.append(grid.copy())
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index = len(self.history) - 1
        else:
            self.current_index = len(self.history) - 1
    
    def can_undo(self):
        return self.current_index > 0
    
    def can_redo(self):
        return self.current_index < len(self.history) - 1
    
    def undo(self):
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index].copy()
        return None
    
    def redo(self):
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index].copy()
        return None
    
    def clear(self):
        self.history = []
        self.current_index = -1


class Rule:
    """Single rule defining state transition based on neighbor conditions"""
    
    def __init__(self, current_state, conditions, next_state, color):
        self.current_state = current_state
        self.conditions = conditions
        self.next_state = next_state
        self.color = color
    
    def applies_to(self, state, neighbor_counts):
        if self.current_state != state:
            return False
        
        rel_operators = {"=": operator.eq, "!=": operator.ne, "<": operator.lt, 
                        "<=": operator.le, ">": operator.gt, ">=": operator.ge}
        
        for condition in self.conditions:
            neighbor_count = neighbor_counts[condition["neighbor_state"]]
            op = rel_operators[condition["operator"]]
            if not op(neighbor_count, condition["count"]):
                return False
        return True


class RuleSet:
    """Collection of rules defining complete automaton behavior"""
    
    def __init__(self):
        self.rules = []
        self.state_colors = {0: "#ffffff", 1: "#808080"}
        self.state_rgb = {}
        self._update_rgb()
    
    def _update_rgb(self):
        self.state_rgb = {}
        for state, hex_color in self.state_colors.items():
            hex_color = hex_color.lstrip('#')
            self.state_rgb[state] = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def add_rule(self, rule):
        self.rules.append(rule)
        self.state_colors[rule.next_state] = rule.color
        self._update_rgb()
    
    def apply_rules(self, current_state, neighbor_counts):
        for rule in self.rules:
            if rule.applies_to(current_state, neighbor_counts):
                return rule.next_state
        return current_state
    
    def get_color(self, state):
        return self.state_colors.get(state, "#ffffff")
    
    def get_rgb(self, state):
        return self.state_rgb.get(state, (255, 255, 255))
    
    def set_default_rules(self):
        """Set Conway's Game of Life rules"""
        self.rules = [Rule(1, [{"neighbor_state": 1, "operator": "<", "count": 2}], 0, "#ffffff"),
                      Rule(1, [{"neighbor_state": 1, "operator": ">", "count": 3}], 0, "#ffffff"),
                      Rule(0, [{"neighbor_state": 1, "operator": "=", "count": 3}], 1, "#808080")]
        self._update_rgb()
    
    def change_rules(self, rules, colors):
        self.rules = []
        self.state_colors = colors
        for rule_dict in rules:
            rule = Rule(rule_dict["current_state"], rule_dict["conditions"], 
                       rule_dict["next_state"], rule_dict["color"])
            self.add_rule(rule)


class CellularAutomaton:
    """Core automaton logic using NumPy for performance"""
    
    def __init__(self, width, height, ruleset, use_sparse=False, wrapping=True, 
                 neighborhood_type="moore", neighborhood_radius=1):
        self.width = width
        self.height = height
        self.ruleset = ruleset
        self.use_sparse = use_sparse
        self.wrapping = wrapping
        self.neighborhood_type = neighborhood_type
        self.neighborhood_radius = neighborhood_radius
        self.generation = 0
        
        self.grid = np.zeros((height, width), dtype=np.int8)
        self.previous_grid = None
        
        # Undo/Redo
        self.history = GenerationHistory(max_history=5)
        self.history.save_state(self.grid)
        
        self._create_kernel()
    
    def _create_kernel(self):
        size = 2 * self.neighborhood_radius + 1
        
        if self.neighborhood_type == "moore":
            self.kernel = np.ones((size, size), dtype=np.int8)
            self.kernel[self.neighborhood_radius, self.neighborhood_radius] = 0
        else:
            self.kernel = np.zeros((size, size), dtype=np.int8)
            center = self.neighborhood_radius
            for i in range(size):
                for j in range(size):
                    manhattan_dist = abs(i - center) + abs(j - center)
                    if 0 < manhattan_dist <= self.neighborhood_radius:
                        self.kernel[i, j] = 1
    
    def get_max_neighbors(self):
        if self.neighborhood_type == "moore":
            return ((2 * self.neighborhood_radius + 1) ** 2) - 1
        else:
            return 4 * self.neighborhood_radius
    
    def get_cell(self, row, col):
        if 0 <= row < self.height and 0 <= col < self.width:
            return int(self.grid[row, col])
        return 0
    
    def set_cell(self, row, col, state):
        if 0 <= row < self.height and 0 <= col < self.width:
            self.grid[row, col] = state
    
    def toggle_cell(self, row, col):
        if 0 <= row < self.height and 0 <= col < self.width and controller.toggleable():
            num_states = len(self.ruleset.state_colors)
            current = int(self.grid[row, col])
            self.grid[row, col] = (current + 1) % num_states
    
    def get_active_bounding_box(self):
        """Calculate bounding box containing all non-zero cells"""
        non_zero = np.argwhere(self.grid != 0)
        
        if len(non_zero) == 0:
            return None
        
        min_row = max(0, non_zero[:, 0].min() - self.neighborhood_radius - 1)
        max_row = min(self.height - 1, non_zero[:, 0].max() + self.neighborhood_radius + 1)
        min_col = max(0, non_zero[:, 1].min() - self.neighborhood_radius - 1)
        max_col = min(self.width - 1, non_zero[:, 1].max() + self.neighborhood_radius + 1)
        
        return (min_row, max_row, min_col, max_col)
    
    def evolve(self):
        """Execute one generation using vectorized NumPy operations"""
        self.previous_grid = self.grid.copy()
        
        states = list(self.ruleset.state_colors.keys())
        
        neighbor_counts = {}
        for state in states:
            state_mask = (self.grid == state).astype(np.int8)
            neighbor_counts[state] = self._convolve2d(state_mask, self.kernel)
        
        new_grid = self.grid.copy()
        
        for rule in self.ruleset.rules:
            current_state_mask = (self.grid == rule.current_state)
            conditions_met = np.ones_like(self.grid, dtype=bool)
            
            for condition in rule.conditions:
                neighbor_state = condition["neighbor_state"]
                operator_str = condition["operator"]
                count = condition["count"]
                
                neighbor_count_array = neighbor_counts[neighbor_state]
                
                if operator_str == "=":
                    conditions_met &= (neighbor_count_array == count)
                elif operator_str == "!=":
                    conditions_met &= (neighbor_count_array != count)
                elif operator_str == "<":
                    conditions_met &= (neighbor_count_array < count)
                elif operator_str == "<=":
                    conditions_met &= (neighbor_count_array <= count)
                elif operator_str == ">":
                    conditions_met &= (neighbor_count_array > count)
                elif operator_str == ">=":
                    conditions_met &= (neighbor_count_array >= count)
            
            rule_applies = current_state_mask & conditions_met
            new_grid[rule_applies] = rule.next_state
        
        self.grid = new_grid
        self.generation += 1
        self.history.save_state(self.grid)
    
    def evolve_with_bounding_box(self):
        """Evolve only the active region - massive speedup for sparse patterns"""
        bbox = self.get_active_bounding_box()
        
        if bbox is None:
            self.generation += 1
            self.history.save_state(self.grid)
            return
        
        min_row, max_row, min_col, max_col = bbox
        
        # Extract region WITH PADDING for neighbor counting
        pad = self.neighborhood_radius
        padded_min_row = max(0, min_row - pad)
        padded_max_row = min(self.height - 1, max_row + pad)
        padded_min_col = max(0, min_col - pad)
        padded_max_col = min(self.width - 1, max_col + pad)
        
        padded_grid = self.grid[padded_min_row:padded_max_row+1, padded_min_col:padded_max_col+1].copy()
        
        states = list(self.ruleset.state_colors.keys())
        
        # USE FAST CONVOLUTION on padded region
        neighbor_counts = {}
        for state in states:
            state_mask = (padded_grid == state).astype(np.int8)
            # This uses the FAST np.roll method
            padded_neighbors = self._convolve2d(state_mask, self.kernel)
            # Extract just the active region from padded result
            active_start_row = min_row - padded_min_row
            active_end_row = active_start_row + (max_row - min_row + 1)
            active_start_col = min_col - padded_min_col
            active_end_col = active_start_col + (max_col - min_col + 1)
            neighbor_counts[state] = padded_neighbors[active_start_row:active_end_row, active_start_col:active_end_col]
        
        active_grid = self.grid[min_row:max_row+1, min_col:max_col+1].copy()
        
        new_active_grid = active_grid.copy()
        
        for rule in self.ruleset.rules:
            current_state_mask = (active_grid == rule.current_state)
            conditions_met = np.ones_like(active_grid, dtype=bool)
            
            for condition in rule.conditions:
                neighbor_state = condition["neighbor_state"]
                operator_str = condition["operator"]
                count = condition["count"]
                
                neighbor_count_array = neighbor_counts[neighbor_state]
                
                if operator_str == "=":
                    conditions_met &= (neighbor_count_array == count)
                elif operator_str == "!=":
                    conditions_met &= (neighbor_count_array != count)
                elif operator_str == "<":
                    conditions_met &= (neighbor_count_array < count)
                elif operator_str == "<=":
                    conditions_met &= (neighbor_count_array <= count)
                elif operator_str == ">":
                    conditions_met &= (neighbor_count_array > count)
                elif operator_str == ">=":
                    conditions_met &= (neighbor_count_array >= count)
            
            rule_applies = current_state_mask & conditions_met
            new_active_grid[rule_applies] = rule.next_state
        
        self.grid[min_row:max_row+1, min_col:max_col+1] = new_active_grid
        self.generation += 1
        self.history.save_state(self.grid)
    
    def _convolve2d(self, array, kernel):
        """Fast convolution using np.roll"""
        result = np.zeros_like(array)
        for dy in range(-self.neighborhood_radius, self.neighborhood_radius + 1):
            for dx in range(-self.neighborhood_radius, self.neighborhood_radius + 1):
                if kernel[dy + self.neighborhood_radius, dx + self.neighborhood_radius] == 1:
                    result += np.roll(np.roll(array, dy, axis=0), dx, axis=1)
        return result
    
    def reset(self):
        self.grid = np.zeros((self.height, self.width), dtype=np.int8)
        self.generation = 0
        self.history.clear()
        self.history.save_state(self.grid)


class AutomatonRenderer:
    """Handles all rendering using PIL for performance"""
    
    def __init__(self, canvas, automaton):
        self.canvas = canvas
        self.automaton = automaton
        self.cell_size = max_cell_size
        self.view_row = 0
        self.view_col = 0
        self.visible_rows = 0
        self.visible_cols = 0
        self.grid_image = None
        self.photo = None
        self.canvas_image_id = None
        
        # Drag state
        self.is_dragging_left = False
        self.is_dragging_right = False
        self.last_drag_cell = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_view_row = 0
        self.drag_start_view_col = 0
        
        self._update_view_dimensions()

    def _update_view_dimensions(self):
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        self.visible_rows = canvas_height // self.cell_size + 1
        self.visible_cols = canvas_width // self.cell_size + 1

    def draw_grid(self):
        if not self.canvas.winfo_exists():
            return
            
        visible_width = self.visible_cols * self.cell_size
        visible_height = self.visible_rows * self.cell_size
        
        self.grid_image = Image.new('RGB', (visible_width, visible_height), (255, 255, 255))
        draw = ImageDraw.Draw(self.grid_image)
        
        for r in range(self.view_row, min(self.view_row + self.visible_rows, self.automaton.height)):
            for c in range(self.view_col, min(self.view_col + self.visible_cols, self.automaton.width)):
                x = (c - self.view_col) * self.cell_size
                y = (r - self.view_row) * self.cell_size
                
                cell_state = self.automaton.get_cell(r, c)
                cell_color = self.automaton.ruleset.get_rgb(cell_state)
                
                x1, y1 = x, y
                x2, y2 = x + self.cell_size, y + self.cell_size
                
                draw.rectangle([x1, y1, x2, y2], fill=cell_color, outline=cell_color)
        
        self.canvas.update_idletasks()
        
        if self.canvas_image_id:
            self.canvas.delete(self.canvas_image_id)
            self.canvas_image_id = None
        
        self.photo = ImageTk.PhotoImage(self.grid_image)
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
    
    def toggle_cell(self, event):
        """Handle left click - start painting"""
        if not controller.toggleable():
            return
        
        row = self.view_row + int(event.y // self.cell_size)
        col = self.view_col + int(event.x // self.cell_size)
        
        if 0 <= row < self.automaton.height and 0 <= col < self.automaton.width:
            self.automaton.toggle_cell(row, col)
            self.last_drag_cell = (row, col)
            self.is_dragging_left = True
            self.draw_grid()
    
    def on_left_drag(self, event):
        """Handle left click + drag - paint cells"""
        if not self.is_dragging_left or not controller.toggleable():
            return
        
        row = self.view_row + int(event.y // self.cell_size)
        col = self.view_col + int(event.x // self.cell_size)
        
        if (row, col) != self.last_drag_cell:
            if 0 <= row < self.automaton.height and 0 <= col < self.automaton.width:
                self.automaton.toggle_cell(row, col)
                self.last_drag_cell = (row, col)
                self.draw_grid()
    
    def on_left_release(self, event):
        """Handle left click release - stop painting"""
        self.is_dragging_left = False
        self.last_drag_cell = None
    
    def on_right_press(self, event):
        """Handle right click - start panning"""
        self.is_dragging_right = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.drag_start_view_row = self.view_row
        self.drag_start_view_col = self.view_col
    
    def on_right_drag(self, event):
        """Handle right click + drag - pan viewport"""
        if not self.is_dragging_right:
            return
        
        dx_pixels = event.x - self.drag_start_x
        dy_pixels = event.y - self.drag_start_y
        
        dx_cells = int(-dx_pixels // self.cell_size)
        dy_cells = int(-dy_pixels // self.cell_size)
        
        new_view_row = self.drag_start_view_row + dy_cells
        new_view_col = self.drag_start_view_col + dx_cells
        
        self.view_row = max(0, min(self.automaton.height - self.visible_rows, new_view_row))
        self.view_col = max(0, min(self.automaton.width - self.visible_cols, new_view_col))
        
        self.draw_grid()
    
    def on_right_release(self, event):
        """Handle right click release - stop panning"""
        self.is_dragging_right = False
    
    def zoom(self, event):
        center_row = self.view_row + self.visible_rows // 2
        center_col = self.view_col + self.visible_cols // 2
        
        zoom_out = False
        zoom_in = False
        
        if keybind_settings.check_keybind(event, "zoom_out"):
            zoom_out = True
        elif keybind_settings.check_keybind(event, "zoom_in"):
            zoom_in = True
        
        if zoom_out:
            if self.cell_size > min_cell_size:
                self.cell_size -= 3
                if self.cell_size < min_cell_size:
                    self.cell_size = min_cell_size
        elif zoom_in:
            if self.cell_size < max_cell_size:
                self.cell_size += 3
                if self.cell_size > max_cell_size:
                    self.cell_size = max_cell_size
        
        self._update_view_dimensions()
        
        self.view_row = max(0, min(self.automaton.height - self.visible_rows, center_row - self.visible_rows // 2))
        self.view_col = max(0, min(self.automaton.width - self.visible_cols, center_col - self.visible_cols // 2))
        self.draw_grid()
    
    def move(self, event):
        up_key = keybind_settings.get_keybind('move_up')
        down_key = keybind_settings.get_keybind('move_down')
        left_key = keybind_settings.get_keybind('move_left')
        right_key = keybind_settings.get_keybind('move_right')
        
        if event.keysym == up_key:
            self.view_row = max(0, self.view_row - 1)
        elif event.keysym == down_key:
            self.view_row = min(self.automaton.height - self.visible_rows, self.view_row + 1)
        elif event.keysym == left_key:
            self.view_col = max(0, self.view_col - 1)
        elif event.keysym == right_key:
            self.view_col = min(self.automaton.width - self.visible_cols, self.view_col + 1)
        self.draw_grid()
        
    def center_view(self):
        self.view_row = max(0, (self.automaton.height - self.visible_rows) // 2)
        self.view_col = max(0, (self.automaton.width - self.visible_cols) // 2)


class AutomatonController:
    """Manages simulation playback and timing"""
    
    def __init__(self, automaton, renderer, root):
        self.automaton = automaton
        self.renderer = renderer
        self.root = root
        self.automata = False
        self.toggle = True
        self.automata_speed = 250
        self.speed_label = None
        self.speed_label_id = None
    
    def play(self):
        self.toggle = False
        self.automata = True
        
        def step():
            if self.automata:
                start_time = time.time()
                
                self.neighbours_optimized()
                
                elapsed = time.time() - start_time
                target_delay_sec = self.automata_speed / 1000.0
                
                remaining = max(1, int((target_delay_sec - elapsed) * 1000))
                
                self.root.after(remaining, step)
        
        step()
    
    def pause(self):
        self.toggle = True
        self.automata = False
    
    def onoff(self, event):
        if self.automata:
            self.pause()
        else:
            self.play()
    
    def reset(self, event):
        apply_current_density()
        if density_control:
            density_control.reset_generation()
            density_control.update_counts()
        self.renderer.draw_grid()    
        self.pause()
    
    def neighbours_optimized(self):
        """Use bounding box optimization if beneficial"""
        bbox = self.automaton.get_active_bounding_box()
        
        if bbox is None:
            return
        
        min_row, max_row, min_col, max_col = bbox
        bbox_area = (max_row - min_row + 1) * (max_col - min_col + 1)
        total_area = self.automaton.height * self.automaton.width
        
        # Use bounding box ONLY if active region is less than 20% of total grid
        # Above 20%, the overhead isn't worth it
        if bbox_area < total_area * 0.2:
            self.automaton.evolve_with_bounding_box()
        else:
            # Use regular fast evolution for larger patterns
            self.automaton.evolve()
        
        self.renderer.draw_grid()
        if density_control:
            density_control.update_generation()
            density_control.update_counts()
    
    def undo_generation(self, event=None):
        """Undo last generation"""
        if not self.automaton.history.can_undo():
            self.show_speed_notification("Cannot undo further")
            return
        
        self.pause()
        
        previous_grid = self.automaton.history.undo()
        if previous_grid is not None:
            self.automaton.grid = previous_grid
            self.automaton.generation -= 1
            self.renderer.draw_grid()
            if density_control:
                density_control.update_generation()
                density_control.update_counts()
            self.show_speed_notification(f"Undo → Gen {self.automaton.generation}")
    
    def redo_generation(self, event=None):
        """Redo undone generation"""
        if not self.automaton.history.can_redo():
            self.show_speed_notification("Cannot redo further")
            return
        
        next_grid = self.automaton.history.redo()
        if next_grid is not None:
            self.automaton.grid = next_grid
            self.automaton.generation += 1
            self.renderer.draw_grid()
            if density_control:
                density_control.update_generation()
                density_control.update_counts()
            self.show_speed_notification(f"Redo → Gen {self.automaton.generation}")
    
    def increase_speed(self):
        self.automata_speed = max(10, self.automata_speed - 20)
        self.show_speed_notification(f"Speed: {self.automata_speed}ms")
    
    def decrease_speed(self):
        self.automata_speed = min(2000, self.automata_speed + 20)
        self.show_speed_notification(f"Speed: {self.automata_speed}ms")
    
    def step_forward(self):
        if not self.automata:
            self.neighbours_optimized()
            self.show_speed_notification("Stepped +1 generation")
    
    def show_speed_notification(self, message):
        if hasattr(self, 'speed_label_id') and self.speed_label_id:
            self.renderer.canvas.delete(self.speed_label_id)
        
        canvas_width = self.renderer.canvas.winfo_width()
        self.speed_label_id = self.renderer.canvas.create_text(
            canvas_width // 2, 30,
            text=message,
            font=("Arial", 16, "bold"),
            fill="white",
            tags="speed_notification"
        )
        
        bbox = self.renderer.canvas.bbox(self.speed_label_id)
        if bbox:
            bg_id = self.renderer.canvas.create_rectangle(
                bbox[0] - 10, bbox[1] - 5,
                bbox[2] + 10, bbox[3] + 5,
                fill="black", outline="white", width=2,
                tags="speed_notification"
            )
            self.renderer.canvas.tag_lower(bg_id, self.speed_label_id)
        
        def remove_notification():
            self.renderer.canvas.delete("speed_notification")
            self.speed_label_id = None
        
        self.root.after(1000, remove_notification)
        
    def toggleable(self):
        return self.toggle


class DensityControl:
    """Side panel for generation counter, state statistics, and density control"""
    
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
        
        sep1 = tk.Frame(self.top_frame, height=2, bg="#cccccc")
        sep1.pack(fill="x", pady=5)
        
        title = tk.Label(self.top_frame, text="Density Control", font=("Arial", 10, "bold"), bg="#f0f0f0")
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
        
        self.state_entries = {}
        self.state_count_labels = {}
        
        self.buttons_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.buttons_frame.pack(fill="x", pady=10)
        
        apply_btn = tk.Button(self.buttons_frame, text="Apply & Reset", command=self.apply_density, 
                             bg="#4CAF50", fg="white", font=("Arial", 9, "bold"))
        apply_btn.pack(pady=5, fill="x", padx=10)
        
        clear_btn = tk.Button(self.buttons_frame, text="Clear All", command=self.clear_grid,
                             bg="#f44336", fg="white", font=("Arial", 9, "bold"))
        clear_btn.pack(fill="x", padx=10, pady=(2, 5))
        
        save_btn = tk.Button(self.buttons_frame, text="Save Grid State", command=self.save_grid_state,
                            bg="#2196F3", fg="white", font=("Arial", 9, "bold"))
        save_btn.pack(fill="x", padx=10, pady=(5, 2))
        
        load_btn = tk.Button(self.buttons_frame, text="Load Grid State", command=self.load_grid_state,
                            bg="#FF9800", fg="white", font=("Arial", 9, "bold"))
        load_btn.pack(fill="x", padx=10, pady=(2, 5))
        
        self.max_screen_height = screen_height - 20
        self.panel_height = 0
        
        self.scrollable_frame.bind("<Configure>", self.update_scroll_region)
    
    def save_grid_state(self):
        if not automaton:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".gridstate",
            filetypes=[("Grid State Files", "*.gridstate"), ("All Files", "*.*")],
            title="Save Grid State"
        )
        
        if filename:
            try:
                with open(filename, 'wb') as f:
                    pickle.dump({
                        'grid': automaton.grid,
                        'generation': automaton.generation,
                        'state_colors': automaton.ruleset.state_colors
                    }, f)
                controller.show_speed_notification(f"Grid saved!")
            except Exception as e:
                controller.show_speed_notification(f"Save failed: {e}")
    
    def load_grid_state(self):
        if not automaton:
            return
        
        filename = filedialog.askopenfilename(
            filetypes=[("Grid State Files", "*.gridstate"), ("All Files", "*.*")],
            title="Load Grid State"
        )
        
        if filename:
            try:
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                
                controller.pause()
                
                automaton.grid = data['grid']
                automaton.generation = data['generation']
                
                current_states = set(automaton.ruleset.state_colors.keys())
                max_current_state = max(current_states)
                
                mask = automaton.grid > max_current_state
                automaton.grid[mask] = 0
                
                self.generation = automaton.generation
                self.generation_label.config(text=str(self.generation))
                self.update_counts()
                renderer.draw_grid()
                
                controller.show_speed_notification(f"Grid loaded!")
            except Exception as e:
                controller.show_speed_notification(f"Load failed: {e}")
    
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
        buttons_height = 180
        available_height = self.max_screen_height - top_height - buttons_height - 40
        
        height_per_state = available_height / num_states if num_states > 0 else available_height
        
        if height_per_state >= 35:
            return {'font_size': 9, 'label_font_size': 9, 'count_font_size': 9, 'pady': 3, 'entry_width': 5, 'use_scrollbar': False}
        elif height_per_state >= 25:
            return {'font_size': 8, 'label_font_size': 8, 'count_font_size': 8, 'pady': 2, 'entry_width': 4, 'use_scrollbar': False}
        elif height_per_state >= 18:
            return {'font_size': 7, 'label_font_size': 7, 'count_font_size': 7, 'pady': 1, 'entry_width': 4, 'use_scrollbar': False}
        else:
            return {'font_size': 7, 'label_font_size': 7, 'count_font_size': 7, 'pady': 1, 'entry_width': 4, 'use_scrollbar': True}
    
    def update_states(self):
        for widget in self.entries_frame.winfo_children():
            widget.destroy()
        self.state_entries.clear()
        self.state_count_labels.clear()
        
        states = sorted(automaton.ruleset.state_colors.keys())
        num_states = len(states)
        
        sizes = self.calculate_optimal_sizes(num_states)
        
        if sizes['use_scrollbar']:
            self.scrollbar.pack(side="right", fill="y")
        else:
            self.scrollbar.pack_forget()
        
        for state in states:
            state_frame = tk.Frame(self.entries_frame, bg="#f0f0f0")
            state_frame.pack(fill="x", pady=sizes['pady'], padx=5)
            
            color = automaton.ruleset.get_color(state)
            color_label = tk.Label(state_frame, text="  ", bg=color, relief="solid", borderwidth=1)
            color_label.pack(side="left", padx=2)
            
            label = tk.Label(state_frame, text=f"S{state}:", bg="#f0f0f0", width=3, font=("Arial", sizes['label_font_size']))
            label.pack(side="left")
            
            count_label = tk.Label(state_frame, text="0", bg="#f0f0f0", width=6, font=("Arial", sizes['count_font_size']), fg="#666666")
            count_label.pack(side="left", padx=2)
            self.state_count_labels[state] = count_label
            
            ratio_label = tk.Label(state_frame, text="Ratio:", bg="#f0f0f0", font=("Arial", sizes['font_size']))
            ratio_label.pack(side="left", padx=(5, 2))
            
            spinbox = tk.Spinbox(state_frame, from_=0, to=9999, width=sizes['entry_width'], font=("Arial", sizes['font_size']))
            spinbox.config(validate="key", validatecommand=(self.root.register(lambda v: validate_spinbox_integer(v, 0, 9999)), "%P"))
            spinbox.delete(0, "end")
            spinbox.insert(0, "1" if state == 0 else "0")
            spinbox.pack(side="left", padx=2)
            
            self.state_entries[state] = spinbox
        
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
        if not automaton:
            return
        
        state_counts = Counter()
        unique, counts = np.unique(automaton.grid, return_counts=True)
        state_counts = dict(zip(unique, counts))
        
        for state, label in self.state_count_labels.items():
            count = state_counts.get(state, 0)
            label.config(text=str(count))
    
    def update_generation(self):
        self.generation = automaton.generation
        self.generation_label.config(text=str(self.generation))
    
    def reset_generation(self):
        self.generation = 0
        self.generation_label.config(text="0")
    
    def get_density_ratios(self):
        ratios = {}
        for state, entry in self.state_entries.items():
            try:
                value = int(entry.get())
                ratios[state] = max(0, value)
            except ValueError:
                ratios[state] = 0
        return ratios
    
    def apply_density(self):
        was_running = controller.automata
        controller.pause()
        
        ratios = self.get_density_ratios()
        apply_density_internal(ratios)
        self.reset_generation()
        renderer.draw_grid()
        self.update_counts()
    
    def clear_grid(self):
        was_running = controller.automata
        controller.pause()
        
        automaton.reset()
        self.reset_generation()
        renderer.draw_grid()
        self.update_counts()


def setup_in_frame(root_win, container, back_func, sparse_grid=False, wrapping=True, 
                   neighborhood_type="moore", neighborhood_radius=1, min_pixel_size=4, max_pixel_size=25):
    global TOTAL_ROWS, TOTAL_COLS, automaton, renderer, controller, root, canvas
    global density_control, back_callback, grid_frame
    global use_sparse_grid, wrapping_enabled, min_cell_size, max_cell_size
    
    root = root_win
    back_callback = back_func
    use_sparse_grid = sparse_grid
    wrapping_enabled = wrapping
    min_cell_size = min_pixel_size
    max_cell_size = max_pixel_size
    
    for widget in container.winfo_children():
        widget.pack_forget()
    
    grid_frame = tk.Frame(container)
    grid_frame.pack(fill="both", expand=True)
    
    root.update()
    
    TOTAL_ROWS = root.winfo_screenheight() // min_cell_size
    TOTAL_COLS = root.winfo_screenwidth() // min_cell_size
    
    canvas = tk.Canvas(grid_frame, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
    canvas.pack(fill="both", expand=True)
    root.update()
    
    ruleset = RuleSet()
    ruleset.set_default_rules()
    
    automaton = CellularAutomaton(TOTAL_COLS, TOTAL_ROWS, ruleset, use_sparse=use_sparse_grid, 
                                  wrapping=wrapping_enabled, neighborhood_type=neighborhood_type, 
                                  neighborhood_radius=neighborhood_radius)
    renderer = AutomatonRenderer(canvas, automaton)
    renderer.center_view()
    controller = AutomatonController(automaton, renderer, root)
    
    density_control = DensityControl(root, canvas)
    
    renderer.view_row = (TOTAL_ROWS - renderer.visible_rows) // 2
    renderer.view_col = (TOTAL_COLS - renderer.visible_cols) // 2
    
    # Drag painting and panning
    canvas.bind("<Button-1>", renderer.toggle_cell)
    canvas.bind("<B1-Motion>", renderer.on_left_drag)
    canvas.bind("<ButtonRelease-1>", renderer.on_left_release)
    
    canvas.bind("<Button-3>", renderer.on_right_press)
    canvas.bind("<B3-Motion>", renderer.on_right_drag)
    canvas.bind("<ButtonRelease-3>", renderer.on_right_release)
    
    def zoom_handler(event):
        renderer.zoom(event)

    zoom_in_key = keybind_settings.get_keybind('zoom_in')
    zoom_out_key = keybind_settings.get_keybind('zoom_out')

    if zoom_in_key == "MouseWheel_Up" or zoom_out_key == "MouseWheel_Down":
        root.bind("<MouseWheel>", zoom_handler)
        root.bind("<Button-5>", zoom_handler)
        root.bind("<Button-4>", zoom_handler)

    if zoom_in_key not in ["MouseWheel_Up", "MouseWheel_Down"]:
        root.bind(f"<{zoom_in_key}>", zoom_handler)
    if zoom_out_key not in ["MouseWheel_Up", "MouseWheel_Down"]:
        root.bind(f"<{zoom_out_key}>", zoom_handler)

    def move_handler(event):
        renderer.move(event)

    root.bind(f"<{keybind_settings.get_keybind('move_up')}>", move_handler)
    root.bind(f"<{keybind_settings.get_keybind('move_down')}>", move_handler)
    root.bind(f"<{keybind_settings.get_keybind('move_left')}>", move_handler)
    root.bind(f"<{keybind_settings.get_keybind('move_right')}>", move_handler)

    root.bind(f"<{keybind_settings.get_keybind('play_pause')}>", controller.onoff)
    root.bind(f"<{keybind_settings.get_keybind('reset')}>", controller.reset)
    root.bind(f"<{keybind_settings.get_keybind('back')}>", go_back)
    
    # Undo/Redo
    root.bind("<Control-z>", controller.undo_generation)
    root.bind("<Control-y>", controller.redo_generation)
    
    root.bind("<plus>", lambda e: controller.increase_speed())
    root.bind("<equal>", lambda e: controller.increase_speed())
    root.bind("<minus>", lambda e: controller.decrease_speed())
    root.bind("<underscore>", lambda e: controller.decrease_speed())
    
    root.bind("<period>", lambda e: controller.step_forward())
    root.bind("<greater>", lambda e: controller.step_forward())

    
def draw_grid():
    global renderer, density_control
    if renderer and root:
        root.update_idletasks()
        renderer.draw_grid()
        if density_control:
            density_control.update_states()
            density_control.update_counts()


def change_rules(rules, colors):
    if automaton:
        automaton.ruleset.change_rules(rules, colors)
        if density_control:
            density_control.update_states()
            density_control.update_counts()
            
            valid_states = set(colors.keys())
            valid_states = {int(s) if isinstance(s, str) else s for s in valid_states}
            
            if valid_states:
                max_valid_state = max(valid_states)
                
                invalid_mask = automaton.grid > max_valid_state
                automaton.grid[invalid_mask] = 0
                
                if renderer:
                    renderer.draw_grid()
                    density_control.update_counts()


def apply_density_internal(density_ratios):
    total_weight = sum(density_ratios.values())
    if total_weight == 0:
        return
    
    weighted_states = []
    for state, weight in density_ratios.items():
        weighted_states.extend([state] * weight)
    
    random_states = np.random.choice(weighted_states, size=(automaton.height, automaton.width))
    automaton.grid = random_states.astype(np.int8)


def apply_current_density():
    if density_control:
        ratios = density_control.get_density_ratios()
        apply_density_internal(ratios)


def go_back(event):
    global grid_frame, controller, density_control, automaton, renderer
    
    if controller:
        controller.automata = False
        controller.pause()
    
    if grid_frame:
        grid_frame.pack_forget()
        grid_frame = None
    
    if density_control:
        try:
            density_control.toggle_button.place_forget()
            density_control.panel_frame.place_forget()
        except:
            pass
        density_control = None
    
    controller = None
    automaton = None
    renderer = None
    
    # CRITICAL FIX: Clear settings state before returning
    import settings
    import Settings_pannel
    import shared_state
    
    settings.rule_set.clear()
    settings.count = 0
    settings.state.clear()
    Settings_pannel.state_rule_panels.clear()
    shared_state.shared.total = 0
    
    back_callback()