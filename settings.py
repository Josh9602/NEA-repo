import tkinter as tk
import Settings_pannel

root = tk.Tk()

width = root.winfo_screenwidth()
height = root.winfo_screenheight()
total = 0

root.geometry(f"{width-10}x{height}")

canvas = tk.Canvas(root, width=400, height=300)
canvas.pack(side="left", fill="both", expand=False)

scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

canvas.configure(yscrollcommand=scrollbar.set)

frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor="nw")
def start():
    root.destroy()

def update_scrollregion(event=None):
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

def scroll(event):
    top = canvas.canvasy(0)
    
    if event.delta > 0: 
        if top <= 0: 
           return

    canvas.yview_scroll(int(-1*(event.delta/100)), "units")
    
def add_pannel():
    global total
    Settings_pannel.new_state0(total, frame, canvas)
    total+=90
    height = total + 150
    frame.configure(height=height, width=400)
    button.place(x = 30, y = 15+total)
    root.after(10, update_scrollregion)
    
def setstart():
    import basic_grid
    basic_grid.draw_grid()
    root.destroy()

button = tk.Button(frame, text="add state", width = 30, command=add_pannel)

add_pannel()
add_pannel()

canvas.bind_all("<MouseWheel>", scroll)
frame.bind("<Configure>", update_scrollregion)

button0 = tk.Button(root, command=setstart, borderwidth=0, bg="spring green", highlightthickness=0, width = 15, height = 3, bd = 2)
button0.place(relx=0.986, rely=0.98, anchor="se")

root.mainloop()
