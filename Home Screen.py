import tkinter as tk
from PIL import Image, ImageTk

root = tk.Tk()

root.overrideredirect(True)
    
width = root.winfo_screenwidth()
height = root.winfo_screenheight()

canvas = tk.Canvas(root, width = width, height = height)
canvas.pack()

def start():
    import basic_grid
    basic_grid.draw_grid()
    root.destroy()
    
def option(*args):
    if selected_option.get() == "Neighbour":
        root.destroy()
        import settings
    elif selected_option.get() == "Pointer":
        root.destroy()
    else:
        slider = tk.Scale(root, from_=0, to=256, orient=tk.HORIZONTAL)
        slider.pack()
    
def exit():
    root.destroy()

canvas.create_text(width // 2, height // 5, text="Cellular Automata", font=("Arial", 100), fill="black", anchor="center")
canvas.create_text(width // 2, height // 5 + 75, text="By Josh Harrison", font=("Arial", 15), fill="black", anchor="center")

button0 = tk.Button(root, command=start, bg = "spring green")
canvas.create_window(width // 2, height // 2 - 50, width = width // 2, height = 100, window=button0, anchor="center")

img = Image.open("images\play.png").convert("RGBA")
img = img.resize ((96, 96))
green_bg = Image.new("RGBA", img.size, (0, 255, 0, 0))
img = Image.alpha_composite(green_bg, img)
photo = ImageTk.PhotoImage(img)
button = tk.Button(root, image=photo, command=start, borderwidth=0, bg="spring green", highlightthickness=0)
canvas.create_window(width // 2, height // 2 -50, window=button, anchor="center")
    
#button1 = tk.Button(root, command=settings, bg = "gainsboro")
#canvas.create_window(width // 2, height // 2 + 75, width = width // 2, height = 100, window=button1, anchor="center")

selected_option = tk.StringVar(root)
selected_option.trace("w", option)

dropdown = tk.OptionMenu(root, selected_option, "Neighbour", "Pointer", "1D")
dropdown.config(width=20, bg="gainsboro")
canvas.create_window(width // 2, height // 2 + 75, width = width // 2, height = 100,  anchor="center", window=dropdown)

button1 = tk.Button(root, command=exit, bg = "red", text = "EXIT", font = ("Arial", 40))
canvas.create_window(width // 2, height // 2 + 200, width = width // 2, height = 100, window=button1, anchor="center")

root.mainloop()