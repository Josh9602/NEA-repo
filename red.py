import tkinter as tk

def exit_button(parent, button):
    button0 = tk.Button(parent, bg = "red", command=parent.destroy)
    button0.place(relx = 1.0, y = 0, anchor="ne", height = 10)
    button0.update_idletasks()