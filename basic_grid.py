import tkinter as tk
from collections import Counter
import operator

root = tk.Tk()

TOTAL_ROWS = int(root.winfo_screenheight() // 7.5)
TOTAL_COLS = int(root.winfo_screenwidth() // 7.5)
CELLS = [[0 for _ in range(TOTAL_COLS)] for _ in range(TOTAL_ROWS)]

CELL_SIZE = 25
ROWS = root.winfo_screenheight() // CELL_SIZE + 1
COLS = root.winfo_screenwidth() // CELL_SIZE + 1

row_view = (TOTAL_ROWS - ROWS) // 2
col_view = (TOTAL_COLS - COLS) // 2

toggle = True
automata = False

canvas = tk.Canvas(root, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE)
canvas.pack()

RULES = [
    {"current_state": 1, "conditions": [{"neighbor_state": 1, "operator": "<", "count": 2}], "next_state": 0},
    {"current_state": 1, "conditions": [{"neighbor_state": 1, "operator": ">", "count": 3}], "next_state": 0},
    {"current_state": 0, "conditions": [{"neighbor_state": 1, "operator": "==", "count": 3}],"next_state": 1}]

rel = {"==": operator.eq, "!=": operator.ne, "<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge}


rect_ids = [[None for _ in range(TOTAL_COLS)] for _ in range(TOTAL_ROWS)]
for r in range(TOTAL_ROWS):
    for c in range(TOTAL_COLS):
        x0 = c * CELL_SIZE
        y0 = r * CELL_SIZE
        x1 = x0 + CELL_SIZE
        y1 = y0 + CELL_SIZE
        rect_ids[r][c] = canvas.create_rectangle(x0, y0, x1, y1, fill="grey", outline="black")


def draw_grid():
    for r in range(TOTAL_ROWS):
        for c in range(TOTAL_COLS):
            actual_row = r
            actual_col = c

            if row_view <= r < row_view + ROWS and col_view <= c < col_view + COLS:
                x0 = (c - col_view) * CELL_SIZE
                y0 = (r - row_view) * CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE
                canvas.coords(rect_ids[r][c], x0, y0, x1, y1)
                color = "white" if CELLS[r][c] == 0 else "grey"
                canvas.itemconfig(rect_ids[r][c], fill=color)
                canvas.itemconfig(rect_ids[r][c], state="normal")
                
            else:
                canvas.itemconfig(rect_ids[r][c], state="hidden")


def toggle_cell(event):
    if toggle == False:
        return
    
    row = row_view + int(event.y // CELL_SIZE)
    col = col_view + int(event.x // CELL_SIZE)
    if 0 <= row < TOTAL_ROWS and 0 <= col < TOTAL_COLS:
        CELLS[row][col] = 1 - CELLS[row][col]
        canvas.itemconfig(rect_ids[row][col], fill="grey" if CELLS[row][col] else "white")
        
def pause():
    global toggle, automata, loop
    
    toggle = True
    automata = False
    
    
def play():
    global toggle, automata, loop
    
    toggle = False
    automata = True
    
    def step():
        if automata:
            neighbours()
            root.after(50, step) 

    step()


def zoom(event):
    global CELL_SIZE, ROWS, COLS, row_view, col_view

    center_row = row_view + ROWS // 2
    center_col = col_view + COLS // 2

    if event.num == 5 or event.delta < 0: 
        if CELL_SIZE > 10:
            CELL_SIZE -= 2.5
    elif event.num == 4 or event.delta > 0:  
        if CELL_SIZE < 50:
            CELL_SIZE += 2.5

    ROWS = int(root.winfo_screenheight() // CELL_SIZE) + 1
    COLS = int(root.winfo_screenwidth() // CELL_SIZE) + 1

    row_view = max(0, min(TOTAL_ROWS - ROWS, center_row - ROWS // 2))
    col_view = max(0, min(TOTAL_COLS - COLS, center_col - COLS // 2))

    draw_grid()


def move(event):
    global row_view, col_view
    if event.keysym == "Up":
        row_view = max(0, row_view - 3)
    elif event.keysym == "Down":
        row_view = min(TOTAL_ROWS - ROWS, row_view + 3)
    elif event.keysym == "Left":
        col_view = max(0, col_view - 3)
    elif event.keysym == "Right":
        col_view = min(TOTAL_COLS - COLS, col_view + 3)
    draw_grid()
    

def onoff(event):
    if automata:
        pause()
    else:
        play()

def neighbours():
    global CELLS
    global RULES
    NEW_CELLS = [[0 for _ in range(TOTAL_COLS)] for _ in range(TOTAL_ROWS)]
    
    for row in range(TOTAL_ROWS):
        for col in range(TOTAL_COLS):
            current_state = CELLS[row][col]

            # collect neighbors
            vision = []
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr = (row + dr) % TOTAL_ROWS
                    nc = (col + dc) % TOTAL_COLS
                    vision.append(CELLS[nr][nc])
            neighbor_counts = Counter(vision)

            new_state = current_state

            for rule in RULES:
                if rule["current_state"] == current_state:
                    match = True
                    for cond in rule["conditions"]:
                        neighbor_count = neighbor_counts[cond["neighbor_state"]]
                        if not rel[cond["operator"]](neighbor_count, cond["count"]):
                            match = False
                            break
                    if match:
                        new_state = rule["next_state"]
                        break

            NEW_CELLS[row][col] = new_state
            
    CELLS = NEW_CELLS
    draw_grid()


canvas.bind("<Button-1>", toggle_cell)

root.bind("<MouseWheel>", zoom)
root.bind("<Button-5>", zoom)  
root.bind("<Button-4>", zoom)

root.bind("<Up>", move)
root.bind("<Down>", move)
root.bind("<Left>", move)
root.bind("<Right>", move)

root.bind("<space>", onoff)