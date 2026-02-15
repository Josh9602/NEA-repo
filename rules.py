"""
Rules UI components for neighborhood-based cellular automata
Creates dropdown menus and spinboxes for defining transition rules
WITH DELETE BUTTON support
"""

import tkinter as tk

class Rules:
    """UI component for a single cellular automaton rule"""
    
    def __init__(self, parent, x, y, states, owner_state, color, max_neighbors=8, create_labels=True, delete_callback=None):
        """
        Initialize rule UI component
        
        Args:
            parent: Parent tkinter widget
            x, y: Position coordinates
            states: List of available states
            owner_state: State this rule belongs to
            color: Color variable for this state
            max_neighbors: Maximum possible neighbors
            create_labels: Whether to create column headers
            delete_callback: Function to call when delete button clicked
        """
        self.states = states
        self.selected1 = tk.StringVar(value=states[0] if states else "")
        self.selected2 = tk.StringVar(value=states[0] if states else "")
        self.selected_op = tk.StringVar(value="=")
        self.spin_val = tk.IntVar(value=0)
        self.owner = owner_state
        self.state_color = color
        self.y_position = y
        self.max_neighbors = max_neighbors
        self.delete_callback = delete_callback

        # Create column headers (only for first rule)
        if create_labels:
            label1 = tk.Label(parent, text="Current:")
            label1.place(x=x, y=y-20, width=80, height=20)

            label2 = tk.Label(parent, text="Neighbor:")
            label2.place(x=x+110, y=y-20, width=80, height=20)

            label3 = tk.Label(parent, text="Op:")
            label3.place(x=x+220, y=y-20, width=50, height=20)

            label4 = tk.Label(parent, text="Count:")
            label4.place(x=x+290, y=y-20, width=40, height=20)

        # Current state dropdown
        dropdown1 = tk.OptionMenu(parent, self.selected1, *states)
        dropdown1.place(x=x, y=y, width=100, height=25)

        # Neighbor state dropdown
        dropdown2 = tk.OptionMenu(parent, self.selected2, *states)
        dropdown2.place(x=x+110, y=y, width=100, height=25)

        # Operator dropdown
        ops = [">", "<", ">=", "<=", "=", "!="]
        dropdown_op = tk.OptionMenu(parent, self.selected_op, *ops)
        dropdown_op.place(x=x+220, y=y, width=60, height=25)

        # Count spinbox
        spinbox = tk.Spinbox(parent, from_=0, to=max_neighbors, textvariable=self.spin_val, width=3)
        spinbox.place(x=x+290, y=y, width=40, height=25)
        
        # Delete button (red X)
        delete_btn = None
        if delete_callback:
            delete_btn = tk.Button(parent, text="X", command=delete_callback, 
                                   bg="#ff4444", fg="white", font=("Arial", 10, "bold"))
            delete_btn.place(x=x+340, y=y, width=30, height=25)
        
        self.widgets = [dropdown1, dropdown2, dropdown_op, spinbox]
        if delete_btn:
            self.widgets.append(delete_btn)
    
    def update_max_neighbors(self, max_neighbors):
        """Update maximum neighbor count when neighborhood changes"""
        self.max_neighbors = max_neighbors
        
        # Find and update spinbox
        for widget in self.widgets:
            if isinstance(widget, tk.Spinbox):
                widget.config(to=max_neighbors)
                # Reset if current value exceeds new max
                if self.spin_val.get() > max_neighbors:
                    self.spin_val.set(max_neighbors)
        
    def move_down(self, pixels):
        """Move rule down by specified pixels"""
        self.y_position += pixels
        for widget in self.widgets:
            widget_info = widget.place_info()
            new_y = int(widget_info['y']) + pixels
            widget.place(y=new_y)
    
    def update_state_dropdowns(self):
        """Rebuild state dropdowns when states change"""
        if not self.states:
            return
            
        parent = self.widgets[0].master
        x = int(self.widgets[0].place_info()['x'])
        current_y = int(self.widgets[0].place_info()['y'])
        
        # Save current selections
        current_val1 = self.selected1.get()
        current_val2 = self.selected2.get()
        
        # Destroy old dropdowns
        self.widgets[0].destroy()
        self.widgets[1].destroy()
        
        # Create new dropdowns
        dropdown1 = tk.OptionMenu(parent, self.selected1, *self.states)
        dropdown1.place(x=x, y=current_y, width=100, height=25)
        dropdown2 = tk.OptionMenu(parent, self.selected2, *self.states)
        dropdown2.place(x=x+110, y=current_y, width=100, height=25)
        
        # Restore selections if still valid
        if current_val1 in [str(s) for s in self.states]:
            self.selected1.set(current_val1)
        if current_val2 in [str(s) for s in self.states]:
            self.selected2.set(current_val2)
        
        self.widgets[0] = dropdown1
        self.widgets[1] = dropdown2
    
    def destroy(self):
        """Destroy all widgets belonging to this rule"""
        for widget in self.widgets:
            widget.destroy()
    
    def get_rule(self):
        """
        Get rule dictionary for automaton engine
        
        Returns:
            dict: Rule specification with current_state, conditions, next_state, color
        """
        # Return raw values - let settings.py handle conversion
        return {
            "current_state": self.selected1.get(), 
            "conditions": [{
                "neighbor_state": self.selected2.get(), 
                "operator": self.selected_op.get(), 
                "count": int(self.spin_val.get())
            }], 
            "next_state": self.owner, 
            "color": self.state_color.get()
        }