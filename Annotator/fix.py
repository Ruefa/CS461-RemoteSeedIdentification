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

dataset_dir = "/home/ethan/Documents/school/cs462/CS461-RemoteSeedIdentification/Annotator/SeedDatasetVOC"
raw_images_dir = "/home/ethan/Documents/school/cs462/CS461-RemoteSeedIdentification/Annotator/raw_images/tf/"


def pick_random_elements(data_list, output_list, num_elements):
    # Seed the rand number generator
    random.seed(datetime.now())

    for element in range(0, num_elements):
        # Randomly pick an element to add to the set
        random_element = random.randint(0, len(data_list) - 1)

        output_list.append(data_list[random_element])

        # Remove the element from our data set so it can't be picked again
        data_list.pop(random_element)


def load_imagesets():
    # Reset imagesets
    imagesets = [[], [], [], []]

    # Open imageset files
    train_file = open(dataset_dir + "/ImageSets/Main/train.txt", "r")
    val_file = open(dataset_dir + "/ImageSets/Main/val.txt", "r")
    test_file = open(dataset_dir + "/ImageSets/Main/test.txt", "r")
    trainval_file = open(dataset_dir + "/ImageSets/Main/trainval.txt", "r")

    files = [train_file, val_file, test_file, trainval_file]

    set_count = 0

    for file in files:
        for line in file.readlines():
            imagesets[set_count].append(line.rstrip('\n'))

        set_count += 1

def get_annotation_names():

    imgs = []

    filenames = [x[2] for x in os.walk(dataset_dir + "/Annotations/")][0]

    for file in filenames:
        imgs.append(file.split(".")[0])

    return imgs

def get_sets():

    train_images = []
    test_images = []
    val_images = []
    slice_names = []

    # Get the file names of the processed data
    filenames = [x[2] for x in os.walk(raw_images_dir)][0]

    # Add full path into file names
    filenames = [raw_images_dir + x for x in filenames]

    # Determine the size of each of the three sets
    num_train_elements = 20
    num_test_elements = 0
    num_val_elements = 2

    # Randomly pick elements of the master set for each sub set
    pick_random_elements(filenames, train_images, int(num_train_elements))
    pick_random_elements(filenames, test_images, int(num_test_elements))
    pick_random_elements(filenames, val_images, int(num_val_elements))

    sets = [train_images, test_images, val_images]

    set_count = 0

    basic_set = [[],[],[]]

    for set in sets:

        for filename in set:

                # Get the name of the image to be saved
                name = ntpath.basename(filename).split(".", 1)[0]

                basic_set[set_count].append(name)

        set_count += 1

    return basic_set

def write_voc_imagesets(basic_set, imgs):

    imagesets = [[],[],[]]

    # Create the imageset files
    train_file = open(dataset_dir+"/ImageSets/Main/train.txt", "w")
    val_file = open(dataset_dir + "/ImageSets/Main/val.txt", "w")
    test_file = open(dataset_dir + "/ImageSets/Main/test.txt", "w")
    trainval_file = open(dataset_dir + "/ImageSets/Main/trainval.txt", "w")

    set_count = 0

    for set in basic_set:

        for name in set:

            for image in imgs:

                if name in image:

                    imagesets[set_count].append(image)

        set_count += 1


    # Write the names to the image set files
    for name in imagesets[0]:

        train_file.write(name+"\n")
        trainval_file.write(name + "\n")

    for name in imagesets[1]:
        test_file.write(name+"\n")

    for name in imagesets[2]:
        val_file.write(name+"\n")
        trainval_file.write(name + "\n")

    train_file.close()
    val_file.close()
    test_file.close()
    trainval_file.close()


#print(get_annotation_names())
#print(get_sets())

imgs = get_annotation_names()
basic_set = get_sets()
write_voc_imagesets(basic_set,imgs)

#get_sets()





