import tkinter as tk
from tkinter import Tk, Text, BOTH, W, N, E, S, filedialog
from tkinter.ttk import Frame, Button, Label, Style
from PIL import Image, ImageTk
import cv2
import os
import xml.etree.cElementTree as et

# Minimum area required to draw a bounding box
MIN_AREA = 500

# The application
app = None

# Defaults for the dataset builder
DEFAULT_SLICE_DIM = 300
DEFAULT_TRAIN_SIZE = 0.85
DEFAULT_TEST_SIZE = 0.1
DEFAULT_VAL_SIZE = 0.05

class MainWindow(Frame):

    # Directory of the dataset
    dataset_dir = ""

    # Get list of filenames in directory
    dataset_filenames = []

    # Index of the sample currently being annotated
    current_sample = 0

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.master.title("Seed Annotator")
        self.pack(fill=BOTH, expand=True)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, pad=7)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, pad=7)

        # Create class drop down
        self.seed_classes = ['Add a new class...']

        self.current_class = tk.StringVar(self.master)
        self.current_class.set(self.seed_classes[0])
        self.classDropdown = tk.OptionMenu(self, self.current_class, *self.seed_classes, command=self.dropdown_callback)
        self.classDropdown.config(width=15)
        self.classDropdown.grid(row=2, column=3, pady=5, sticky=W)

        self.class_select_label = tk.Label(self,text="Select a class: ")
        self.class_select_label.grid(row=1, column=3, pady=(15,0),stick=W)

        self.autosave = tk.BooleanVar(self.master)
        self.autosave_radio  = tk.Radiobutton(self, text="Autosave",
                        variable=self.autosave, value=False)
        self.autosave_radio.grid(row=3, column=3, sticky=tk.NW)

        self.homogeneous = tk.BooleanVar(self.master)
        self.homogeneous_radio = tk.Radiobutton(self, text="Homogeneous sample",
                                             variable=self.homogeneous, value=False)
        self.homogeneous_radio.grid(row=3, column=3, sticky=tk.NW,pady=20)

        # Bind arrow key events
        self.bind('<Right>', self.next_sample)
        self.bind('<Left>', self.prev_sample)
        self.bind('s', self.save_annotation)

        # Create image canvas
        self.canvas = tk.Canvas(self, width=512, height=512, background='white')
        self.canvas.grid(row=0, column=0, columnspan=2, rowspan=4,
                  pady=10, padx=10, sticky=N)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=None)

        # Create canvas mouse handlers for rectangles
        self.canvas.bind("<Button-1>", self.startRect)
        self.canvas.bind("<ButtonRelease-1>", self.stopRect)
        self.canvas.bind("<Motion>", self.movingRect)
        self.canvas.bind("<Button-3>", self.deleteRect)

        # Create canvas variables for bbox drawing
        self.rectx0 = 0
        self.recty0 = 0
        self.rectx1 = 0
        self.recty1 = 0
        self.rectid = None
        self.drawing = False
        self.bounding_boxes = []
        self.object_offset = 0

        # Create menu bar
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # Create file menu and add to menu bar
        self.fileMenu = tk.Menu(self.menubar, tearoff=0)
        self.fileMenu.add_command(label="Load dataset directory...", command=self.load_dataset)
        self.fileMenu.add_command(label="Load classifier...", command=self.quit)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)

        # Create tool menu and add to menu bar
        self.toolMenu = tk.Menu(self.menubar,tearoff=0)
        self.toolMenu.add_command(label="Build dataset...", command=self.create_builder_window)
        self.menubar.add_cascade(label="Tools", menu=self.toolMenu)

        # Create help menu and add to menu bar
        self.helpMenu = tk.Menu(self.menubar, tearoff=0)
        self.helpMenu.add_command(label="How to use...", command=self.quit)
        self.helpMenu.add_command(label="About...", command=self.quit)
        self.menubar.add_cascade(label="Help", menu=self.helpMenu)

        self.focus_set()

    def create_class_window(self):

        self.class_window = tk.Toplevel(self)

        # Stores the value of the new class to be added
        self.new_class = tk.StringVar()

        # Create title
        self.class_window.wm_title("New class")

        # Add label
        tk.Label(self.class_window, text="Enter a new class: ", pady=10).grid(row=0)

        # Add entry
        entry = tk.Entry(self.class_window, textvariable=self.new_class)
        entry.grid(row=0, column=1)

        # Add button
        tk.Button(self.class_window, text="OK",command=self.add_class).grid(row=0, column=2, padx=10)

        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty()
        self.class_window.geometry("350x40+%d+%d" % (x, y))

    def save_annotation(self, event):

        annotation = et.Element("annotation")

        size = et.SubElement(annotation, "size")

        et.SubElement(annotation,"segmented").text = "0"
        et.SubElement(size, "width").text = str(self.canvas.image.width())
        et.SubElement(size, "height").text = str(self.canvas.image.height())
        et.SubElement(size, "depth").text = "3"

        for bbox in self.bounding_boxes:

            object = et.SubElement(annotation, "object")
            bndbox = et.SubElement(object, "bndbox")

            et.SubElement(object, "name").text = self.current_class.get()
            et.SubElement(object, "pose").text = "Unspecified"
            et.SubElement(object, "truncated").text = "0"
            et.SubElement(object, "difficult").text = "0"

            et.SubElement(bndbox, "xmin").text = str(bbox[1])
            et.SubElement(bndbox, "ymin").text = str(bbox[2])
            et.SubElement(bndbox, "xmax").text = str(bbox[3])
            et.SubElement(bndbox, "ymax").text = str(bbox[4])

        tree = et.ElementTree(annotation)
        tree.write(self.dataset_dir+"/Annotations/"+self.dataset_filenames[self.current_sample].split(".")[0]+".xml")

    def load_annotation(self):

        path = self.dataset_dir+"/Annotations/"+self.dataset_filenames[self.current_sample].split(".")[0]+".xml"

        rectids = []

        if os.path.isfile(path):

            tree = et.parse(path)
            root = tree.getroot()

            for child in root:
                if child.tag == "object":
                    for gchild in child:
                        if gchild.tag == "bndbox":
                            xmin = float(gchild.find("xmin").text)
                            ymin = float(gchild.find("ymin").text)
                            xmax = float(gchild.find("xmax").text)
                            ymax = float(gchild.find("ymax").text)

                            # Create rectangle
                            self.rect = self.canvas.create_rectangle(
                            xmin, ymin, xmax, ymax, fill=None, width=2)

                            # Get rectangle's canvas object ID
                            self.rectid = self.canvas.find_closest(xmin, ymin, halo=2)

                            # Append box to bounding boxes
                            self.bounding_boxes.append([self.rectid, xmin, ymin, xmax, ymax])


    def dropdown_callback(self, item):

        print(item)
        if item == "Add a new class...":

            self.create_class_window()

    def create_builder_window(self):

        self.builder_window = tk.Toplevel(self)

        # Create title
        self.builder_window.wm_title("Build dataset")

        # Create variables for dataset builder
        self.raw_images_path = tk.StringVar()
        self.slice_dim = tk.StringVar()
        self.train_size = tk.StringVar()
        self.test_size = tk.StringVar()
        self.val_size = tk.StringVar()

        self.raw_images_path.set("Select a path...")
        self.slice_dim.set(str(DEFAULT_SLICE_DIM))
        self.train_size.set(str(DEFAULT_TRAIN_SIZE))
        self.test_size.set(str(DEFAULT_TEST_SIZE))
        self.val_size.set(str(DEFAULT_VAL_SIZE))

        # Add labels
        tk.Label(self.builder_window, text="Slice pixel dimension", pady=10, padx=10).grid(row=0, stick=W)
        tk.Label(self.builder_window, text="Training set size:", pady=10, padx=10).grid(row=1, stick=W)
        tk.Label(self.builder_window, text="Testing set size:", pady=10, padx=10).grid(row=2, stick=W)
        tk.Label(self.builder_window, text="Validation set size:", pady=10, padx=10).grid(row=3, stick=W)
        tk.Label(self.builder_window, text="Raw image path", pady=10, padx=10).grid(row=4, stick=W)

        # Add entries
        raw_images_path_entry = tk.Entry(self.builder_window, textvariable=self.raw_images_path, justify=tk.CENTER)
        slice_dim_entry = tk.Entry(self.builder_window, textvariable=self.slice_dim, justify=tk.CENTER)
        train_size_entry = tk.Entry(self.builder_window, textvariable=self.train_size, justify=tk.CENTER)
        test_size_entry = tk.Entry(self.builder_window, textvariable=self.test_size, justify=tk.CENTER)
        val_size_entry = tk.Entry(self.builder_window, textvariable=self.val_size, justify=tk.CENTER)

        # Bind click event for selecting dataset
        raw_images_path_entry.bind("<1>", self.select_raw_images_path)

        slice_dim_entry.grid(row=0, column=1, sticky=W)
        train_size_entry.grid(row=1, column=1, sticky=W)
        test_size_entry.grid(row=2, column=1, sticky=W)
        val_size_entry.grid(row=3, column=1, sticky=W)
        raw_images_path_entry.grid(row=4, column=1, sticky=W)

        # Add button
        tk.Button(self.builder_window, text="OK", command=self.build_dataset).grid(row=5, column=1, sticky=E)

        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty()
        self.builder_window.geometry("330x220+%d+%d" % (x, y))

    def select_raw_images_path(self, event):

        # Get the directory of the raw dataset
        self.raw_images_path.set(filedialog.askdirectory(initialdir="/", title='Please select a directory'))

        # Bring builder window back to the front
        self.builder_window.lift()

    def build_dataset(self):

        print("Building dataset...")

    def refresh_class_dropdown(self):

        self.current_class.set(self.seed_classes[0])

        # Reset var and delete all old options
        self.classDropdown['menu'].delete(0, 'end')

        # Insert list of new options (tk._setit hooks them up to var)
        for c in self.seed_classes:
            self.classDropdown['menu'].add_command(label=c, command=tk._setit(self.current_class, c))

    def add_class(self):

        self.seed_classes.insert(0, self.new_class.get())
        self.refresh_class_dropdown()
        self.t.destroy()

    def startRect(self, event):

        self.drawing = True

        # Translate mouse screen x0,y0 coordinates to canvas coordinates
        self.rectx0 = self.canvas.canvasx(event.x)
        self.recty0 = self.canvas.canvasy(event.y)

        # Create rectangle
        self.rect = self.canvas.create_rectangle(
            self.rectx0, self.recty0, self.rectx0, self.recty0, fill=None, width=2)

        # Get rectangle's canvas object ID
        self.rectid = self.canvas.find_closest(self.rectx0, self.recty0, halo=2)

    def mouse_over(self, x, y, coords):

        if coords[2] > x > coords[0] and coords[3] > y > coords[1]:
            return True

        return False

    def movingRect(self, event):

        mx = self.canvas.canvasx(event.x)
        my = self.canvas.canvasy(event.y)

        if self.drawing:

            # Translate mouse screen x1,y1 coordinates to canvas coordinates

            self.rectx1 = mx
            self.recty1 = my

            # Modify rectangle x1, y1 coordinates
            self.canvas.coords(self.rectid, self.rectx0, self.recty0,
                               self.rectx1, self.recty1)

        else:

            # Check for hover of each bbox
            for bbox in self.bounding_boxes:

                if self.mouse_over(mx,my,bbox[1:5]):
                        self.canvas.itemconfigure(bbox[0][0], outline="red")
                        outlined=True
                else:
                    self.canvas.itemconfigure(bbox[0][0], outline="black")

    def stopRect(self, event):

        self.drawing = False

        # Translate mouse to canvas coordinates

        self.rectx1 = self.canvas.canvasx(event.x)
        self.recty1 = self.canvas.canvasy(event.y)

        # Translate bbox cords to AD notation
        #
        #   A    B
        #    \
        #     \
        #      \
        #   C    D
        #

        if self.rectx0 > self.rectx1 and self.recty0 < self.recty1:
            coords = (self.rectx1,self.recty0,self.rectx0,self.recty1)
        elif self.rectx0 > self.rectx1 and self.recty0 > self.recty1:
            coords = (self.rectx1, self.recty1, self.rectx0, self.recty0)
        elif self.rectx0 < self.rectx1 and self.recty0 > self.recty1:
            coords = (self.rectx0, self.recty1, self.rectx1, self.recty0)
        else:
            coords = (self.rectx0, self.recty0, self.rectx1, self.recty1)

        # Only draw box if area is big enough to avoid annoying small boxes
        if (coords[2]-coords[0])*(coords[3]-coords[1]) > MIN_AREA:
            self.bounding_boxes.append([self.rectid, coords[0], coords[1], coords[2], coords[3]])
        else:
            self.canvas.delete(self.rectid)

    def deleteRect(self, event):

        mx = self.canvas.canvasx(event.x)
        my = self.canvas.canvasy(event.y)

        # Check for hover of each bbox
        for bbox in self.bounding_boxes:

            if self.mouse_over(mx, my, bbox[1:5]):
                self.canvas.delete(bbox[0][0])

    def load_sample(self, filename):

        # Read image and change color format for tkinter
        img2 = cv2.imread(filename)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

        # Convert the opencv image to tkinter compatible form
        im2 = Image.fromarray(img2)
        imgtk2 = ImageTk.PhotoImage(image=im2)

        #self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk2)
        self.canvas.image = imgtk2

        self.canvas.update()
        self.load_annotation()

    def load_dataset(self):

        self.dataset_dir = filedialog.askdirectory(initialdir="/", title='Please select a directory')
        self.dataset_filenames = [x[2] for x in os.walk(self.dataset_dir + "/JPEGImages/")][0]

        self.load_sample(self.dataset_dir+"/JPEGImages/"+self.dataset_filenames[self.current_sample])

    def next_sample(self, event):

        if self.current_sample < len(self.dataset_filenames):

            self.current_sample += 1
            self.bounding_boxes.clear()
            self.load_sample(self.dataset_dir+"/JPEGImages/"+self.dataset_filenames[self.current_sample])

    def prev_sample(self, event):

        if self.current_sample > 0:

            self.current_sample -= 1
            self.bounding_boxes.clear()
            self.load_sample(self.dataset_dir + "/JPEGImages/"+self.dataset_filenames[self.current_sample])

def main():


    root = Tk()
    root.focus_set()

    #img = cv2.imread("/home/ethan/Documents/deeplearning/ssd/pytorch/VOCdevkit/VOC2007/JPEGImages/IMG_1205_1.png")
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    #im = Image.fromarray(img)
    #imgtk = ImageTk.PhotoImage(image=im)

    root.geometry("700x545+300+300")

    app = MainWindow()

    #app.canvas.itemconfig(app.image_on_canvas, image=imgtk)

    root.mainloop()


if __name__ == '__main__':
    main()