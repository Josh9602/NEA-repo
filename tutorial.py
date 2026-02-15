"""
tutorial.py
Interactive first-launch tutorial system
Simple, non-blocking tutorial
"""

import tkinter as tk
import os
import json

def show_tutorial_dialog(root):
    """Show simple welcome tutorial dialog"""
    dialog = tk.Toplevel(root)
    dialog.title("Welcome to Cellular Automata!")
    dialog.geometry("700x500")
    dialog.transient(root)
    dialog.grab_set()
    
    # Center window
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Instructions frame with scrollbar
    text_frame = tk.Frame(dialog)
    text_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 11), 
                         yscrollcommand=scrollbar.set, relief="flat", bg="#f0f0f0")
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text_widget.yview)
    
    tutorial_text = """Quick Start Guide:

🎮 MAIN MENU BUTTONS:

• Green PLAY Button
  Runs Conway's Game of Life - the classic cellular automaton
  
• SETTINGS Dropdown
  - Neighbour: Create custom neighborhood automata (Brian's Brain)
  - Pointer: Create pointer automata (Langton's Ant)  
  - 1D: Run 1D elementary cellular automata (Rules 0-255)
  
• KEYBINDS
  Customise all keyboard shortcuts to your preference
  
• TUTORIAL (this button)
  Show this help again anytime


⚙️ CREATING CUSTOM AUTOMATA:

1. Click SETTINGS → Choose Neighbour or Pointer
2. Add states with the "add state" button
3. Give each state a color  
4. Add rules that define how cells change
5. Click START to run your simulation


🕹️ SIMULATION CONTROLS:

While running a simulation:

• Left Click + Drag: Paint cells
• Right Click + Drag: Pan viewport (move around)
• Arrow Keys: Pan viewport
• Mouse Wheel: Zoom in/out

• SPACE: Play/Pause
• R: Reset grid
• ESC: Go back to settings/menu

• Ctrl+Z: Undo (up to 5 generations)
• Ctrl+Y: Redo

• +/-: Speed up/slow down
• . (period): Step forward 1 generation


💡 TIPS:

• Start with the green PLAY button to see Conway's Life in action
• Experiment with different rules in settings
• Save your favorite rulesets for later
• Use the side panel to adjust grid density


📚 WANT MORE INFO?

• Customize controls in the KEYBINDS menu
• Have fun exploring cellular automata!
"""
    
    text_widget.insert("1.0", tutorial_text)
    text_widget.config(state="disabled")  # Make read-only
    
    # Buttons
    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=20)
    
    def close_tutorial():
        dialog.destroy()
    
    got_it_btn = tk.Button(button_frame, text="Got it!", command=close_tutorial,
                          font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
                          width=15, height=2)
    got_it_btn.pack(side="left", padx=10)
    
    def on_close():
        dialog.destroy()
    
    dialog.protocol("WM_DELETE_WINDOW", on_close)


def force_show_tutorial(root, on_complete_callback=None):
    """Force show tutorial (for testing or 'Help' menu option)"""
    show_tutorial_dialog(root)