import tkinter as tk
import json
import os

# Global variables
keybinds_frame = None
root_window = None
main_container = None
back_callback = None
waiting_for_key = None
current_keybind_button = None

# Default keybinds
DEFAULT_KEYBINDS = {
    "close_window": "Delete",
    "back": "Escape",
    "play_pause": "space",
    "reset": "r",
    "move_up": "Up",
    "move_down": "Down",
    "move_left": "Left",
    "move_right": "Right",
    "zoom_in": "MouseWheel_Up",
    "zoom_out": "MouseWheel_Down",
    "jump_start": "Home",
    "jump_end": "End",
    "undo": "Control-z",
    "redo": "Control-y",
    "step_forward": "period",
    "speed_up": "plus",
    "speed_down": "minus"
}

# Current keybinds (loaded from file or defaults)
current_keybinds = DEFAULT_KEYBINDS.copy()

def load_keybinds():
    """Load keybinds from file or use defaults"""
    global current_keybinds
    if os.path.exists("keybinds.json"):
        try:
            with open("keybinds.json", "r") as f:
                loaded_keybinds = json.load(f)
                # Start with defaults and update with loaded values
                current_keybinds = DEFAULT_KEYBINDS.copy()
                current_keybinds.update(loaded_keybinds)
        except:
            current_keybinds = DEFAULT_KEYBINDS.copy()
    else:
        current_keybinds = DEFAULT_KEYBINDS.copy()

# Load keybinds on module import
load_keybinds()

def save_keybinds():
    """Save keybinds to file"""
    with open("keybinds.json", "w") as f:
        json.dump(current_keybinds, f, indent=2)

def get_keybind(action):
    """Get the current keybind for an action"""
    return current_keybinds.get(action, DEFAULT_KEYBINDS.get(action, ""))

def check_keybind(event, action):
    """Check if an event matches a keybind action"""
    bound_key = get_keybind(action)
    
    # Handle special mouse wheel cases
    if action in ["zoom_in", "zoom_out"]:
        if bound_key == "MouseWheel_Up":
            return event.delta > 0 or event.num == 4
        elif bound_key == "MouseWheel_Down":
            return event.delta < 0 or event.num == 5
    
    # Handle regular keys
    if hasattr(event, 'keysym'):
        return event.keysym == bound_key
    
    return False

def format_key(key):
    """Format key name for display"""
    if key == "space":
        return "SPACE"
    elif key == "Escape":
        return "ESC"
    elif key == "Delete":
        return "DELETE"
    elif key == "MouseWheel_Up":
        return "SCROLL UP"
    elif key == "MouseWheel_Down":
        return "SCROLL DOWN"
    elif key == "period":
        return ". (PERIOD)"
    elif key == "Control-z":
        return "CTRL+Z"
    elif key == "Control-y":
        return "CTRL+Y"
    elif key.startswith("Mouse"):
        return key.upper()
    else:
        return key.upper()

def check_for_collision(new_key, current_key_id):
    """Check if a key is already bound to another action"""
    for action_id, bound_key in current_keybinds.items():
        if action_id != current_key_id and bound_key == new_key:
            return action_id
    return None

