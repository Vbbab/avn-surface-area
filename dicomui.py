import tkinter as tk
import numpy as np
from tkinter import *
from tkinter import filedialog as fd
from PIL import ImageTk, Image 

import dicom

# Test imports start
import PIL.Image
import PIL.ImageTk
# Test imports end

IMAGE_WIDTH = 400
IMAGE_HEIGHT = 400

IMAGE_HOLDER_WIDTH = 400
IMAGE_HOLDER_HEIGHT = 400

class DICOMImgViewer(Frame):
    def __init__(self, master):
        self.study_dir = fd.askdirectory(master=master)
        print("study_dir:", self.study_dir)

        # Initialize DICOMStudy
        self.current_slice = 0
        self.dicom_study = dicom.DICOMStudy(self.study_dir)
        self.study_series = np.array(self.dicom_study.getSeries())
        self.dicom_slice_obj = self.dicom_study.get(self.study_series[0])
        self.dicom_array_length = len(self.dicom_slice_obj)
        self.slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array
        self.image = ImageTk.PhotoImage(image=Image.fromarray(self.slice_cv_array).resize((IMAGE_WIDTH, IMAGE_HEIGHT)))
        self.point_array = []
        

        # Setup the UI
        Frame.__init__(self, master)

        self.uiFrame = Frame(self)

        # Button to open an image file
        # Button(self.uiFrame, text="Open an Image File", command=self.open_image_file).pack(side=LEFT)
        # Button(self.uiFrame, text="Choose a directory").pack(side=LEFT)
        # Button to close the window
        #Button(self.uiFrame, text="Previous Slice", command=self.load_previous).pack(side=LEFT)
        #Button(self.uiFrame, text="Next Slice", command=self.load_next).pack(side=LEFT)
        Button(self.uiFrame, text = "delete all annotations", command = self.delete_all).pack(side=LEFT)
        Button(self.uiFrame, text="Close Window", command=self.close_window).pack(side=LEFT)
        Button(self.uiFrame, text="save annotations",command=self.save).pack(side=LEFT)
        # Label to hold the image
        self.image_holder = Label(self, width=IMAGE_HOLDER_WIDTH, height=IMAGE_HOLDER_HEIGHT)
        self.image_holder.pack()

        self.canvas = Canvas(master=self.image_holder, width=IMAGE_HOLDER_WIDTH, height=IMAGE_HOLDER_HEIGHT, bg="cyan")
        self.id_canvas_mouse_left_bind = self.canvas.bind("<Button-1>", self.on_mouse_left_click)
        self.id_canvas_mouse_right_bind = self.canvas.bind("<Button-3>", self.on_mouse_right_click)
        self.id_canvas_keyboard_back_bind = master.bind('q', self.load_previous)
        self.id_canvas_keyboard_back_bind = master.bind('w', self.load_next)
        self.canvas.pack(side=LEFT)

        self.uiFrame.pack(side=TOP, fill=BOTH)
        self.pack()

        self.show_image()

        # Initialize annotation marker variables
        self.reset_annotation_markers()

    def reset_annotation_markers(self):
        self.line_start_x = 0
        self.line_start_y = 0
        self.line_end_x = 0
        self.line_end_y = 0
        
    def open_image_file(self):
        filename = fd.askopenfilename()
        if filename != "":
            self.image_obj = PIL.Image.open(filename)
        self.image = PIL.ImageTk.PhotoImage(self.image_obj.resize((IMAGE_WIDTH, IMAGE_HEIGHT)))
        self.show_image()
    
    def load_previous(self, _useless):
        self.current_slice = self.current_slice - 1;
        if self.current_slice < 0:
            self.current_slice = (self.dicom_array_length-1)
        self.slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array
        self.image = ImageTk.PhotoImage(image=Image.fromarray(self.slice_cv_array).resize((IMAGE_WIDTH, IMAGE_HEIGHT)))
        self.show_image()

    def load_next(self, _useless):
        self.current_slice = self.current_slice + 1;
        if self.current_slice > (self.dicom_array_length-1):
            self.current_slice = 0
        self.slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array
        self.image = ImageTk.PhotoImage(image=Image.fromarray(self.slice_cv_array).resize((IMAGE_WIDTH, IMAGE_HEIGHT)))
        self.show_image()

    def show_image(self):        
        # self.image_holder.config(image=self.image, bg="#000000")
        # print(self.image_obj.n_frames)
        canvas_img = self.canvas.create_image(200, 200, image=self.image)
        self.canvas.itemconfig(canvas_img, image=self.image)

    def on_mouse_left_click(self, event):
        print(event)
        self.point_array = []
        self.line_start_x = event.x
        self.line_start_y = event.y
        self.start_tuple = (event.x, event.y)
        self.point_array.append(self.start_tuple)

    def on_mouse_right_click(self, event):
        print(event)
        self.line_end_x = event.x
        self.line_end_y = event.y
        self.print_annotation_markers()
        self.annotation_line = self.canvas.create_line(self.line_start_x, self.line_start_y, self.line_end_x, self.line_end_y, fill="red", tag='my_line')
        self.line_start_x = event.x
        self.line_start_y = event.y
        self.next_tuple = (event.x, event.y)
        self.point_array.append(self.next_tuple)
        print(self.point_array)
        self.canvas.pack()
        #self.reset_annotation_markers()
    
    def save(self):
        dicom.DICOMConstants.addPoints(self.dicom_slice_obj, self.point_array)

    def delete_all(self):
        self.canvas.delete('my_line')

    def close_window(self):
        self.master.destroy()
        self.point_array = []

    # Debug functions
    def print_annotation_markers(self):
        print(self.line_start_x, self.line_start_y, self.line_end_x, self.line_end_y)

if __name__ == "__main__":
    root_window = tk.Tk()
    root_window.geometry('1280x720')
    dicom_viewer = DICOMImgViewer(master=root_window)
    root_window.mainloop()
