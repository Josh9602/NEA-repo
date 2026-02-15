import tkinter as tk

class RotationRule:
    def __init__(self, parent, x, y, states, owner_state, delete_callback=None):
        self.states = states
        self.parent = parent
        self.owner_state = owner_state
        self.y_position = y
        self.delete_callback = delete_callback
        
        self.angle = tk.IntVar(value=90)
        
        label2 = tk.Label(parent, text="Rotate:")
        label2.place(x=x, y=y, width=45, height=25)
        
        angles = [-180, -90, -45, 45, 90, 180]
        angle_dropdown = tk.OptionMenu(parent, self.angle, *angles)
        angle_dropdown.place(x=x+50, y=y, width=60, height=25)
        
        label3 = tk.Label(parent, text="°")
        label3.place(x=x+115, y=y, width=15, height=25)
        
        # Delete button
        delete_btn = None
        if delete_callback:
            delete_btn = tk.Button(parent, text="X", command=delete_callback,
                                   bg="#ff4444", fg="white", font=("Arial", 9, "bold"))
            delete_btn.place(x=x+135, y=y, width=25, height=25)
        
        self.widgets = [label2, angle_dropdown, label3]
        if delete_btn:
            self.widgets.append(delete_btn)
    
    def get_rule(self, next_state):
        return {
            "type": "rotation",
            "current_state": self.owner_state,
            "angle": self.angle.get(),
            "next_state": next_state
        }
    
    def destroy(self):
        for widget in self.widgets:
            widget.destroy()


class FaceRule:
    def __init__(self, parent, x, y, states, owner_state, delete_callback=None):
        self.states = states
        self.parent = parent
        self.owner_state = owner_state
        self.y_position = y
        self.delete_callback = delete_callback
        
        self.direction = tk.StringVar(value="North")
        
        label2 = tk.Label(parent, text="Face:")
        label2.place(x=x, y=y, width=35, height=25)
        
        directions = ["North", "South", "East", "West"]
        direction_dropdown = tk.OptionMenu(parent, self.direction, *directions)
        direction_dropdown.place(x=x+40, y=y, width=70, height=25)
        
        # Delete button
        delete_btn = None
        if delete_callback:
            delete_btn = tk.Button(parent, text="X", command=delete_callback,
                                   bg="#ff4444", fg="white", font=("Arial", 9, "bold"))
            delete_btn.place(x=x+115, y=y, width=25, height=25)
        
        self.widgets = [label2, direction_dropdown]
        if delete_btn:
            self.widgets.append(delete_btn)
    
    def get_rule(self, next_state):
        direction_map = {
            "North": 0,
            "East": 90,
            "South": 180,
            "West": 270
        }
        return {
            "type": "face",
            "current_state": self.owner_state,
            "direction": direction_map[self.direction.get()],
            "next_state": next_state
        }
    
    def destroy(self):
        for widget in self.widgets:
            widget.destroy()


class MovementRule:
    def __init__(self, parent, x, y, states, owner_state, delete_callback=None):
        self.states = states
        self.parent = parent
        self.owner_state = owner_state
        self.y_position = y
        self.delete_callback = delete_callback
    
        self.x_val = tk.IntVar(value=0)
        self.y_val = tk.IntVar(value=0)
        self.is_relative = tk.BooleanVar(value=True)
        
        toggle_btn = tk.Checkbutton(parent, text="Rel", variable=self.is_relative)
        toggle_btn.place(x=x, y=y, width=40, height=25)
        
        label2 = tk.Label(parent, text="X:")
        label2.place(x=x+45, y=y, width=15, height=25)
        
        x_spin = tk.Spinbox(parent, from_=-100, to=100, textvariable=self.x_val, width=4)
        x_spin.place(x=x+65, y=y, width=40, height=25)
        
        label3 = tk.Label(parent, text="Y:")
        label3.place(x=x+110, y=y, width=15, height=25)
        
        y_spin = tk.Spinbox(parent, from_=-100, to=100, textvariable=self.y_val, width=4)
        y_spin.place(x=x+130, y=y, width=40, height=25)
        
        # Delete button
        delete_btn = None
        if delete_callback:
            delete_btn = tk.Button(parent, text="X", command=delete_callback,
                                   bg="#ff4444", fg="white", font=("Arial", 9, "bold"))
            delete_btn.place(x=x+175, y=y, width=25, height=25)
        
        self.widgets = [toggle_btn, label2, x_spin, label3, y_spin]
        if delete_btn:
            self.widgets.append(delete_btn)
    
    def get_rule(self, next_state):
        return {
            "type": "movement",
            "current_state": self.owner_state,
            "x": self.x_val.get(),
            "y": self.y_val.get(),
            "relative": self.is_relative.get(),
            "next_state": next_state
        }
    
    def destroy(self):
        for widget in self.widgets:
            widget.destroy()


class CloneRule:
    def __init__(self, parent, x, y, states, owner_state, delete_callback=None):
        self.states = states
        self.parent = parent
        self.owner_state = owner_state
        self.y_position = y
        self.delete_callback = delete_callback
        
        # Clone position controls (like movement rule)
        self.x_val = tk.IntVar(value=0)
        self.y_val = tk.IntVar(value=0)
        self.is_relative = tk.BooleanVar(value=True)
        
        label1 = tk.Label(parent, text="Clone:")
        label1.place(x=x, y=y, width=40, height=25)
        
        toggle_btn = tk.Checkbutton(parent, text="Rel", variable=self.is_relative)
        toggle_btn.place(x=x+45, y=y, width=40, height=25)
        
        label2 = tk.Label(parent, text="X:")
        label2.place(x=x+90, y=y, width=15, height=25)
        
        x_spin = tk.Spinbox(parent, from_=-100, to=100, textvariable=self.x_val, width=4)
        x_spin.place(x=x+110, y=y, width=40, height=25)
        
        label3 = tk.Label(parent, text="Y:")
        label3.place(x=x+155, y=y, width=15, height=25)
        
        y_spin = tk.Spinbox(parent, from_=-100, to=100, textvariable=self.y_val, width=4)
        y_spin.place(x=x+175, y=y, width=40, height=25)
        
        # Delete button
        delete_btn = None
        if delete_callback:
            delete_btn = tk.Button(parent, text="X", command=delete_callback,
                                   bg="#ff4444", fg="white", font=("Arial", 9, "bold"))
            delete_btn.place(x=x+220, y=y, width=25, height=25)
        
        self.widgets = [label1, toggle_btn, label2, x_spin, label3, y_spin]
        if delete_btn:
            self.widgets.append(delete_btn)
    
    def get_rule(self, next_state):
        return {
            "type": "clone",
            "current_state": self.owner_state,
            "x": self.x_val.get(),
            "y": self.y_val.get(),
            "relative": self.is_relative.get(),
            "next_state": next_state
        }
    
    def destroy(self):
        for widget in self.widgets:
            widget.destroy()