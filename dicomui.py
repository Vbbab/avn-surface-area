import ttkbootstrap as ttk
import numpy as np
from tkinter import *
from tkinter import filedialog as fd
from PIL import ImageTk, Image
import shutil 

from ttkbootstrap.window import tkinter 

from annotated import Annotated
import dicom
import surface_area

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
        print("study_dir: ", self.study_dir)

        # Initialize DICOMStudy
        self.current_slice = 0
        self.dicom_study = dicom.DICOMStudy(self.study_dir)
        self.study_series = np.array(self.dicom_study.getSeries())
        self.dicom_slice_obj = self.dicom_study.get(self.study_series[0])
        self.slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array.copy()
        self.array_preprocessing()
        self.dicom_array_length = len(self.dicom_slice_obj)
        self.image = ImageTk.PhotoImage(image=Image.fromarray(self.slice_cv_array).resize((IMAGE_WIDTH, IMAGE_HEIGHT)))
        self.point_array = []
        self.SAButton = None

        self.anpts = []
        

        # Setup the UI
        Frame.__init__(self, master)

        self.uiFrame = Frame(self, width=600, height=600)

        # Button to open an image file
        # Button(self.uiFrame, text="Open an Image File", command=self.open_image_file).pack(side=LEFT)
        # Button(self.uiFrame, text="Choose a directory").pack(side=LEFT)
        # Button to close the window
        #Button(self.uiFrame, text="Previous Slice", command=self.load_previous).pack(side=LEFT)
        #Button(self.uiFrame, text="Next Slice", command=self.load_next).pack(side=LEFT)
        Button(self.uiFrame, text = "Delete All Annotations", command = self.delete_all).pack(side=LEFT)
        Button(self.uiFrame, text="Close Window", command=self.close_window).pack(side=LEFT)
        Button(self.uiFrame, text="Save to Disk", command=self.save_to_disk).pack(side=LEFT)
        Button(self.uiFrame, text="Remove Annotated Files", command=self.delete_anfiles).pack(side=LEFT)
        
        # Label to hold the image
        self.image_holder = Label(self, width=IMAGE_HOLDER_WIDTH, height=IMAGE_HOLDER_HEIGHT)
        self.image_holder.pack()
        self.surface_area = 0.0 

        self.canvas = Canvas(master=self.image_holder, width=IMAGE_HOLDER_WIDTH, height=IMAGE_HOLDER_HEIGHT, bg="black")
        self.s_area_button = Button(master=self.uiFrame, text="Get Surface Area", command=self.surf_area_disp)
        print(self.surface_area)
        
        self.id_canvas_mouse_left_bind = self.canvas.bind("<Button-1>", self.on_mouse_left_click)
        self.id_canvas_mouse_right_bind = self.canvas.bind("<Button-3>", self.on_mouse_right_click)
        self.id_canvas_keyboard_back_bind = master.bind('q', self.load_previous)
        self.id_canvas_keyboard_forward_bind = master.bind('w', self.load_next)
        self.save_keyboard_bind = master.bind('e', self.save)
        self.undo_keyboard_bind = master.bind('u', self.undo)
        self.canvas.pack()
        
        self.s_area_button.pack()
        self.uiFrame.pack(side=TOP, fill=BOTH)
        self.pack()

        self.show_image()
        self.load_annotations()

        # Initialize annotation marker variables
        self.reset_annotation_markers()
    
    def load_annotations(self):
        try:
            self.anpts = Annotated(self.dicom_slice_obj[self.current_slice]).getPoints()
            self.show_annotations()
            print(str(self.current_slice) + " annotated")
            # print(self.anpts)
        except ValueError:
            print(str(self.current_slice) + " not annotated")
        
        self.reset_annotation_markers()

    def array_preprocessing(self):
        self.slice_cv_array = self.slice_cv_array / np.max(self.slice_cv_array)
        self.slice_cv_array = (self.slice_cv_array*255).astype(np.uint8)
    
    def delete_anfiles(self):
        shutil.rmtree("./annotated_dicom_files")

    def save_to_disk(self):
        try:
            dicom.DICOMConstants.save(self.dicom_slice_obj, './annotated_dicom_files')
            print("saved!")
        except FileExistsError:
            print("folder already exists!")

    def reset_annotation_markers(self):
        self.line_start_x = ttk.IntVar()
        self.line_start_y = ttk.IntVar()
        self.line_end_x = ttk.IntVar()
        self.line_end_y = ttk.IntVar()
        
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
        self.slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array.copy()
        self.array_preprocessing()
        self.image = ImageTk.PhotoImage(image=Image.fromarray(self.slice_cv_array).resize((IMAGE_WIDTH, IMAGE_HEIGHT)))
        self.show_image()
        self.load_annotations() 

    def load_next(self, _useless):
        self.current_slice = self.current_slice + 1;
        if self.current_slice > (self.dicom_array_length-1):
            self.current_slice = 0
        self.slice_cv_array = (self.dicom_slice_obj[self.current_slice]).pixel_array.copy()
        self.array_preprocessing()
        self.image = ImageTk.PhotoImage(image=Image.fromarray(self.slice_cv_array).resize((IMAGE_WIDTH, IMAGE_HEIGHT)))
        self.show_image()
        self.load_annotations()
        

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
        self.start_tuple = (self.line_start_x, self.line_start_y)
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
        self.canvas.pack()
        #self.reset_annotation_markers()
    
    def undo(self, _useless):
        self.point_array.remove(self.point_array[(len(self.point_array))-1])
        self.canvas.delete('my_line')
        for i in range(len(self.point_array)-1):
            self.canvas.create_line(self.point_array[i][0], self.point_array[i][1], self.point_array[i+1][0], self.point_array[i+1][1], fill="red", tag='my_line')
        self.line_start_x = self.point_array[len(self.point_array)-1][0] 
        self.line_start_y = self.point_array[len(self.point_array)-1][1] 
    
    def save(self, _useless):
        dicom.DICOMConstants.addPoints(self.dicom_slice_obj[self.current_slice], self.point_array)
        print("saved!")

    def delete_all(self):
        self.canvas.delete('my_line')
        dicom.DICOMConstants.clearAnnotations(self.dicom_slice_obj[self.current_slice])
        print("deleted all annotations!")
        
    def close_window(self):
        self.master.destroy()
        self.point_array = []

    # Debug functions
    def print_annotation_markers(self):
        print(self.line_start_x, self.line_start_y, self.line_end_x, self.line_end_y)

    def show_annotations(self):
        for i in range(len(self.anpts)-1):
            self.canvas.create_line(self.anpts[i][0], self.anpts[i][1], self.anpts[i+1][0], self.anpts[i+1][1], fill="#66ff00", tag='my_line')

    def surf_area_disp(self):
        try:
            self.surf_area_obj = surface_area.SurfaceArea(self.dicom_study, self.study_series[0])
            self.surface_area = self.surf_area_obj.getArea()
            if self.SAButton == None:
                self.SAButton = Button(master=self.uiFrame, text="Surface area in cm²: " + str((round(((self.surface_area)/100), 3))))
                self.SAButton.pack(side=LEFT)
                print(self.surface_area)
            

        except ValueError:
            print("sth not annotated!")


# main tk window
if __name__ == "__main__":
    root_window = ttk.Window(themename='pulse')
    root_window.geometry('900x470')
    dicom_viewer = DICOMImgViewer(master=root_window)
    root_window.mainloop()
