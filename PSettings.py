import tkinter as tk
import PSettings_Pannel
import shared_state
import json
import os
from functools import partial
from Spinbox_validation import validate_spinbox_integer
from Spinbox_validation import create_spinbox_fixer

# Global variables
psettings_frame = None
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
simulation_speed = tk.IntVar(value=100)
show_arrows = tk.BooleanVar(value=False)
min_pixel_size = tk.IntVar(value=4)
max_pixel_size = tk.IntVar(value=50)

def setup_in_frame(root, container, back_func):
    """Setup pointer settings interface"""
    global psettings_frame, root_window, main_container, back_callback
    global canvas, frame, canvas0, frame0, scrollbar, scrollbar0, button, button0, save_text
    
    root_window = root
    main_container = container
    back_callback = back_func
    
    for widget in container.winfo_children():
        widget.pack_forget()
    
    psettings_frame = tk.Frame(container)
    psettings_frame.pack(fill="both", expand=True)
    
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    
    content_frame = tk.Frame(psettings_frame)
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
    
    # STORAGE METHOD SECTION
    tk.Label(toggles_frame, text="Grid Storage:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
    
    sparse_check = tk.Checkbutton(toggles_frame, text="Sparse (Dictionary)", 
                                  variable=use_sparse_grid, font=("Arial", 10))
    sparse_check.pack(anchor="w", padx=40, pady=2)
    
    tk.Label(toggles_frame, text="Good for medium density", 
            font=("Arial", 8), fg="gray").pack(anchor="w", padx=60)
    
    tk.Label(toggles_frame, text="Best for very sparse patterns", 
            font=("Arial", 8), fg="gray").pack(anchor="w", padx=60)
    
    arrow_check = tk.Checkbutton(toggles_frame, text="Show pointer arrows", variable=show_arrows, font=("Arial", 11))
    arrow_check.pack(anchor="w", padx=20, pady=(20, 5))
    
    tk.Label(toggles_frame, text="Simulation Speed:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(20, 5))
    speed_frame = tk.Frame(toggles_frame)
    speed_frame.pack(anchor="w", padx=20, pady=5)
    tk.Label(speed_frame, text="Fast", font=("Arial", 9)).pack(side="left")
    speed_slider = tk.Scale(speed_frame, from_=10, to=2000, orient="horizontal", variable=simulation_speed, showvalue=True, length=150, resolution=10)
    speed_slider.pack(side="left", padx=5)
    tk.Label(speed_frame, text="Slow", font=("Arial", 9)).pack(side="left")
    tk.Label(toggles_frame, text="(milliseconds per step)", font=("Arial", 8), fg="gray").pack(anchor="w", padx=20)
    
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
    
    button = tk.Button(frame, text="add state", width=30, command=basic.add_pannel)
    
    button0 = tk.Button(psettings_frame, command=basic.setstart, borderwidth=0, bg="spring green", 
                       highlightthickness=0, width=15, height=3, bd=2, text="START", font=("Arial"))
    button0.place(relx=0.5, rely=0.922, anchor="c")
    
    global save_name
    save_name = tk.StringVar()
    button1 = tk.Button(psettings_frame, command=save, borderwidth=0, bg="spring green", 
                       highlightthickness=0, width=5, height=2, bd=2, text="SAVE", font=("Arial"))
    button1.place(relx=0.95, rely=0.942, anchor="c")
    save_text = tk.Entry(psettings_frame, width=20, textvariable=save_name, font=("Arial", 20), borderwidth=5)
    save_text.place(relx=0.8, rely=0.942, anchor="c")
    
    canvas.bind("<Configure>", update_scrollregion)
    canvas0.bind("<Configure>", update_scrollregion0)
    root.bind("<Escape>", go_back)
    root.bind("<MouseWheel>", scroll_handler)
    
    basic.add_pannel()
    basic.add_pannel()
    list_json_files()

def update_scrollregion(event=None):
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

def update_scrollregion0(event=None):
    canvas0.update_idletasks()
    canvas0.configure(scrollregion=canvas0.bbox("all"))

def scroll_left(event):
    top = canvas.canvasy(0)
    if event.delta > 0 and top <= 0:
        return
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def scroll_right(event):
    top = canvas0.canvasy(0)
    if event.delta > 0 and top <= 0:
        return
    canvas0.yview_scroll(int(-1*(event.delta/120)), "units")

def scroll_handler(event):
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
    height_val = shared_state.shared.total + 150
    frame.configure(height=height_val, width=400)
    button.place(x=30, y=15 + shared_state.shared.total)
    update_scrollregion()

def go_back(event):
    global psettings_frame, rule_set, count, state
    if psettings_frame:
        psettings_frame.pack_forget()
    rule_set.clear()
    count = 0
    state.clear()
    PSettings_Pannel.state_managers.clear()
    shared_state.shared.total = 0
    back_callback()

class basic:
    """Helper class for managing pointer state creation"""
    
    def add_pannel():
        global rule_set, count, state
        state.append(count)
        PSettings_Pannel.create_new_state(frame, canvas, rule_set, state, shared_state.shared.total)
        
        for manager in PSettings_Pannel.state_managers:
            manager.update_dropdown()
        
        shared_state.shared.total += 110
        shared_state.shared.update_callback = update_layout
        update_layout()
        count += 1
        
    def setstart():
        """Validate and start simulation"""
        all_rules = []
        
        for manager in PSettings_Pannel.state_managers:
            state_rules = manager.get_rules()
            all_rules.extend(state_rules)
        
        if not all_rules:
            show_error_popup("No Rules Defined")
            return
        
        psettings_frame.pack_forget()
        
        try:
            import basic_pointer
            
            basic_pointer.setup_in_frame(
                root_window,
                main_container,
                lambda: setup_in_frame(root_window, main_container, back_callback),
                min_cell_size=min_pixel_size.get(),
                max_cell_size=max_pixel_size.get(),
                sparse_mode=use_sparse_grid.get()
            )
            
            basic_pointer.show_arrows = show_arrows.get()
            
            colors = {}
            for manager in PSettings_Pannel.state_managers:
                colors[manager.my_state_index] = manager.state_color.get()
            
            basic_pointer.change_rules(all_rules, colors)
            basic_pointer.set_simulation_speed(simulation_speed.get())
            basic_pointer.draw_grid()
            
        except Exception as e:
            print(f"Error starting simulation: {e}")
            show_error_popup("Failed to start simulation")

def load_and_start(preset_name):
    """Load preset and start simulation with error handling"""
    try:
        file_path = f"pointer_save/{preset_name}.json"
        
        if not os.path.exists(file_path):
            show_error_popup("Save file not found")
            return
        
        with open(file_path, "r") as f:
            config = json.load(f)
        
        if not isinstance(config, dict):
            show_error_popup("Invalid save file format")
            return
        
        if "rules" not in config or "state_colors" not in config:
            show_error_popup("Corrupted save file")
            return
        
        if not isinstance(config["rules"], list) or len(config["rules"]) == 0:
            show_error_popup("No rules in save file")
            return
        
        psettings_frame.pack_forget()
        
        import basic_pointer
        
        basic_pointer.setup_in_frame(
            root_window,
            main_container,
            lambda: setup_in_frame(root_window, main_container, back_callback),
            min_cell_size=min_pixel_size.get(),
            max_cell_size=max_pixel_size.get(),
            sparse_mode=use_sparse_grid.get()
        )
        
        basic_pointer.show_arrows = show_arrows.get()
        basic_pointer.change_rules(config["rules"], config["state_colors"])
        basic_pointer.set_simulation_speed(simulation_speed.get())
        basic_pointer.draw_grid()
        
    except json.JSONDecodeError:
        show_error_popup("Save file is corrupted")
    except Exception as e:
        print(f"Error loading preset: {e}")
        show_error_popup("Failed to load preset")

def delete_preset(preset_name):
    """Delete preset with confirmation"""
    confirm_window = tk.Toplevel(root_window)
    confirm_window.title("Confirm Delete")
    confirm_window.geometry("400x150")
    confirm_window.transient(root_window)
    confirm_window.grab_set()
    
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
            file_path = f"pointer_save/{preset_name}.json"
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
            show_error_popup("Failed to delete")
            confirm_window.destroy()
    
    def cancel_delete():
        confirm_window.destroy()
    
    tk.Button(button_frame, text="Delete", command=confirm_delete, bg="red", fg="white", 
             font=("Arial", 11, "bold"), width=10).pack(side="left", padx=5)
    tk.Button(button_frame, text="Cancel", command=cancel_delete, bg="gray", fg="white",
             font=("Arial", 11), width=10).pack(side="left", padx=5)

def save():
    """Save current rules with validation"""
    all_rules = []
    
    for manager in PSettings_Pannel.state_managers:
        state_rules = manager.get_rules()
        all_rules.extend(state_rules)
    
    if not all_rules:
        show_error_popup("No Rules Defined")
        return
    
    name = save_name.get().strip()
    if not name:
        show_error_popup("Please enter a save name")
        return
    
    if len(name) > 100:
        show_error_popup("Save name too long (max 100 characters)")
        return
    
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in name for char in invalid_chars):
        show_error_popup(f"Save name cannot contain: {' '.join(invalid_chars)}")
        return
    
    try:
        if not os.path.exists("pointer_save"):
            os.makedirs("pointer_save")
        
        colors = {}
        for manager in PSettings_Pannel.state_managers:
            colors[manager.my_state_index] = manager.state_color.get()
        
        data = {
            "rules": all_rules,
            "state_colors": colors
        }
        
        file_path = f"pointer_save/{name}.json"
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
    
    popup.update_idletasks()
    x = (root_window.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (root_window.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")
    
    popup.after(2000, popup.destroy)

def list_json_files():
    """List all saved presets sorted by modification time"""
    for widget in frame0.winfo_children():
        widget.destroy()
    
    folder = "pointer_save"
    
    try:
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