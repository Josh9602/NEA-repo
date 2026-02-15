"""
PSettings_Pannel.py
UI panels for configuring individual states in pointer-based automata.
Each panel manages state color, name, state switching, and rule type buttons.
WITH DELETE BUTTONS for individual rules - FULLY FIXED
"""

import tkinter as tk
from Prules import RotationRule, FaceRule, MovementRule, CloneRule
from tkinter import colorchooser
import shared_state

# Global list tracking all state managers for coordination
state_managers = []


class StateManager:
    """
    Configuration panel for one state in pointer automata.
    Manages state properties and up to 4 rule types (rotation, face, movement, clone).
    """
    
    def __init__(self, pframe, canvas, rule_set, states, initial_total=0):
        """
        Initialize state configuration panel.
        """
        self.pframe = pframe
        self.canvas = canvas
        self.rule_set = rule_set
        self.states = states
        self.my_base_y = initial_total
        self.my_state_index = len(states) - 1
        
        # Rule type references (only one of each allowed)
        self.rotation_rule = None
        self.face_rule = None
        self.movement_rule = None
        self.clone_rule = None
        
        self.state_color = tk.StringVar(value="#ffffff")
        self.entry_var = tk.StringVar(value=states[len(states)-1] if states else "")
        self.switch_state = tk.IntVar(value=0)  # Store state index as integer
        self.state_indices = list(range(len(states)))
        
        state_managers.append(self)
        
        self.create_ui()
        self.setup_events()
        self.current_y_offset = 90
    
    def create_ui(self):
        """Create UI elements: color picker, name entry, state switcher, rule buttons."""
        # Color swatch showing current state color
        self.swatch = tk.Label(self.pframe, width=2, height=1, bg="white", relief="solid")
        self.swatch.place(x=205, y=27.5 + self.my_base_y)
        
        # Color picker button
        self.button = tk.Button(self.pframe, text="Color", command=self.choose_color)
        self.button.place(x=160, y=25 + self.my_base_y)
        
        # State name entry
        self.entry = tk.Entry(self.pframe, width=20, textvariable=self.entry_var)
        self.entry.place(x=30, y=30 + self.my_base_y)
        
        # "Switch to state" dropdown
        switch_label = tk.Label(self.pframe, text="Switch to state:")
        switch_label.place(x=30, y=60 + self.my_base_y)
        
        self.switch_dropdown = tk.OptionMenu(self.pframe, self.switch_state, *self.state_indices)
        self.switch_dropdown.place(x=130, y=57 + self.my_base_y, width=80, height=25)
        
        # Rule type buttons (mutually exclusive for rotation/face)
        self.rotation_button = tk.Button(self.pframe, text="+ Rotation", command=self.add_rotation)
        self.rotation_button.place(x=30, y=95 + self.my_base_y, width=80, height=25)
        
        self.face_button = tk.Button(self.pframe, text="+ Face", command=self.add_face)
        self.face_button.place(x=120, y=95 + self.my_base_y, width=80, height=25)
        
        self.movement_button = tk.Button(self.pframe, text="+ Movement", command=self.add_movement)
        self.movement_button.place(x=210, y=95 + self.my_base_y, width=80, height=25)
        
        self.clone_button = tk.Button(self.pframe, text="+ Clone", command=self.add_clone)
        self.clone_button.place(x=300, y=95 + self.my_base_y, width=80, height=25)
        
        # Initialize dropdown display
        self.update_dropdown()
    
    def setup_events(self):
        """Bind event handlers for reactive updates."""
        self.entry_var.trace_add("write", self.update_state)
    
    def choose_color(self):
        """
        Open color picker dialog and update state color.
        Updates swatch to show selected color.
        """
        color = colorchooser.askcolor(title="Choose color")
        if color[1]:
            self.state_color.set(color[1])
            self.swatch.config(bg=color[1])
    
    def add_rotation(self):
        """
        Add rotation rule to this state.
        Hides both rotation and face buttons (mutually exclusive).
        """
        if self.rotation_rule is None:
            current_y = self.my_base_y + self.current_y_offset
            self.pushdown(current_y)
            
            self.rotation_rule = RotationRule(self.pframe, 30, current_y, self.states, 
                                             self.my_state_index, 
                                             delete_callback=self.delete_rotation)
            self.rule_set.append(self.rotation_rule)
            self.rotation_button.place_forget()
            self.face_button.place_forget()
            self.current_y_offset += 30
            self.shift_buttons_down()
            self.update_manager_positions()

    def delete_rotation(self):
        """Delete rotation rule and restore buttons"""
        if self.rotation_rule:
            deleted_y = self.rotation_rule.y_position
            self.rotation_rule.destroy()
            if self.rotation_rule in self.rule_set:
                self.rule_set.remove(self.rotation_rule)
            self.rotation_rule = None
            
            self.current_y_offset -= 30
            self.pullup(deleted_y)
            
            # Restore both rotation and face buttons
            self.reposition_all_buttons()
            
            self.update_manager_positions()

    def add_face(self):
        """
        Add facing direction rule to this state.
        Hides both face and rotation buttons (mutually exclusive).
        """
        if self.face_rule is None:
            current_y = self.my_base_y + self.current_y_offset
            self.pushdown(current_y)
            
            self.face_rule = FaceRule(self.pframe, 30, current_y, self.states, 
                                     self.my_state_index,
                                     delete_callback=self.delete_face)
            self.rule_set.append(self.face_rule)
            self.face_button.place_forget()
            self.rotation_button.place_forget()
            self.current_y_offset += 30
            self.shift_buttons_down()
            self.update_manager_positions()

    def delete_face(self):
        """Delete face rule and restore buttons"""
        if self.face_rule:
            deleted_y = self.face_rule.y_position
            self.face_rule.destroy()
            if self.face_rule in self.rule_set:
                self.rule_set.remove(self.face_rule)
            self.face_rule = None
            
            self.current_y_offset -= 30
            self.pullup(deleted_y)
            
            # Restore both rotation and face buttons
            self.reposition_all_buttons()
            
            self.update_manager_positions()

    def add_movement(self):
        """
        Add movement rule to this state.
        Hides movement button only (can coexist with rotation/face).
        """
        if self.movement_rule is None:
            current_y = self.my_base_y + self.current_y_offset
            self.pushdown(current_y)
            
            self.movement_rule = MovementRule(self.pframe, 30, current_y, self.states, 
                                             self.my_state_index,
                                             delete_callback=self.delete_movement)
            self.rule_set.append(self.movement_rule)
            self.movement_button.place_forget()
            self.current_y_offset += 30
            self.shift_buttons_down()
            self.update_manager_positions()

    def delete_movement(self):
        """Delete movement rule and restore button"""
        if self.movement_rule:
            deleted_y = self.movement_rule.y_position
            self.movement_rule.destroy()
            if self.movement_rule in self.rule_set:
                self.rule_set.remove(self.movement_rule)
            self.movement_rule = None
            
            self.current_y_offset -= 30
            self.pullup(deleted_y)
            
            # Restore movement button
            self.reposition_all_buttons()
            
            self.update_manager_positions()

    def add_clone(self):
        """
        Add clone rule to this state.
        Hides clone button only.
        """
        if self.clone_rule is None:
            current_y = self.my_base_y + self.current_y_offset
            self.pushdown(current_y)
            
            self.clone_rule = CloneRule(self.pframe, 30, current_y, self.states, 
                                       self.my_state_index,
                                       delete_callback=self.delete_clone)
            self.rule_set.append(self.clone_rule)
            self.clone_button.place_forget()
            self.current_y_offset += 30
            self.shift_buttons_down()
            self.update_manager_positions()

    def delete_clone(self):
        """Delete clone rule and restore button"""
        if self.clone_rule:
            deleted_y = self.clone_rule.y_position
            self.clone_rule.destroy()
            if self.clone_rule in self.rule_set:
                self.rule_set.remove(self.clone_rule)
            self.clone_rule = None
            
            self.current_y_offset -= 30
            self.pullup(deleted_y)
            
            # Restore clone button
            self.reposition_all_buttons()
            
            self.update_manager_positions()
    
    def reposition_all_buttons(self):
        """
        Reposition ALL rule buttons based on which rules exist.
        This is called after deletion to restore hidden buttons.
        """
        button_y = self.my_base_y + self.current_y_offset
        x_offset = 30
        
        # Rotation and Face are mutually exclusive - show if neither rule exists
        if self.rotation_rule is None and self.face_rule is None:
            self.rotation_button.place(x=x_offset, y=button_y, width=80, height=25)
            x_offset += 90
            self.face_button.place(x=x_offset, y=button_y, width=80, height=25)
            x_offset += 90
        else:
            # Hide both if either exists
            self.rotation_button.place_forget()
            self.face_button.place_forget()
        
        # Movement - show if rule doesn't exist
        if self.movement_rule is None:
            self.movement_button.place(x=x_offset, y=button_y, width=80, height=25)
            x_offset += 90
        else:
            self.movement_button.place_forget()
        
        # Clone - show if rule doesn't exist
        if self.clone_rule is None:
            self.clone_button.place(x=x_offset, y=button_y, width=80, height=25)
        else:
            self.clone_button.place_forget()
    
    def pushdown(self, current_y):
        """
        Shift all widgets below insertion point down by 30 pixels.
        Cascades through all panels to maintain layout.
        """
        # Move widgets in this frame
        for widget in self.pframe.winfo_children():
            widget_info = widget.place_info()
            if widget_info and 'y' in widget_info:
                widget_y = int(widget_info['y'])
                if widget_y > current_y:
                    widget.place(y=widget_y + 30)
        
        # Update base positions of panels below this one
        for manager in state_managers:
            if manager.my_base_y > self.my_base_y:
                manager.my_base_y += 30
        
        shared_state.shared.total += 30
    
    def pullup(self, deleted_y):
        """
        Shift all widgets below deleted rule up by 30 pixels.
        """
        # Move widgets in this frame
        for widget in self.pframe.winfo_children():
            widget_info = widget.place_info()
            if widget_info and 'y' in widget_info:
                widget_y = int(widget_info['y'])
                if widget_y > deleted_y:
                    widget.place(y=widget_y - 30)
        
        # Update y_position for remaining rules
        if self.rotation_rule and self.rotation_rule.y_position > deleted_y:
            self.rotation_rule.y_position -= 30
        if self.face_rule and self.face_rule.y_position > deleted_y:
            self.face_rule.y_position -= 30
        if self.movement_rule and self.movement_rule.y_position > deleted_y:
            self.movement_rule.y_position -= 30
        if self.clone_rule and self.clone_rule.y_position > deleted_y:
            self.clone_rule.y_position -= 30
        
        # Update base positions of panels below this one
        for manager in state_managers:
            if manager.my_base_y > self.my_base_y:
                manager.my_base_y -= 30
        
        shared_state.shared.total -= 30
    
    def shift_buttons_down(self):
        """Reposition visible rule buttons in a row at current offset."""
        button_y = self.my_base_y + self.current_y_offset
        x_offset = 30
        
        # Layout buttons horizontally based on visibility
        if self.rotation_button.winfo_ismapped():
            self.rotation_button.place(x=x_offset, y=button_y, width=80, height=25)
            x_offset += 90
        if self.face_button.winfo_ismapped():
            self.face_button.place(x=x_offset, y=button_y, width=80, height=25)
            x_offset += 90
        if self.movement_button.winfo_ismapped():
            self.movement_button.place(x=x_offset, y=button_y, width=80, height=25)
            x_offset += 90
        if self.clone_button.winfo_ismapped():
            self.clone_button.place(x=x_offset, y=button_y, width=80, height=25)
    
    def update_manager_positions(self):
        """
        Recalculate total height and update scrollbar.
        Triggers layout callback for parent frame.
        """
        shared_state.shared.total = sum(manager.current_y_offset + 40 for manager in state_managers)
        if shared_state.shared.update_callback:
            shared_state.shared.update_callback()
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def update_state(self, *args):
        """
        Update state name in shared list when entry changes.
        Propagates to all dropdowns across all panels.
        """
        if 0 <= self.my_state_index < len(self.states):
            self.states[self.my_state_index] = self.entry_var.get()
            
            # Update all manager dropdowns
            for manager in state_managers:
                manager.update_dropdown()
                
            self.canvas.update_idletasks()
            self.pframe.update_idletasks()
    
    def update_dropdown(self):
        """
        Rebuild switch state dropdown to show state names while storing indices.
        Called when states are added/renamed.
        """
        if not self.states:
            return
        
        # Store current selection
        current_val = self.switch_state.get()
        
        # Get dropdown position
        x = int(self.switch_dropdown.place_info()['x'])
        y = int(self.switch_dropdown.place_info()['y'])
        
        # Destroy old dropdown
        self.switch_dropdown.destroy()
        
        # Update state indices
        self.state_indices = list(range(len(self.states)))
        
        # Create new dropdown
        self.switch_dropdown = tk.OptionMenu(self.pframe, self.switch_state, *self.state_indices)
        self.switch_dropdown.place(x=x, y=y, width=80, height=25)
        
        # Customize menu items to show state names
        menu = self.switch_dropdown["menu"]
        menu.delete(0, "end")
        for idx in self.state_indices:
            display_text = str(self.states[idx])
            menu.add_command(label=display_text, command=lambda value=idx: self.switch_state.set(value))
        
        # Restore selection if valid
        if current_val < len(self.states):
            self.switch_state.set(current_val)
        else:
            self.switch_state.set(0)
        
        # Update display text on button
        self._update_dropdown_display()
    
    def _update_dropdown_display(self):
        """
        Update dropdown button text to show state name.
        Sets up trace to keep display synchronized.
        """
        idx = self.switch_state.get()
        if idx < len(self.states):
            self.switch_dropdown.config(text=str(self.states[idx]))
        
        # Remove old trace to avoid duplicates
        try:
            self.switch_state.trace_remove("write", self._trace_id)
        except (AttributeError, KeyError):
            pass
        
        # Add trace to update display on selection change
        self._trace_id = self.switch_state.trace_add("write", lambda *args: self._update_display())
    
    def _update_display(self):
        """Update button text when selection changes."""
        idx = self.switch_state.get()
        if idx < len(self.states):
            self.switch_dropdown.config(text=str(self.states[idx]))
    
    def get_rules(self):
        """
        Collect all rules for this state.
        """
        rules = []
        next_state = self.switch_state.get()  # Already an integer (state index)
        
        if self.rotation_rule:
            rules.append(self.rotation_rule.get_rule(next_state))
        if self.face_rule:
            rules.append(self.face_rule.get_rule(next_state))
        if self.movement_rule:
            rules.append(self.movement_rule.get_rule(next_state))
        if self.clone_rule:
            rules.append(self.clone_rule.get_rule(next_state))
        
        return rules


def create_new_state(pframe, canvas, rule_set, states, initial_total=0):
    """
    Factory function to create new state configuration panel.
    """
    return StateManager(pframe, canvas, rule_set, states, initial_total)