import tkinter as tk

def keypad(parent_window, x, y):
    keypad_window = tk.Frame(parent_window, bd=2, relief="raised")
    keypad_window.place(x=x, y=y)
    result = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    def press(btn, index):
        if result[index]<1:
            btn.config(bg = 'grey')
            result[index]+=1
        else:
            btn.config(bg = 'white')
            result[index]-=1
    
    
    buttons = [
        '', '', '',
        '', '', '',
        '', '', ''
    ]


    for index, button in enumerate(buttons):
        row_val = index // 3
        col_val = index % 3
        
        btn_widget = tk.Button(keypad_window, text=button, width=5, height=3, font=("Arial", 5), bg='white')
        btn_widget.config(command=lambda b=btn_widget, i=index: press(b, i))
        btn_widget.grid(row=row_val, column=col_val, padx=0, pady=0)

        col_val += 1
        if col_val > 2:
            col_val = 0
            row_val += 1

    return(result)
