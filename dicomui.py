import tkinter as tk
import numpy as np
from tkinter import *
from tkinter import filedialog
from PIL import ImageTk, Image

import dicom

# Test imports start
import PIL.Image
import PIL.ImageTk
# Test imports end

class DICOMImgViewer(Frame):
    def __init__(self, master = None, study_dir = None):
        print("study_dir:", study_dir)

        # Initialize DICOMStudy
        self.current_slice = 0
        self.dicom_study = dicom.DICOMStudy(study_dir)
        self.study_series = np.array(self.dicom_study.getSeries())
        self.dicom_slice_obj = self.dicom_study.get(self.study_series[0])
        self.dicom_array_length = len(self.dicom_slice_obj)
        slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array
        self.image = ImageTk.PhotoImage(image=Image.fromarray(slice_cv_array).resize((300, 300)))
         

        # Setup the UI
        Frame.__init__(self, master)
        self.master.title("DICOM Image Viewer")

        self.uiFrame = Frame(self)

        # Button to open an image file
        # Button(self.uiFrame, text="Open an Image File", command=self.open_image_file).pack(side=LEFT)
        # Button(self.uiFrame, text="Choose a directory").pack(side=LEFT)
        # Button to close the window
        Button(self.uiFrame, text="Previous Slice", command=self.load_previous).pack(side=LEFT)
        Button(self.uiFrame, text="Next Slice", command=self.load_next).pack(side=LEFT)
        Button(self.uiFrame, text="Close Window", command=self.close_window).pack(side=LEFT)
         


        # Lable to hold the image
        self.image_holder = Label(self)
        self.image_holder.pack()
        
        
        self.uiFrame.pack(side=TOP, fill=BOTH)
        self.pack()

        self.show_image()
        
    def open_image_file(self):
        filename = filedialog.askopenfilename()
        if filename != "":
            self.image_obj = PIL.Image.open(filename)
        self.image = PIL.ImageTk.PhotoImage(self.image_obj.resize((300, 300)))
        self.show_image()
    
    def load_previous(self):
        self.current_slice = self.current_slice - 1;
        if self.current_slice < 0:
            self.current_slice = 0
        print("previous slice!")
        slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array
     
        self.image = ImageTk.PhotoImage(image=Image.fromarray(slice_cv_array).resize((300, 300)))
        self.show_image()
        

    def load_next(self):
        self.current_slice = self.current_slice + 1;
        if self.current_slice > (self.dicom_array_length-1):
            self.current_slice =  (self.dicom_array_length-1)
        print("next slice!")
        slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array
        self.image = ImageTk.PhotoImage(image=Image.fromarray(slice_cv_array).resize((300, 300)))
        self.show_image()
        

    def show_image(self):        
        self.image_holder.config(image=self.image, bg="#000000")
        # print(self.image_obj.n_frames)

    def close_window(self):
        self.master.destroy()

if __name__ == "__main__":

    dir = "/home/chaas/neovim/avn-surface-area/COVID-19-NY-SBU/11-28-1900-NA-MRI ABD WWO IV CONT-05790/2.000000-T2 HASTE AX-39240" 
    root_window = tk.Tk()
    root_window.geometry('1280x768')
    dicom_viewer = DICOMImgViewer(master=root_window, study_dir=dir)
    root_window.mainloop()
