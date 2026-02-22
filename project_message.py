import tkinter as tk
from tkinter import simpledialog
import random
import itertools

PASSWORD = "1234"

# Setup window
root = tk.Tk()
root.title("PROJECT ONGOING")
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg='black')

# Warning text with scary emojis
text = "☠️💀⚠️ PROJECT ONGOING – DO NOT USE ⚠️💀☠️"
label = tk.Label(root, text=text, font=("Consolas", 72, "bold"), fg="red", bg="black")
label.place(x=100, y=100)  # initial position

# Colors for flicker
colors = ['red', 'darkred', 'orange', 'white']
color_cycle = itertools.cycle(colors)

# Flicker effect
def flicker():
    label.config(fg=next(color_cycle))
    root.after(100, flicker)

# Pulse effect
scale_direction = 1
def pulse():
    global scale_direction
    size = label.cget("font").split()[1]
    size = int(size)
    size += scale_direction * 2
    if size >= 90 or size <= 60:
        scale_direction *= -1
    label.config(font=("Consolas", size, "bold"))
    root.after(100, pulse)

# Random jump effect
def jump():
    x = random.randint(0, root.winfo_screenwidth() - 800)
    y = random.randint(0, root.winfo_screenheight() - 200)
    label.place(x=x, y=y)
    root.after(500, jump)

# Intercept all key presses except Ctrl+C
def key_press(event):
    if event.keysym == 'c' and (event.state & 0x4):  # Ctrl+C
        root.destroy()
        return
    pw = simpledialog.askstring("Password Required", "Enter password to dismiss:", show="*")
    if pw == PASSWORD:
        root.destroy()

root.bind("<Key>", key_press)

flicker()
pulse()
jump()
root.mainloop()