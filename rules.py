import tkinter as tk

def create_rule(parent, x, y, states):
    selected1 = tk.StringVar(value=states[0] if states else "")
    selected2 = tk.StringVar(value=states[0] if states else "")
    selected_op = tk.StringVar(value="==")
    spin_val = tk.IntVar(value=0)

    dropdown1 = tk.OptionMenu(parent, selected1, *states)
    dropdown1.place(x=x, y=y, width=100, height=25)

    dropdown2 = tk.OptionMenu(parent, selected2, *states)
    dropdown2.place(x=x+110, y=y, width=100, height=25)

    ops = [">", "<", ">=", "<=", "==", "!="]
    dropdown_op = tk.OptionMenu(parent, selected_op, *ops)
    dropdown_op.place(x=x+220, y=y, width=60, height=25)

    spinbox = tk.Spinbox(parent, from_=0, to=8, textvariable=spin_val, width=3)
    spinbox.place(x=x+290, y=y, width=40, height=25)

    label = tk.Label(parent, text="neighbors")
    label.place(x=x+340, y=y, width=70, height=25)

    return {"current_state": selected1.get(), "conditions": [{"neighbor_state": selected2.get(), "operator": selected_op.get(), "count": int(spin_val.get())}], "next_state": selected2.get()}