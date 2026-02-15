"""
Settings_pannel.py
UI panels for configuring individual states in neighborhood-based automata.
Each panel manages state color, name, and multiple neighbor-based rules.
WITH DELETE BUTTONS for individual rules
"""

import tkinter as tk
from tkinter import colorchooser
from rules import Rules
import shared_state

# Global list tracking all state panels for coordination
state_rule_panels = []


class StateRulePanel:
    """
    Configuration panel for one state in neighborhood automata.
    Manages state properties and dynamic rule creation.
    """
    
    def __init__(self, pframe, canvas, rule_set, states, initial_total=0, max_neighbors=8):
        """
        Initialize state configuration panel.
        """
        self.pframe = pframe
        self.canvas = canvas
        self.rule_set = rule_set
        self.states = states
        self.my_base_y = initial_total
        self.my_state_index = len(states) - 1
        self.max_neighbors = max_neighbors
        
        self.rules = []  # Rules belonging to this state
        self.state_color = tk.StringVar(value="#ffffff")
        self.entry_var = tk.StringVar(value=states[len(states)-1] if states else "")
        
        state_rule_panels.append(self)
        
        self.create_ui()
        self.setup_events()
        self.current_y_offset = 75
        self.labels_created = False  # Track if column headers exist
    
    def create_ui(self):
        """Create UI elements: color picker, name entry, add rule button."""
        # Color swatch showing current state color
        self.swatch = tk.Label(self.pframe, width=2, height=1, bg="white", relief="solid")
        self.swatch.place(x=205, y=27.5 + self.my_base_y)
        
        # Color picker button
        self.button = tk.Button(self.pframe, text="Color", command=self.choose_color)
        self.button.place(x=160, y=25 + self.my_base_y)
        
        # State name entry
        self.entry = tk.Entry(self.pframe, width=20, textvariable=self.entry_var)
        self.entry.place(x=30, y=30 + self.my_base_y)
        
        # Add rule button
        self.add_rule_button = tk.Button(self.pframe, text="+ Add Rule", command=self.add_rule)
        self.add_rule_button.place(x=30, y=60 + self.my_base_y, width=300, height=25)
    
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
    
    def add_rule(self):
        """
        Add new neighbor rule to this state.
        Creates column headers on first rule, then adds rule row.
        """
        current_y = self.my_base_y + self.current_y_offset
        self.pushdown(current_y)
        
        # Create column headers only once
        if not self.labels_created:
            self.create_rule_labels(current_y - 20)
            self.labels_created = True
        
        # Create new rule with delete callback
        new_rule = Rules(self.pframe, 30, current_y, self.states, self.my_state_index, 
                        self.state_color, self.max_neighbors, create_labels=False,
                        delete_callback=lambda r=None: self.delete_rule(new_rule))
        self.rules.append(new_rule)
        self.rule_set.append(new_rule)
        
        self.current_y_offset += 30
        self.shift_button_down()
        self.update_panel_positions()
    
    def delete_rule(self, rule):
        """
        Delete a specific rule and reposition everything.
        """
        if rule not in self.rules:
            return
        
        # Remove from lists
        self.rules.remove(rule)
        if rule in self.rule_set:
            self.rule_set.remove(rule)
        
        # Destroy widgets
        rule.destroy()
        
        # If no rules left, remove the column headers too
        if len(self.rules) == 0:
            self.labels_created = False
            # Delete all labels in the header area
            for widget in self.pframe.winfo_children():
                widget_info = widget.place_info()
                if widget_info and 'y' in widget_info:
                    widget_y = int(widget_info['y'])
                    # Labels are 20 pixels above first rule position
                    if widget_y == self.my_base_y + 55:  # Header y position
                        widget.destroy()
        
        # Recalculate positions
        self.current_y_offset -= 30
        
        # Shift all widgets up
        self.pullup(rule.y_position)
        
        # Reposition button at correct location
        self.shift_button_down()
        
        # Update all panel positions
        self.update_panel_positions()
    
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
        
        # Update y_position for all rules below the deleted one
        for rule in self.rules:
            if rule.y_position > deleted_y:
                rule.y_position -= 30
        
        # Update base positions of panels below this one
        for panel in state_rule_panels:
            if panel.my_base_y > self.my_base_y:
                panel.my_base_y -= 30
        
        shared_state.shared.total -= 30
    
    def create_rule_labels(self, y):
        """
        Create column headers for rule table.
        Only called once per panel for efficiency.
        """
        label1 = tk.Label(self.pframe, text="Current:")
        label1.place(x=30, y=y, width=80, height=20)
        
        label2 = tk.Label(self.pframe, text="Neighbor:")
        label2.place(x=140, y=y, width=80, height=20)
        
        label3 = tk.Label(self.pframe, text="Op:")
        label3.place(x=250, y=y, width=50, height=20)
        
        label4 = tk.Label(self.pframe, text="Count:")
        label4.place(x=320, y=y, width=40, height=20)
        
        # Add "Delete" header for delete buttons
        label5 = tk.Label(self.pframe, text="Del:")
        label5.place(x=370, y=y, width=30, height=20)
    
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
        for panel in state_rule_panels:
            if panel.my_base_y > self.my_base_y:
                panel.my_base_y += 30
        
        shared_state.shared.total += 30
    
    def shift_button_down(self):
        """Reposition 'Add Rule' button below all rules."""
        button_y = self.my_base_y + self.current_y_offset
        self.add_rule_button.place(x=30, y=button_y, width=300, height=25)
    
    def update_panel_positions(self):
        """
        Recalculate total height and update scrollbar.
        Triggers layout callback for parent frame.
        """
        shared_state.shared.total = sum(panel.current_y_offset + 40 for panel in state_rule_panels)
        if shared_state.shared.update_callback:
            shared_state.shared.update_callback()
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def update_state(self, *args):
        """
        Update state name in shared list when entry changes.
        Propagates to all rule dropdowns across all panels.
        """
        if 0 <= self.my_state_index < len(self.states):
            self.states[self.my_state_index] = self.entry_var.get()
            
            # Update all dropdowns in all panels
            for panel in state_rule_panels:
                for rule in panel.rules:
                    rule.update_state_dropdowns()
                
            self.canvas.update_idletasks()
            self.pframe.update_idletasks()
    
    def update_max_neighbors(self, max_neighbors):
        """
        Update maximum neighbor count for all rules in this panel.
        Called when neighborhood settings change.
        """
        self.max_neighbors = max_neighbors
        for rule in self.rules:
            rule.update_max_neighbors(max_neighbors)
    
    def get_rules(self):
        """
        Collect all rules for this state.
        """
        return [rule.get_rule() for rule in self.rules]


def create_new_state(pframe, canvas, rule_set, states, initial_total=0, max_neighbors=8):
    """
    Factory function to create new state configuration panel.
    """
    return StateRulePanel(pframe, canvas, rule_set, states, initial_total, max_neighbors)


def update_all_max_neighbors(max_neighbors):
    """
    Propagate max neighbor change to all existing panels.
    Called when neighborhood type/radius changes.
    
    Args:
        max_neighbors: New maximum neighbor count
    """
    for panel in state_rule_panels:
        panel.update_max_neighbors(max_neighbors)