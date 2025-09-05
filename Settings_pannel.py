import tkinter as tk
import keypad
import rules
from tkinter import colorchooser

def cpanel():
    button = tk.Button(tk.Tk(), bg = "spring green")
    canvas.create_window(width // 2, height // 2 - 50, width = width // 2, height = 100, window=button0, anchor="center")

def new_state0(total, pframe, canvas, new_rule):
    states = [0, 1]
    
    def choose_color():
        color = colorchooser.askcolor(title="Choose color") #stupid american spelling just gonna go with it otherwise im gonna confuse myself later
        swatch.config(bg=color[1])
    
    def keypads():
        keypad_button.place_forget()
        key = keypad.keypad(pframe, x = 250, y = 25 + total)
        print(key)
        
    def comparison():
        rel_button.place_forget()
        keypad_button.place_forget()
        new_rule = rules.create_rule(pframe, 30, 75 + total, states)
        
    
    swatch = tk.Label(pframe, width=2, height=1, bg="white", relief="solid")
    swatch.place(x=225, y=27.5+total)
    
    button = tk.Button(pframe, text="Color", command=choose_color)
    button.place(x = 175, y = 25+total)
    
    entry = tk.Entry(pframe, width = 20)
    entry.place(x=30, y=30+total)
    value = entry.get()
    entry.insert(0, "Name Of State")

    keypad_button = tk.Button(pframe, text = "keypad", command = keypads)
    keypad_button.place(x = 30, y = 70+total)

    rel_button = tk.Button(pframe, text = "relational", command = comparison)
    rel_button.place(x = 95, y = 70+total)