def show_collision_error(key, conflicting_action):
    """Show error popup when key is already bound"""
    # Get display name for the conflicting action
    action_names = {
        "close_window": "Close Window",
        "back": "Back to Menu",
        "play_pause": "Play / Pause",
        "reset": "Reset",
        "move_up": "Move Up",
        "move_down": "Move Down",
        "move_left": "Move Left",
        "move_right": "Move Right",
        "zoom_in": "Zoom In",
        "zoom_out": "Zoom Out",
        "jump_start": "Jump to Start (1D)",
        "jump_end": "Jump to End (1D)",
        "undo": "Undo",
        "redo": "Redo",
        "step_forward": "Step Forward",
        "speed_up": "Speed Up",
        "speed_down": "Speed Down"
    }
    
    display_name = action_names.get(conflicting_action, conflicting_action)
    
    error = tk.Toplevel(root_window)
    error.title("Keybind Conflict")
    error.geometry("450x180")
    error.transient(root_window)
    error.grab_set()
    error.config(bg="#3c3c3c")
    
    # Center window
    error.update_idletasks()
    x = (error.winfo_screenwidth() // 2) - (error.winfo_width() // 2)
    y = (error.winfo_screenheight() // 2) - (error.winfo_height() // 2)
    error.geometry(f"+{x}+{y}")
    
    tk.Label(error, text="This key is already in use!", 
            font=("Arial", 16, "bold"), bg="#3c3c3c", fg="#ff5555").pack(pady=(20, 10))
    
    tk.Label(error, text=f"{format_key(key)} is already bound to:", 
            font=("Arial", 12), bg="#3c3c3c", fg="white").pack(pady=5)
    
    tk.Label(error, text=f'"{display_name}"', 
            font=("Arial", 12, "bold"), bg="#3c3c3c", fg="#ffaa00").pack(pady=5)
    
    tk.Label(error, text="Please unbind it first or choose a different key.", 
            font=("Arial", 10), bg="#3c3c3c", fg="#aaaaaa").pack(pady=10)
    
    tk.Button(error, text="OK", command=error.destroy, bg="#55cc55",
             fg="white", font=("Arial", 12, "bold"), width=12).pack(pady=10)

def on_key_press(event):
    """Handle key press when rebinding"""
    global waiting_for_key, current_keybind_button
    
    if waiting_for_key is None:
        return
    
    # Get the key
    new_key = event.keysym
    
    # Handle Control combinations
    if event.state & 0x4:  # Control key is pressed
        new_key = f"Control-{new_key}"
    
    # Don't allow rebinding modifier keys only
    if new_key in ["Shift_L", "Shift_R", "Control_L", "Control_R", 
                   "Alt_L", "Alt_R", "Super_L", "Super_R"]:
        return
    
    # Check for collision
    collision = check_for_collision(new_key, waiting_for_key)
    if collision:
        show_collision_error(new_key, collision)
        # Restore original keybind display
        current_keybind_button.config(
            text=f"> {format_key(current_keybinds[waiting_for_key])} <",
            bg="#8b8b8b",
            fg="white"
        )
        finish_rebind()
        return
    
    # Update keybind
    current_keybinds[waiting_for_key] = new_key
    
    # Update button
    current_keybind_button.config(
        text=f"> {format_key(new_key)} <",
        bg="#8b8b8b",
        fg="white"
    )
    
    # Save keybinds
    save_keybinds()
    
    # Clear waiting state and unbind
    finish_rebind()

def on_mouse_button(event):
    """Handle mouse button clicks when rebinding"""
    global waiting_for_key, current_keybind_button
    
    if waiting_for_key is None:
        return
    
    # Map button numbers to names
    button_map = {
        1: "Mouse1",
        2: "Mouse2",
        3: "Mouse3",
        4: "Mouse4",
        5: "Mouse5"
    }
    
    # If clicking on the keybind button itself, cancel
    if event.widget == current_keybind_button:
        # Restore original keybind display
        current_keybind_button.config(
            text=f"> {format_key(current_keybinds[waiting_for_key])} <",
            bg="#8b8b8b",
            fg="white"
        )
        finish_rebind()
        return
    
    # Otherwise, bind to this mouse button
    new_key = button_map.get(event.num, f"Mouse{event.num}")
    
    # Check for collision
    collision = check_for_collision(new_key, waiting_for_key)
    if collision:
        show_collision_error(new_key, collision)
        # Restore original keybind display
        current_keybind_button.config(
            text=f"> {format_key(current_keybinds[waiting_for_key])} <",
            bg="#8b8b8b",
            fg="white"
        )
        finish_rebind()
        return
    
    # Update keybind
    current_keybinds[waiting_for_key] = new_key
    
    # Update button
    current_keybind_button.config(
        text=f"> {format_key(new_key)} <",
        bg="#8b8b8b",
        fg="white"
    )
    
    # Save keybinds
    save_keybinds()
    
    # Clear waiting state and unbind
    finish_rebind()

def on_mouse_wheel(event):
    """Handle mouse wheel when rebinding"""
    global waiting_for_key, current_keybind_button
    
    if waiting_for_key is None:
        return
    
    # Determine scroll direction
    if event.delta > 0 or event.num == 4:
        new_key = "MouseWheel_Up"
    else:
        new_key = "MouseWheel_Down"
    
    # Check for collision
    collision = check_for_collision(new_key, waiting_for_key)
    if collision:
        show_collision_error(new_key, collision)
        # Restore original keybind display
        current_keybind_button.config(
            text=f"> {format_key(current_keybinds[waiting_for_key])} <",
            bg="#8b8b8b",
            fg="white"
        )
        finish_rebind()
        return
    
    # Update keybind
    current_keybinds[waiting_for_key] = new_key
    
    # Update button
    current_keybind_button.config(
        text=f"> {format_key(new_key)} <",
        bg="#8b8b8b",
        fg="white"
    )
    
    # Save keybinds
    save_keybinds()
    
    # Clear waiting state and unbind
    finish_rebind()

def finish_rebind():
    """Clear waiting state and restore normal bindings"""
    global waiting_for_key, current_keybind_button
    
    waiting_for_key = None
    current_keybind_button = None
    
    # Unbind rebinding events
    root_window.unbind("<Key>")
    root_window.unbind("<Button-1>")
    root_window.unbind("<Button-2>")
    root_window.unbind("<Button-3>")
    root_window.unbind("<Button-4>")
    root_window.unbind("<Button-5>")
    root_window.unbind("<MouseWheel>")
    
    # Restore normal scrolling - re-setup the whole page
    if keybinds_frame and keybinds_frame.winfo_ismapped():
        setup_in_frame(root_window, main_container, back_callback)

def start_rebind(key_id, button):
    """Start waiting for a new key press"""
    global waiting_for_key, current_keybind_button
    
    waiting_for_key = key_id
    current_keybind_button = button
    
    # Change button appearance to show it's waiting
    button.config(text="...", bg="#ffaa00", fg="black")
    
    # Unbind ALL normal inputs while rebinding
    root_window.unbind_all("<MouseWheel>")
    root_window.unbind("<Escape>")
    root_window.unbind("<Delete>")
    
    # Bind ALL input events for rebinding
    root_window.bind("<Key>", on_key_press)
    root_window.bind("<Button-1>", on_mouse_button)
    root_window.bind("<Button-2>", on_mouse_button)
    root_window.bind("<Button-3>", on_mouse_button)
    root_window.bind("<Button-4>", on_mouse_button)
    root_window.bind("<Button-5>", on_mouse_button)
    root_window.bind("<MouseWheel>", on_mouse_wheel)

def create_keybind_row(parent, display_name, key_id):
    """Create a single keybind row"""
    row_frame = tk.Frame(parent, bg="#2c2c2c")
    row_frame.pack(fill="x", padx=10, pady=4)
    
    # Action name
    label = tk.Label(row_frame, text=display_name + ":", font=("Arial", 12),
                    bg="#2c2c2c", fg="white", anchor="w", width=18)
    label.pack(side="left", padx=(10, 15))
    
    # Keybind button (Minecraft style)
    keybind_btn = tk.Button(row_frame, text=f"> {format_key(current_keybinds[key_id])} <",
                           font=("Arial", 11, "bold"), bg="#8b8b8b", fg="white",
                           width=16, height=1, relief="raised", borderwidth=3,
                           command=lambda: start_rebind(key_id, keybind_btn))
    keybind_btn.pack(side="left", padx=5)
    
    # Store reference
    keybind_btn.key_id = key_id

def reset_to_defaults():
    """Reset all keybinds to defaults"""
    global current_keybinds
    
    # Confirmation dialog
    confirm = tk.Toplevel(root_window)
    confirm.title("Reset Keybinds")
    confirm.geometry("400x150")
    confirm.transient(root_window)
    confirm.grab_set()
    confirm.config(bg="#3c3c3c")
    
    # Center window
    confirm.update_idletasks()
    x = (confirm.winfo_screenwidth() // 2) - (confirm.winfo_width() // 2)
    y = (confirm.winfo_screenheight() // 2) - (confirm.winfo_height() // 2)
    confirm.geometry(f"+{x}+{y}")
    
    tk.Label(confirm, text="Reset all keybinds to defaults?", 
            font=("Arial", 14), bg="#3c3c3c", fg="white").pack(pady=30)
    
    button_frame = tk.Frame(confirm, bg="#3c3c3c")
    button_frame.pack(pady=10)
    
    def do_reset():
        global current_keybinds
        current_keybinds = DEFAULT_KEYBINDS.copy()
        save_keybinds()
        confirm.destroy()
        # Refresh the keybinds page
        setup_in_frame(root_window, main_container, back_callback)
    
    tk.Button(button_frame, text="Yes", command=do_reset, bg="#55cc55", 
             fg="white", font=("Arial", 12, "bold"), width=10).pack(side="left", padx=5)
    tk.Button(button_frame, text="No", command=confirm.destroy, bg="#cc5555",
             fg="white", font=("Arial", 12, "bold"), width=10).pack(side="left", padx=5)

def go_back():
    """Navigate back to home screen"""
    global keybinds_frame
    if keybinds_frame:
        keybinds_frame.pack_forget()
    save_keybinds()
    
    # Rebind global keys from Home_Screen
    def close_handler(event):
        root_window.destroy()
    
    root_window.bind(f"<{get_keybind('close_window')}>", close_handler)
    
    back_callback()

def setup_in_frame(root, container, back_func):
    """Setup keybinds settings in the main container"""
    global keybinds_frame, root_window, main_container, back_callback
    
    root_window = root
    main_container = container
    back_callback = back_func
    
    load_keybinds()
    
    # Unbind global keys to prevent them working while in keybinds menu
    root.unbind(f"<{get_keybind('back')}>")
    root.unbind(f"<{get_keybind('close_window')}>")
    
    # Hide all other frames
    for widget in container.winfo_children():
        widget.pack_forget()
    
    # Create keybinds frame
    keybinds_frame = tk.Frame(container, bg="#3c3c3c")
    keybinds_frame.pack(fill="both", expand=True)
    
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    
    # Title
    title = tk.Label(keybinds_frame, text="Controls", font=("Arial", 40, "bold"), 
                     bg="#3c3c3c", fg="white")
    title.pack(pady=30)
    
    # Main content frame with scrollbar
    main_frame = tk.Frame(keybinds_frame, bg="#3c3c3c")
    main_frame.pack(fill="both", expand=True, padx=100)
    
    canvas = tk.Canvas(main_frame, bg="#3c3c3c", highlightthickness=0)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#3c3c3c")
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Enable mousewheel scrolling (will be disabled during rebinding)
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Container for all category boxes
    categories_container = tk.Frame(scrollable_frame, bg="#3c3c3c")
    categories_container.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Keybind categories arranged in 2x2 grid
    categories = [
        ("Global Controls", [
            ("Close Window", "close_window"),
            ("Back to Menu", "back")
        ]),
        ("Simulation", [
            ("Play / Pause", "play_pause"),
            ("Reset", "reset"),
            ("Undo", "undo"),
            ("Redo", "redo"),
            ("Step Forward", "step_forward"),
            ("Speed Up", "speed_up"),
            ("Speed Down", "speed_down")
        ]),
        ("Navigation", [
            ("Move Up", "move_up"),
            ("Move Down", "move_down"),
            ("Move Left", "move_left"),
            ("Move Right", "move_right")
        ]),
        ("View Controls", [
            ("Zoom In", "zoom_in"),
            ("Zoom Out", "zoom_out"),
            ("Jump to Start", "jump_start"),
            ("Jump to End", "jump_end")
        ])
    ]
    
    # Create 2x2 grid of category boxes
    # Top row: Global Controls + Simulation
    top_row = tk.Frame(categories_container, bg="#3c3c3c")
    top_row.pack(fill="x", pady=5)
    
    # Bottom row: Navigation + View Controls
    bottom_row = tk.Frame(categories_container, bg="#3c3c3c")
    bottom_row.pack(fill="x", pady=5)
    
    # Category 0: Global Controls (top-left)
    category_frame_0 = tk.Frame(top_row, bg="#2c2c2c", relief="ridge", borderwidth=2)
    category_frame_0.pack(side="left", fill="both", expand=True, padx=5)
    
    header_0 = tk.Label(category_frame_0, text=categories[0][0], font=("Arial", 20, "bold"),
                     bg="#2c2c2c", fg="white")
    header_0.pack(fill="x", padx=10, pady=10)
    
    for display_name, key_id in categories[0][1]:
        create_keybind_row(category_frame_0, display_name, key_id)
    
    # Add padding to match height
    tk.Frame(category_frame_0, bg="#2c2c2c", height=10).pack()
    
    # Category 1: Simulation (top-right)
    category_frame_1 = tk.Frame(top_row, bg="#2c2c2c", relief="ridge", borderwidth=2)
    category_frame_1.pack(side="left", fill="both", expand=True, padx=5)
    
    header_1 = tk.Label(category_frame_1, text=categories[1][0], font=("Arial", 20, "bold"),
                     bg="#2c2c2c", fg="white")
    header_1.pack(fill="x", padx=10, pady=10)
    
    for display_name, key_id in categories[1][1]:
        create_keybind_row(category_frame_1, display_name, key_id)
    
    # Add padding to match height
    tk.Frame(category_frame_1, bg="#2c2c2c", height=10).pack()
    
    # Category 2: Navigation (bottom-left)
    category_frame_2 = tk.Frame(bottom_row, bg="#2c2c2c", relief="ridge", borderwidth=2)
    category_frame_2.pack(side="left", fill="both", expand=True, padx=5)
    
    header_2 = tk.Label(category_frame_2, text=categories[2][0], font=("Arial", 20, "bold"),
                     bg="#2c2c2c", fg="white")
    header_2.pack(fill="x", padx=10, pady=10)
    
    for display_name, key_id in categories[2][1]:
        create_keybind_row(category_frame_2, display_name, key_id)
    
    # Category 3: View Controls (bottom-right)
    category_frame_3 = tk.Frame(bottom_row, bg="#2c2c2c", relief="ridge", borderwidth=2)
    category_frame_3.pack(side="left", fill="both", expand=True, padx=5)
    
    header_3 = tk.Label(category_frame_3, text=categories[3][0], font=("Arial", 20, "bold"),
                     bg="#2c2c2c", fg="white")
    header_3.pack(fill="x", padx=10, pady=10)
    
    for display_name, key_id in categories[3][1]:
        create_keybind_row(category_frame_3, display_name, key_id)
    
    # Bottom buttons frame
    bottom_frame = tk.Frame(keybinds_frame, bg="#3c3c3c")
    bottom_frame.pack(fill="x", pady=20)
    
    # Reset to defaults button
    reset_btn = tk.Button(bottom_frame, text="Reset to Defaults", 
                         command=reset_to_defaults, bg="#cc5555", fg="white",
                         font=("Arial", 14, "bold"), width=20, height=2)
    reset_btn.pack(side="left", padx=(width//2 - 250, 20))
    
    # Done button
    done_btn = tk.Button(bottom_frame, text="Done", command=go_back,
                        bg="#55cc55", fg="white", font=("Arial", 14, "bold"),
                        width=20, height=2)
    done_btn.pack(side="left", padx=20)