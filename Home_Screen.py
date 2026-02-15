"""
Home_Screen.py
Main entry point and navigation hub for the Cellular Automata application.
"""

import tkinter as tk
from PIL import Image, ImageTk
from functools import partial
import keybind_settings
import tutorial
from Spinbox_validation import validate_spinbox_integer
from Spinbox_validation import create_spinbox_fixer

# Create single root window
root = tk.Tk()
root.state('zoomed')

# Container frame
main_container = tk.Frame(root)
main_container.pack(fill="both", expand=True)

# Home screen frame
home_frame = tk.Frame(main_container)

# Get screen dimensions
width = root.winfo_screenwidth()
height = root.winfo_screenheight()

# Main canvas
canvas = tk.Canvas(home_frame, width=width, height=height)
canvas.pack(fill="both", expand=True)

def show_home():
    """Display the home screen"""
    for widget in main_container.winfo_children():
        widget.pack_forget()
    home_frame.pack(fill="both", expand=True)


def start_basic_grid():
    """Launch Conway's Game of Life"""
    import basic_grid
    basic_grid.setup_in_frame(root, main_container, show_home)
    basic_grid.draw_grid()


def start_1d():
    """Show 1D automata rule selection"""
    slider_window = SliderWindow(root, main_container, show_home)


class SliderWindow:
    """1D cellular automaton rule selector"""
    
    def __init__(self, root, container, back_callback):
        self.root = root
        self.container = container
        self.back_callback = back_callback
        
        for widget in container.winfo_children():
            widget.pack_forget()
        
        self.slider_frame = tk.Frame(container)
        self.slider_frame.pack(fill="both", expand=True)
        
        center_frame = tk.Frame(self.slider_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(center_frame, text="Select 1D Rule (0-255)", font=("Arial", 20)).pack(pady=20)
        
        self.slider_value = tk.IntVar(value=0)
        self.slider = tk.Spinbox(center_frame, from_=0, to=255, font=("Arial", 16), width=10, textvariable=self.slider_value)
        self.slider.config(validate="key", validatecommand=(self.root.register(lambda v: validate_spinbox_integer(v, 0, 255)), "%P"))
        self.slider.bind("<FocusOut>", create_spinbox_fixer(self.slider_value, 0, 255, 0))
        self.slider.pack(pady=10)

        
        btn = tk.Button(center_frame, text="START", command=self.start_1d, font=("Arial", 16), bg="spring green", width=20, height=2)
        btn.pack(pady=20)
        
        back_btn = tk.Button(center_frame, text="BACK", command=self.go_back, font=("Arial", 14), width=20)
        back_btn.pack(pady=10)
        
        self.root.bind("<Escape>", lambda e: self.go_back())
    
    def start_1d(self):
        slider_value = self.slider.get()
        if 0 <= int(slider_value) <= 255:
            self.slider_frame.pack_forget()
            import basic_1D
            basic_1D.setup_in_frame(self.root, self.container, self.back_callback, int(slider_value))
    
    def go_back(self):
        self.slider_frame.pack_forget()
        self.back_callback()
        
def show_keybinds():
    import keybind_settings
    keybind_settings.setup_in_frame(root, main_container, show_home)


def start_settings():
    """Launch neighborhood-based automata settings"""
    import settings
    settings.setup_in_frame(root, main_container, show_home)


def start_psettings():
    """Launch pointer-based automata settings"""
    import PSettings
    PSettings.setup_in_frame(root, main_container, show_home)


def show_option_menu(event):
    """Display dropdown menu for settings options"""
    menu.post(event.x_root, event.y_root)


def option_selected(option):
    """Handle settings option selection"""
    selected_option.set(option)


def option_handler(*args):
    """Route to appropriate settings screen"""
    if selected_option.get() == "Neighbour":
        start_settings()
    elif selected_option.get() == "Pointer":
        start_psettings()
    else:  # 1D
        start_1d()


def exit_app():
    """Close the application"""
    root.destroy()


def close(event):
    """Handle Delete key press"""
    root.destroy()


# Title text
canvas.create_text(width // 2, height // 5, text="Cellular Automata", font=("Arial", 100), fill="black", anchor="center")

# Green play button background
button0 = tk.Button(home_frame, command=start_basic_grid, bg="spring green")
canvas.create_window(width // 2, height // 2 - 100, width=width // 2 - 5, height=100, window=button0, anchor="center")

# Play button icon
img = Image.open("images\play.png").convert("RGBA")
img = img.resize((96, 96))
green_bg = Image.new("RGBA", img.size, (0, 255, 0, 0))
img = Image.alpha_composite(green_bg, img)
photo = ImageTk.PhotoImage(img)
button = tk.Button(home_frame, image=photo, command=start_basic_grid, borderwidth=0, bg="spring green", highlightthickness=0)
canvas.create_window(width // 2, height // 2 - 100, window=button, anchor="center")

# Settings dropdown menu
selected_option = tk.StringVar(root, value="SETTINGS")
selected_option.trace_add("write", option_handler)

menu = tk.Menu(root, tearoff=0)
options = ["Neighbour", "Pointer", "1D"]
for opt in options:
    menu.add_command(label=opt, command=partial(option_selected, opt))

button_settings = tk.Button(home_frame, textvariable=selected_option, bg="gainsboro", font=("Arial", 40))
button_settings.bind("<Button-1>", show_option_menu)
canvas.create_window(width // 2 - 52.5, height // 2 + 15, width=width // 2 - 105, height=100, anchor="center", window=button_settings)

# Info button
info_button = tk.Button(home_frame, command=lambda: tutorial.force_show_tutorial(root), bg="light sky blue", text="i", font=("Arial", 40))
canvas.create_window(width // 2 + 270, height // 2 + 15, width=100, height=100, window=info_button, anchor="center")

# Keybinds button
keybinds_button = tk.Button(home_frame, command=show_keybinds, bg="dark grey", text="KEYBINDS", font=("Arial", 40))
canvas.create_window(width // 2, height // 2 + 130, width=width // 2, height=100, anchor="center", window=keybinds_button)

# Exit button
button1 = tk.Button(home_frame, command=exit_app, bg="red", text="EXIT", font=("Arial", 40))
canvas.create_window(width // 2, height // 2 + 245, width=width // 2, height=100, window=button1, anchor="center")

# Show home screen initially
show_home()

# Keep reference to image
button.image = photo

# Keyboard shortcuts
root.bind(f"<{keybind_settings.get_keybind('close_window')}>", close)

# Run fullscreen
root.overrideredirect(True)
root.mainloop()