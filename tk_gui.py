import dicom 
import tkinter as tk
from tkinter import *
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
import PySimpleGUI as sg

# for close button
def close():
    root.destroy()

# uploader
def diruploader():
    directory = tk.filedialog.askdirectory(master=root)
    return directory
def slider_changed(val):
    print(int(slider.get()))

# Set up tkinter
root = tk.Tk()
root.geometry('1618x500')

upload_button = tk.Button(root, text="click to upload dir")

# gets directory from user
if upload_button:
    dir = diruploader()

close_buton = tk.Button(root, text="close", command=close)
label = tk.Label(root, text=dir)
current_value = tk.IntVar()
slider = ttk.Scale(master=root, length=200, from_=0, to=100, orient='horizontal', variable=current_value, command=slider_changed)
entry=tk.Entry()
slider.pack()

study = dicom.DICOMStudy(dir)
image_array = study.get()
img = ImageTk.PhotoImage(image=Image.fromarray(image_array[slider]))


# i keep forgetting to pack :joy:
label.pack()
upload_button.pack()
close_buton.pack()


root.mainloop()

