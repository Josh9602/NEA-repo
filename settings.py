"""
Settings interface for neighborhood-based cellular automata
Allows users to create custom rules and manage presets
"""

import tkinter as tk
import Settings_pannel
from rules import Rules
import shared_state
import json
import os
from functools import partial
from Spinbox_validation import validate_spinbox_integer
from Spinbox_validation import create_spinbox_fixer

# Global variables
settings_frame = None
root_window = None
main_container = None
back_callback = None
total = 0
rule_set = []
count = 0
state = []

# Toggle variables
wrapping_enabled = tk.BooleanVar(value=True)
use_sparse_grid = tk.BooleanVar(value=False)
simulation_speed = tk.IntVar(value=20)
neighborhood_type = tk.StringVar(value="moore")
neighborhood_radius = tk.IntVar(value=1)
min_pixel_size = tk.IntVar(value=1)
max_pixel_size = tk.IntVar(value=25)

def setup_in_frame(root, container, back_func):
    """Setup settings interface in main container"""
    global settings_frame, root_window, main_container, back_callback
    global canvas, frame, canvas0, frame0, scrollbar, scrollbar0, button, button0, save_text
    
    root_window = root
    main_container = container
    back_callback = back_func
    
    # Hide all other frames
    for widget in container.winfo_children():
        widget.pack_forget()
    
    # Create settings frame
    settings_frame = tk.Frame(container)
    settings_frame.pack(fill="both", expand=True)
    
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    
    # Main content frame
    content_frame = tk.Frame(settings_frame)
    content_frame.pack(fill="both", expand=True)
    
    # LEFT: Scrollable canvas for states
    canvas = tk.Canvas(content_frame, width=450, height=height-100)
    canvas.pack(side="left", fill="y", expand=False)
    scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="left", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)
    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")
    
    # MIDDLE: Toggles frame
    toggles_frame = tk.Frame(content_frame, width=300, relief="solid", borderwidth=1)
    toggles_frame.pack(side="left", fill="y", padx=10, pady=10)
    toggles_frame.pack_propagate(False)
    
    tk.Label(toggles_frame, text="Simulation Settings", font=("Arial", 14, "bold")).pack(pady=(10, 20))
    
    wrap_check = tk.Checkbutton(toggles_frame, text="Wrap grid edges", variable=wrapping_enabled, font=("Arial", 11))
    wrap_check.pack(anchor="w", padx=20, pady=5)
    
    sparse_check = tk.Checkbutton(toggles_frame, text="Use sparse grid\n(for low density)", variable=use_sparse_grid, font=("Arial", 11), justify="left")
    sparse_check.pack(anchor="w", padx=20, pady=5)
    
    tk.Label(toggles_frame, text="Simulation Speed:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(20, 5))
    speed_frame = tk.Frame(toggles_frame)
    speed_frame.pack(anchor="w", padx=20, pady=5)
    tk.Label(speed_frame, text="Fast", font=("Arial", 9)).pack(side="left")
    speed_slider = tk.Scale(speed_frame, from_=10, to=2000, orient="horizontal", variable=simulation_speed, showvalue=True, length=150, resolution=10)
    speed_slider.pack(side="left", padx=5)
    tk.Label(speed_frame, text="Slow", font=("Arial", 9)).pack(side="left")
    tk.Label(toggles_frame, text="(milliseconds per step)", font=("Arial", 8), fg="gray").pack(anchor="w", padx=20)
    
    tk.Label(toggles_frame, text="Neighborhood Type:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(20, 5))
    neighborhood_frame = tk.Frame(toggles_frame)
    neighborhood_frame.pack(anchor="w", padx=20, pady=5)
    tk.Radiobutton(neighborhood_frame, text="Moore (8 neighbors)", variable=neighborhood_type, value="moore", font=("Arial", 10)).pack(anchor="w")
    tk.Radiobutton(neighborhood_frame, text="Von Neumann (4 neighbors)", variable=neighborhood_type, value="von_neumann", font=("Arial", 10)).pack(anchor="w")
    
    tk.Label(toggles_frame, text="Neighborhood Radius:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 5))
    radius_spinbox = tk.Spinbox(toggles_frame, from_=1, to=5, textvariable=neighborhood_radius, width=10, font=("Arial", 10))
    radius_spinbox.config(validate="key", validatecommand=(root.register(lambda v: validate_spinbox_integer(v, 1, 5)), "%P"))
    radius_spinbox.bind("<FocusOut>", create_spinbox_fixer(neighborhood_radius, 1, 5, 1))
    radius_spinbox.pack(anchor="w", padx=20)
    
    tk.Label(toggles_frame, text="Min Pixel Size (Zoom Out):", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(20, 5))
    min_pixel_spinbox = tk.Spinbox(toggles_frame, from_=4, to=10, textvariable=min_pixel_size, width=10, font=("Arial", 10))
    min_pixel_spinbox.config(validate="key", validatecommand=(root.register(lambda v: validate_spinbox_integer(v, 4, 10)), "%P"))
    min_pixel_spinbox.bind("<FocusOut>", create_spinbox_fixer(min_pixel_size, 4, 10, 4))
    min_pixel_spinbox.pack(anchor="w", padx=20)
    
    tk.Label(toggles_frame, text="Max Pixel Size (Zoom In):", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 5))
    max_pixel_spinbox = tk.Spinbox(toggles_frame, from_=10, to=50, textvariable=max_pixel_size, width=10, font=("Arial", 10))
    max_pixel_spinbox.config(validate="key", validatecommand=(root.register(lambda v: validate_spinbox_integer(v, 10, 50)), "%P"))
    max_pixel_spinbox.bind("<FocusOut>", create_spinbox_fixer(max_pixel_size, 10, 50, 25))
    max_pixel_spinbox.pack(anchor="w", padx=20)
    
    # RIGHT: Save/Load section
    save_load_frame = tk.Frame(content_frame, width=300, relief="solid", borderwidth=1)
    save_load_frame.pack(side="top", fill="x", expand=False, padx=10, pady=10)
    tk.Label(save_load_frame, text="Saves", font=("Arial", 14, "bold")).pack(pady=10)
    canvas0 = tk.Canvas(save_load_frame, width=420, height=height-150)
    canvas0.pack(side="left", expand=False, padx=23)
    scrollbar0 = tk.Scrollbar(save_load_frame, orient="vertical", command=canvas0.yview)
    scrollbar0.pack(side="right", fill="y")
    canvas0.configure(yscrollcommand=scrollbar0.set)
    frame0 = tk.Frame(canvas0)
    canvas0.create_window((0, 0), window=frame0, anchor="nw")
    
    # Add states button
    button = tk.Button(frame, text="add state", width=30, command=basic.add_pannel)
    
    # Start button
    button0 = tk.Button(settings_frame, command=basic.setstart, borderwidth=0, bg="spring green", 
                       highlightthickness=0, width=15, height=3, bd=2, text="START", font=("Arial"))
    button0.place(relx=0.5, rely=0.922, anchor="c")
    
    # Save controls
    global save_name
    save_name = tk.StringVar()
    button1 = tk.Button(settings_frame, command=save, borderwidth=0, bg="spring green", 
                       highlightthickness=0, width=5, height=2, bd=2, text="SAVE", font=("Arial"))
    button1.place(relx=0.95, rely=0.942, anchor="c")
    save_text = tk.Entry(settings_frame, width=20, textvariable=save_name, font=("Arial", 20), borderwidth=5)
    save_text.place(relx=0.8, rely=0.942, anchor="c")
    
    # Bindings
    canvas.bind("<Configure>", update_scrollregion)
    canvas0.bind("<Configure>", update_scrollregion0)
    root.bind("<Escape>", go_back)
    root.bind("<MouseWheel>", scroll_handler)
    
    # Update max neighbor counts when neighborhood settings change
    neighborhood_type.trace_add("write", update_spinbox_maximums)
    neighborhood_radius.trace_add("write", update_spinbox_maximums)
    
    # Initialize with default states
    basic.add_pannel()
    basic.add_pannel()
    list_json_files()


def calculate_max_neighbors():
    """Calculate maximum possible neighbors based on type and radius"""
    radius = neighborhood_radius.get()
    n_type = neighborhood_type.get()
    if n_type == "moore":
        return ((2 * radius + 1) ** 2) - 1
    else:
        return 4 * radius

def update_spinbox_maximums(*args):
    """Update neighbor count spinboxes when neighborhood changes"""
    max_neighbors = calculate_max_neighbors()
    Settings_pannel.update_all_max_neighbors(max_neighbors)

def update_scrollregion(event=None):
    """Update scroll region for main canvas"""
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

def update_scrollregion0(event=None):
    """Update scroll region for saves canvas"""
    canvas0.update_idletasks()
    canvas0.configure(scrollregion=canvas0.bbox("all"))

def scroll_left(event):
    """Handle scrolling on left canvas"""
    top = canvas.canvasy(0)
    if event.delta > 0 and top <= 0:
        return
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def scroll_right(event):
    """Handle scrolling on right canvas"""
    top = canvas0.canvasy(0)
    if event.delta > 0 and top <= 0:
        return
    canvas0.yview_scroll(int(-1*(event.delta/120)), "units")

def scroll_handler(event):
    """Route scroll events to correct canvas based on mouse position"""
    mouse_x = root_window.winfo_pointerx() - root_window.winfo_rootx()
    canvas_left_x = canvas.winfo_rootx() - root_window.winfo_rootx()
    canvas_left_right = canvas_left_x + canvas.winfo_width()
    canvas0_x = canvas0.winfo_rootx() - root_window.winfo_rootx()
    canvas0_right = canvas0_x + canvas0.winfo_width()
    
    if canvas_left_x < mouse_x < canvas_left_right:
        scroll_left(event)
    elif canvas0_x < mouse_x < canvas0_right:
        scroll_right(event)

def update_layout():
    """Update layout after adding/removing states"""
    height_val = shared_state.shared.total + 150
    frame.configure(height=height_val, width=400)
    button.place(x=30, y=15 + shared_state.shared.total)
    update_scrollregion()

def go_back(event):
    """Return to home screen and clean up state"""
    global settings_frame, rule_set, count, state
    if settings_frame:
        settings_frame.pack_forget()
    # Clear state data to prevent issues on return
    rule_set.clear()
    count = 0
    state.clear()
    Settings_pannel.state_rule_panels.clear()
    shared_state.shared.total = 0
    back_callback()

class basic:
    """Helper class for managing state creation and simulation start"""
    
    def add_pannel():
        """Add a new state panel"""
        global rule_set, count, state
        state.append(count)
        max_neighbors = calculate_max_neighbors()
        Settings_pannel.create_new_state(frame, canvas, rule_set, state, shared_state.shared.total, max_neighbors)
        for rule in rule_set:
            rule.update_state_dropdowns()
        shared_state.shared.total += 100
        shared_state.shared.update_callback = update_layout
        update_layout()
        count += 1
        
    def setstart():
        """Validate rules and start simulation"""
        # Create mapping from state names to indices
        name_to_index = {}
        for i, name in enumerate(state):
            name_to_index[str(name)] = i
        
        # Check unique names
        if len(name_to_index) != len(state):
            show_error_popup("All state names must be unique!")
            return
        
        # Get rules
        raw_rules = [rule.get_rule() for rule in rule_set]
        
        # Convert text names to indices
        real_rules = []
        for rule in raw_rules:
            # Convert current_state
            current = str(rule["current_state"])
            current_idx = name_to_index.get(current, 0)
            
            # Convert next_state
            next_val = str(rule["next_state"])
            next_idx = name_to_index.get(next_val, rule["next_state"])
            if isinstance(next_idx, str):
                try:
                    next_idx = int(next_idx)
                except:
                    next_idx = 0
            
            converted_rule = {
                "current_state": current_idx,
                "conditions": [],
                "next_state": next_idx,
                "color": rule["color"]
            }
            
            # Convert neighbor states
            for condition in rule["conditions"]:
                neighbor = str(condition["neighbor_state"])
                neighbor_idx = name_to_index.get(neighbor, 0)
                
                converted_rule["conditions"].append({
                    "neighbor_state": neighbor_idx,
                    "operator": condition["operator"],
                    "count": condition["count"]
                })
            
            real_rules.append(converted_rule)
        
        # Validate all states have rules
        allowed = True
        for i in range(count):
            has_rule = False
            for rule in real_rules:
                if rule["next_state"] == i:
                    has_rule = True
                    break  
            if not has_rule:  
                allowed = False
                break
            
        if allowed:
            colors = {}
            for rule in real_rules:
                colors[rule["next_state"]] = rule["color"]
            
            settings_frame.pack_forget()
            
            try:
                import basic_grid
                basic_grid.setup_in_frame(
                    root_window,
                    main_container,
                    lambda: setup_in_frame(root_window, main_container, back_callback),
                    sparse_grid=use_sparse_grid.get(),
                    wrapping=wrapping_enabled.get(),
                    neighborhood_type=neighborhood_type.get(),
                    neighborhood_radius=neighborhood_radius.get(),
                    min_pixel_size=min_pixel_size.get(),
                    max_pixel_size=max_pixel_size.get()
                )
                basic_grid.change_rules(real_rules, colors)
                basic_grid.controller.automata_speed = simulation_speed.get()
                basic_grid.draw_grid()
            except Exception as e:
                print(f"Error starting simulation: {e}")
                import traceback
                traceback.print_exc()
                show_error_popup("Failed to start simulation")
        else:
            show_error_popup("Not All States Have Rules")
def load_and_start(preset_name):
    """Load preset and start simulation with error handling"""
    try:
        # Validate file exists
        file_path = f"neighbour_save/{preset_name}.json"
        if not os.path.exists(file_path):
            show_error_popup("Save file not found")
            return
        
        with open(file_path, "r") as f:
            real_rules = json.load(f)
        
        # Validate rules structure
        if not isinstance(real_rules, list) or len(real_rules) == 0:
            show_error_popup("Invalid save file format")
            return
        
        # Validate each rule has required keys
        for rule in real_rules:
            required_keys = ["current_state", "conditions", "next_state", "color"]
            if not all(key in rule for key in required_keys):
                show_error_popup("Corrupted save file")
                return
        
        colors = {}
        for rule in real_rules:
            colors[rule["next_state"]] = rule["color"]
        
        settings_frame.pack_forget()
        
        import basic_grid
        basic_grid.setup_in_frame(
            root_window,
            main_container,
            lambda: setup_in_frame(root_window, main_container, back_callback),
            sparse_grid=use_sparse_grid.get(),
            wrapping=wrapping_enabled.get(),
            neighborhood_type=neighborhood_type.get(),
            neighborhood_radius=neighborhood_radius.get(),
            min_pixel_size=min_pixel_size.get(),
            max_pixel_size=max_pixel_size.get()
        )
        basic_grid.change_rules(real_rules, colors)
        basic_grid.controller.automata_speed = simulation_speed.get()
        basic_grid.draw_grid()
        
    except json.JSONDecodeError:
        show_error_popup("Save file is corrupted")
    except Exception as e:
        print(f"Error loading preset: {e}")
        show_error_popup("Failed to load preset")

def delete_preset(preset_name):
    """Delete preset with confirmation dialog"""
    confirm_window = tk.Toplevel(root_window)
    confirm_window.title("Confirm Delete")
    confirm_window.geometry("400x150")
    confirm_window.transient(root_window)
    confirm_window.grab_set()
    
    # Center window
    confirm_window.update_idletasks()
    x = (confirm_window.winfo_screenwidth() // 2) - (confirm_window.winfo_width() // 2)
    y = (confirm_window.winfo_screenheight() // 2) - (confirm_window.winfo_height() // 2)
    confirm_window.geometry(f"+{x}+{y}")
    
    tk.Label(confirm_window, text=f"Are you sure you want to delete:", font=("Arial", 12)).pack(pady=(20, 5))
    tk.Label(confirm_window, text=f'"{preset_name}"?', font=("Arial", 12, "bold")).pack(pady=(0, 20))
    
    button_frame = tk.Frame(confirm_window)
    button_frame.pack(pady=10)
    
    def confirm_delete():
        try:
            file_path = f"neighbour_save/{preset_name}.json"
            if os.path.exists(file_path):
                os.remove(file_path)
                list_json_files()
                confirm_window.destroy()
            else:
                show_error_popup("File not found")
                confirm_window.destroy()
        except PermissionError:
            show_error_popup("Permission denied")
            confirm_window.destroy()
        except Exception as e:
            print(f"Delete error: {e}")
            show_error_popup("Failed to delete file")
            confirm_window.destroy()
    
    def cancel_delete():
        confirm_window.destroy()
    
    tk.Button(button_frame, text="Delete", command=confirm_delete, bg="red", fg="white", 
             font=("Arial", 11, "bold"), width=10).pack(side="left", padx=5)
    tk.Button(button_frame, text="Cancel", command=cancel_delete, bg="gray", fg="white",
             font=("Arial", 11), width=10).pack(side="left", padx=5)

def save():
    """Save current rules to JSON file with validation"""
    real_rules = [rule.get_rule() for rule in rule_set]
    
    # Validate all states have rules
    allowed = True
    for i in range(count):
        has_rule = False
        for rule in real_rules:
            if rule["next_state"] == i:
                has_rule = True
                break  
        if not has_rule:  
            allowed = False
            break
    
    if not allowed:
        show_error_popup("Not All States Have Rules")
        return
    
    # Validate save name
    name = save_name.get().strip()
    if not name:
        show_error_popup("Please enter a save name")
        return
    
    if len(name) > 100:
        show_error_popup("Save name too long (max 100 characters)")
        return
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in name for char in invalid_chars):
        show_error_popup(f"Save name cannot contain: {' '.join(invalid_chars)}")
        return
    
    try:
        # Create save directory if it doesn't exist
        if not os.path.exists("neighbour_save"):
            os.makedirs("neighbour_save")
        
        colors = {}
        for rule in real_rules:
            colors[rule["next_state"]] = rule["color"]
        
        data = real_rules
        file_path = f"neighbour_save/{name}.json"
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        list_json_files()
        
    except PermissionError:
        show_error_popup("Permission denied - cannot write to folder")
    except Exception as e:
        print(f"Save error: {e}")
        show_error_popup("Failed to save file")

def show_error_popup(message):
    """Display error message popup"""
    popup = tk.Toplevel(root_window)
    popup.overrideredirect(True)
    label = tk.Label(popup, text=message, font=("arial", 20), bg="#ffcccc", padx=20, pady=20)
    label.pack()
    
    # Center popup
    popup.update_idletasks()
    x = (root_window.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (root_window.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")
    
    popup.after(2000, popup.destroy)

def list_json_files():
    """List all saved presets sorted by modification time"""
    for widget in frame0.winfo_children():
        widget.destroy()
    
    folder = "neighbour_save"
    
    try:
        # Create folder if it doesn't exist
        if not os.path.exists(folder):
            os.makedirs(folder)
            return
        
        files = [f for f in os.listdir(folder) if f.endswith(".json")]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
        json_files = [f[:-5] for f in files]
        
        for i, preset_name in enumerate(json_files):
            preset_frame = tk.Frame(frame0)
            preset_frame.pack(pady=5, padx=5, fill="x")
            
            load_btn = tk.Button(preset_frame, text=preset_name, width=18, height=1, font=("Arial", 23), 
                               bd=2, bg="lightblue", command=partial(load_and_start, preset_name))
            load_btn.pack(side="left", padx=2)
            
            delete_btn = tk.Button(preset_frame, text="X", width=4, height=2, font=("Arial", 14, "bold"), 
                                  bd=2, bg="red", fg="white", command=partial(delete_preset, preset_name))
            delete_btn.pack(side="left")
        
        update_scrollregion0()
        
    except Exception as e:
        print(f"Error listing files: {e}")