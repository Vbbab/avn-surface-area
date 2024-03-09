#dicomui.py is the actual ui now

import dicom 
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as filedialog
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk

root = tk.Tk()
root.geometry('1000x1000')

s_value = 1
 
# for close button
def close():
    root.destroy()

# uploader
def diruploader():
    directory = filedialog.askdirectory(master=root)
    return directory

# returns slider value when slider changes
class s_value_holder:
    def __init__(self):
        self.s_value = 10
        #print(val)
    def slider_changed(self, val):
        self.s_value = int(slider.get())
    def get_variable(self):
        print(self.s_value)
        return self.s_value

# Set up tkinter

#upload_button = tk.Button(root, text="upload dir")

# gets directory from user
#if upload_button:
    #dir = diruploader()
dir = "/home/chaas/neovim/avn-surface-area/COVID-19-NY-SBU/11-28-1900-NA-MRI ABD WWO IV CONT-05790/2.000000-T2 HASTE AX-39240"

close_buton = tk.Button(root, text="close", command=close)
label = tk.Label(root, text=dir)
study = dicom.DICOMStudy(dir)
series_array = np.array(study.getSeries())
# print(current_value)
canvas = tk.Canvas(root,width=500,height=500)
array = study.get(series_array[0])
current_value = tk.IntVar()
indexval = s_value_holder()
slider = ttk.Scale(master=root, length=200, from_=0, to=40, orient='horizontal', variable=current_value, command = indexval.slider_changed)


slice_cv_array = (array[indexval.get_variable()]).pixel_array
img = ImageTk.PhotoImage(image=Image.fromarray(slice_cv_array))
displayimg = canvas.create_image(0,0, anchor="nw", image=img)
canvas.itemconfig(displayimg, image=img)

entry=tk.Entry()


# i keep forgetting to pack :joy:
label.pack()
#upload_button.pack()
close_buton.pack()
canvas.pack()
slider.pack()

root.mainloop()

