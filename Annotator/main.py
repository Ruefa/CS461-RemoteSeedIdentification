
import tkinter as tk
from tkinter import Tk, Text, BOTH, W, N, E, S, filedialog
from tkinter.ttk import Frame, Button, Label, Style
from PIL import Image, ImageTk
import cv2
import os
import shutil
import xml.etree.cElementTree as et
import random
from datetime import datetime
import math
import ntpath
import sys
import numpy as np

# Add the classifier to the include files
sys.path.append("../Classifier/")

import torch
from ssd import build_ssd
import torch.nn as nn
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
import torch.utils.data as data
import torchvision.transforms as transforms
from torch.utils.serialization import load_lua

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

        self.class_select_label = tk.Label(self,text="Select a class: ", font='Helvetica 7 bold')
        self.class_select_label.grid(row=1, column=3, pady=(15, 0), sticky=W)

        self.autoann_label = tk.Label(self, text="Auto-annotation options:", font='Helvetica 7 bold')
        self.autoann_label.grid(row=3, column=3, pady=10, sticky=tk.NW)

        self.gen_bbox_button = tk.Button(self, text="Generate bounding boxes", command=self.gen_dataset_bboxes)
        self.gen_bbox_button.grid(row=3, column=3, sticky=tk.NW, pady=90)

        self.filter_empty = tk.IntVar(self.master)
        self.filter_empty_check  = tk.Checkbutton(self, text="Discard empty samples",
                                    variable=self.filter_empty)
        self.filter_empty_check.grid(row=3, column=3, sticky=tk.NW, pady=40)

        self.homogeneous = tk.IntVar(self.master)
        self.homogeneous_check = tk.Checkbutton(self, text="Homogeneous sample",
                                    variable=self.homogeneous)
        self.homogeneous_check.grid(row=3, column=3, sticky=tk.NW, pady=60)

        # Bind arrow key events
        self.bind('<Right>', self.next_sample)
        self.bind('<Left>', self.prev_sample)
        self.bind('s', self.save_annotation)
        self.bind('d', self.delete_sample)

        # Create image canvas
        self.canvas = tk.Canvas(self, width=300, height=300, background='white')
        self.canvas.grid(row=0, column=0, columnspan=2, rowspan=4,
                  pady=10, padx=10, sticky=tk.NW)
        self.image_on_canvas = self.canvas.create_image(0, 0, image=None)

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
        self.fileMenu.add_command(label="Load classifier...", command=self.load_classifier)
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

    def gen_dataset_bboxes(self):

        for img_file in self.dataset_filenames:

            # Load the image
            image = cv2.imread(self.dataset_dir+"/JPEGImages/"+img_file)

            # Convert to rgb
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Prepare image
            x = cv2.resize(rgb_image, (300, 300)).astype(np.float32)
            x -= (104.0, 117.0, 123.0)
            x = torch.from_numpy(x).permute(2, 0, 1)
            x = Variable(x.unsqueeze(0))

            if torch.cuda.is_available():
                x = x.cuda()

            # Evaluate network on image
            y = self.net(x)

            self.bounding_boxes.clear()

            # Record the bounding boxes
            scale = torch.Tensor([rgb_image.shape[1::-1], rgb_image.shape[1::-1]])
            for i in range(y.data.size(1)):

                j = 0
                while y.data[0, i, j, 0] >= 0.6:

                    pt = (y.data[0, i, j, 1:] * scale).cpu().numpy()
                    self.bounding_boxes.append([None, pt[0], pt[1], pt[2], pt[3]])
                    j += 1

            # Save the bounding boxes in xml format
            self.save_annotation()
            self.current_sample += 1

            print("Image " + img_file + " processed")

        self.bounding_boxes.clear()

        # Re-load the dataset
        self.load_dataset()


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

    def save_annotation(self, event=None):

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

    def delete_sample(self, event=None):

        if len(self.dataset_filenames) > 0:

            image_file = self.dataset_dir+"/JPEGImages/"+self.dataset_filenames[self.current_sample]
            annotation_file = self.dataset_dir+"/Annotations/"+self.dataset_filenames[self.current_sample].split(".")[0]+".xml"

            if os.path.isfile(image_file):

                os.remove(image_file)
                self.dataset_filenames.pop(self.current_sample)

                if self.current_sample == len(self.dataset_filenames):
                    self.current_sample -= 1

                if len(self.dataset_filenames) > 0:
                    self.load_sample(self.dataset_dir+"/JPEGImages/"+self.dataset_filenames[self.current_sample])
                else:
                    # self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.image_on_canvas = self.canvas.create_image(1, 1, anchor=tk.NW, image=None)
                    self.canvas.image = None
                    self.canvas.update()

            if os.path.isfile(annotation_file):
                os.remove(annotation_file)


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

        # Remove the previous data set
        if os.path.exists("SeedDatasetVOC"):
            shutil.rmtree("SeedDatasetVOC")

        # Create the data set folder tree
        os.makedirs("SeedDatasetVOC")
        os.makedirs("SeedDatasetVOC/Annotations")
        os.makedirs("SeedDatasetVOC/ImageSets")
        os.makedirs("SeedDatasetVOC/JPEGImages")

        # Create and partition the data set
        self.partition_raw_dataset_images(self.raw_images_path.get()+"/", "SeedDatasetVOC/", [int(self.slice_dim.get()), int(self.slice_dim.get()), 3])

        # Load the dataset into the annotator
        self.load_dataset("SeedDatasetVOC/")

        self.builder_window.destroy()

    def refresh_class_dropdown(self):

        self.current_class.set(self.seed_classes[0])

        # Reset var and delete all old options
        #self.classDropdown['menu'].delete(0, 'end')

        # Insert list of new options (tk._setit hooks them up to var)
        label = self.seed_classes[0]

        print(label)

        self.classDropdown['menu'].add_command(label=label, command=tk._setit(self.current_class, label))

    def add_class(self):

        self.seed_classes.insert(0, self.new_class.get())
        self.refresh_class_dropdown()
        self.class_window.destroy()

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
        self.image_on_canvas = self.canvas.create_image(1, 1, anchor=tk.NW, image=imgtk2)
        self.canvas.image = imgtk2

        self.canvas.update()
        self.load_annotation()

    def load_dataset(self, dir=None):

        if dir == None:
            self.dataset_dir = filedialog.askdirectory(initialdir="/", title='Please select a directory')
        else:
            self.dataset_dir = dir

        self.current_sample = 0

        self.dataset_filenames = [x[2] for x in os.walk(self.dataset_dir + "/JPEGImages/")][0]

        if len(self.dataset_filenames) > 0:
            self.load_sample(self.dataset_dir+"/JPEGImages/"+self.dataset_filenames[self.current_sample])

    def load_classifier(self):

        # Let the user choose the weights file
        self.classifier_weights_file = filedialog.askopenfile(initialdir="/", title="Select weight file", filetypes=[("Torch Model","*.pth")])

        # Create the SSD and load its weights
        self.net = build_ssd('test', 300, 3)
        self.net.load_weights(self.classifier_weights_file.name)

    def next_sample(self, event):

        if self.current_sample < len(self.dataset_filenames)-1:

            self.current_sample += 1
            self.bounding_boxes.clear()
            self.load_sample(self.dataset_dir+"/JPEGImages/"+self.dataset_filenames[self.current_sample])

    def prev_sample(self, event):

        if self.current_sample > 0:

            self.current_sample -= 1
            self.bounding_boxes.clear()
            self.load_sample(self.dataset_dir + "/JPEGImages/"+self.dataset_filenames[self.current_sample])

    def partition_image(self, image, shape):

        # Step half the shape dimension to avoid losing seeds on the edges
        partitions_x = math.floor(image.shape[0] / shape[0]) * 2
        partitions_y = math.floor(image.shape[1] / shape[1]) * 2

        image_set = []

        for x in range(partitions_x):
            for y in range(partitions_y):

                start_x = int(x * (shape[0] / 2))
                start_y = int(y * (shape[1] / 2))
                end_x = start_x + shape[0]
                end_y = start_y + shape[1]

                image_set.append(image[start_x:end_x, start_y:end_y, :])

        return image_set

    def partition_raw_dataset_images(self, raw_images_dir, dataset_dir, shape):

        train_images = []
        test_images = []
        val_images = []

        # Get the file names of the processed data
        filenames = [x[2] for x in os.walk(raw_images_dir)][0]

        # Add full path into file names
        filenames = [raw_images_dir + x for x in filenames]

        # Determine the size of each of the three sets
        num_train_elements = math.floor(len(filenames) * float(self.train_size.get()))
        num_test_elements = math.floor(len(filenames) * float(self.test_size.get()))
        num_val_elements = math.floor(len(filenames) * float(self.val_size.get()))

        # Randomly pick elements of the master set for each sub set
        self.pick_random_elements(filenames, train_images, num_train_elements)
        self.pick_random_elements(filenames, test_images, num_test_elements)
        self.pick_random_elements(filenames, val_images, num_val_elements)

        sets = [train_images, test_images, val_images]

        # Partion images and create VOC images set files
        for set in sets:

            for filename in set:

                partitions = self.partition_image(cv2.imread(filename), shape)

                image_count = 0

                for image in partitions:

                    cv2.imwrite(dataset_dir+"JPEGImages/"+ntpath.basename(filename).split(".",1)[0]+"_"+str(image_count)+".png", image)

                    image_count += 1

    def pick_random_elements(self, data_list, output_list, num_elements):

        # Seed the rand number generator
        random.seed(datetime.now())

        for element in range(0, num_elements):

            #Randomly pick an element to add to the set
            random_element = random.randint(0, len(data_list)-1)

            output_list.append(data_list[random_element])

            #Remove the element from our data set so it can't be picked again
            data_list.pop(random_element)

def main():

    # Use CUDA if available
    if torch.cuda.is_available():
        torch.set_default_tensor_type('torch.cuda.FloatTensor')

    root = Tk()
    root.focus_set()



    root.geometry("525x330+300+300")

    app = MainWindow()

    root.mainloop()


if __name__ == '__main__':
    main()