#*************************************************************************************************#
#                                                                                                 #
#   File: sample_analysis.py                                                                      #
#   Author: Ethan Takla                                                                           #
#   Last modified: 4/5/2018                                                                       #
#   Description: This file contains all the tools to localize and predict the species of          #
#                an arbitrary amount of seeds in an image. The large sample image is partitioned  #
#                into many small slices, which are each individually analyzed by the classifier.  #
#                A single-shot multibox detector (SSD) is used along with a VGG-16 base network   #
#                to run perform classification. Slice deltas are 1/3 of the slice width so seeds  #
#                caught on the edges will be guaranteed to appear wholly in at least image.       #
#                Probability-based non-maximal suppression is used to merge any redundant         #
#                detections.                                                                      #
#   Inputs:                                                                                       #
#           -img        Path to the image to be analzyed                                          #
#           -weights    Path to the weights file for the classifier                               #
#   Outputs:                                                                                      #
#           results.png     A .PNG image of all of the image overlaid with the seed detections    #
#           statistics.dat  A text-based file containing the possible species and their           #
#                           composition percentages                                               #
#                                                                                                 #
#*************************************************************************************************#


import os
import sys
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
import torch.utils.data as data
import torchvision.transforms as transforms
from torch.utils.serialization import load_lua
import numpy as np
from data import VOC_CLASSES as labels
import cv2
import matplotlib
matplotlib.use('Agg') # Needed to run without a display
from matplotlib import pyplot as plt
from data import VOCDetection, VOCroot, AnnotationTransform
from ssd import build_ssd
import math
import argparse

# Size of center-based inclusion square. BBox's are included if their centroids fit in this square. This is used
# mainly to eliminate seed detections that touch the edges of the slices
INCLUSION_WINDOW = 0.75

# Amount of overlap required for BBox's to be considered bounding the same object
OVERLAP_THRESHOLD = 0.8

# Create an argument parser for weights and image file
parser = argparse.ArgumentParser(description='Seed sample analzyer')
parser.add_argument('image', metavar='img', type=str, nargs='+',
                   help='path to the sample image')
parser.add_argument('weights', metavar='wts', type=str, nargs='+',
                   help='path to the weights file')

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

# Set up cuda for floating ops
if torch.cuda.is_available():
    torch.set_default_tensor_type('torch.cuda.FloatTensor')

# The possible species that can be detected
species_names = ['prg', 'tf']

# Chop up an sample image into smaller, overlapping windows
def partition_image(image, shape):

    # Step half the shape dimension to avoid losing seeds on the edges
    partitions_x = math.floor(image.shape[1] / shape[0]) * 3
    partitions_y = math.floor(image.shape[0] / shape[1]) * 3

    image_set = []

    for x in range(partitions_x):
        for y in range(partitions_y):
            start_x = int(x * (shape[0] / 3))
            start_y = int(y * (shape[1] / 3))
            end_x = start_x + shape[0]
            end_y = start_y + shape[1]

            image_set.append([image[start_y:end_y, start_x:end_x, :], [start_y, start_x]])

    return image_set

def gen_slice_predictions(image_slice, net):

    predictions = []

    rgb_image = cv2.cvtColor(image_slice, cv2.COLOR_BGR2RGB)

    x = cv2.resize(image_slice, (300, 300)).astype(np.float32)
    x -= (104.0, 117.0, 123.0)
    x = x.astype(np.float32)
    x = x[:, :, ::-1].copy()
    x = torch.from_numpy(x).permute(2, 0, 1)

    # wrap tensor in Variable
    xx = Variable(x.unsqueeze(0))
    if torch.cuda.is_available():
        xx = xx.cuda()

    # Evaluate the net
    y = net(xx)
    top_k=10

    detections = y.data

    # scale each detection back up to the image
    scale = torch.Tensor([rgb_image.shape[1::-1], rgb_image.shape[1::-1]])
    for i in range(detections.size(1)):
        j = 0
        while detections[0,i,j,0] >= 0.75:

            # Get the score of the prediction
            score = detections[0,i,j,0]

            # Get the centroid of the bouding box
            pt = (detections[0,i,j,1:]*scale).cpu().numpy()

            # Get the bounding box coordinates
            coords = [(pt[0], pt[1]), pt[2]-pt[0]+1, pt[3]-pt[1]+1]

            predictions.append([score,i,coords])

            j+=1

    return predictions


def analyze_sample(image, net, slice_shape):

    predictions = []

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image_set = partition_image(rgb_image, slice_shape)

    for im in image_set:

        raw_predictions = gen_slice_predictions(im[0], net)

        for prediction in raw_predictions:

            centroid_x = (prediction[2][0][1] + prediction[2][2])/2
            centroid_y = (prediction[2][0][0] + prediction[2][1])/2

            max_bound = (INCLUSION_WINDOW/2)+0.5
            min_bound = 0.5-(INCLUSION_WINDOW/2)

            if slice_shape[0] * max_bound > centroid_x > slice_shape[0] * min_bound \
                    and slice_shape[1] * max_bound > centroid_y > slice_shape[1] * min_bound:

                shifted_pred = [prediction[0],prediction[1], [(prediction[2][0][1]+im[1][0],
                                                               prediction[2][0][0]+im[1][1]),
                                                              prediction[2][2], prediction[2][1]]]

                predictions.append(shifted_pred)

    return predictions


# Non-maximal supression from Adrian Rosebrock, based on Malisiewicz et al.
def non_max_suppression_fast(boxes, overlapThresh):
    # if there are no boxes, return an empty list
    if len(boxes) == 0:
        return []

    # if the bounding boxes integers, convert them to floats --
    # this is important since we'll be doing a bunch of divisions
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # initialize the list of picked indexes
    pick = []

    # grab the coordinates of the bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # compute the area of the bounding boxes and sort the bounding
    # boxes by the bottom-right y-coordinate of the bounding box
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    # keep looping while some indexes still remain in the indexes
    # list
    while len(idxs) > 0:
        # grab the last index in the indexes list and add the
        # index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # find the largest (x, y) coordinates for the start of
        # the bounding box and the smallest (x, y) coordinates
        # for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # delete all indexes from the index list that have
        idxs = np.delete(idxs, np.concatenate(([last],
                                               np.where(overlap > overlapThresh)[0])))

    # return only the bounding boxes that were picked using the
    # integer data type
    return boxes[pick].astype("int")

def save_predicitons(image, predictions):

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(10, 10))
    colors = plt.cm.hsv(np.linspace(0, 1, 3)).tolist()
    plt.imshow(rgb_image)  # plot the image for matplotlib
    currentAxis = plt.gca()

    species = {}

    for specie in species_names:
        species[specie] = 0

    for prediction in predictions:

        j = 0

        # Get the score for the class
        score = prediction[0]
        id = prediction[1]
        coords = (prediction[2][0][1],prediction[2][0][0]),prediction[2][2],prediction[2][1]

        # Add to specie counter
        species[str(species_names[id-1])] += 1

        # Get the label for the class
        color = colors[id]

        currentAxis.add_patch(plt.Rectangle(*coords, fill=False, edgecolor=color, linewidth=2))
        #currentAxis.text(coords[0][0], coords[0][1], display_txt, bbox={'facecolor': color, 'alpha': 0.5})
        j += 1

    # Save the image
    plt.savefig('result.png')

    total_seeds = 0

    # Determine statistics
    for specie in species:
        total_seeds += species[specie]

    compositions = []

    for specie in species:
        compositions.append(species[specie]/total_seeds)

    file = open("statistics.dat", "w")

    id = 0

    for specie in compositions:
        file.write(str(species_names[id])+":"+str(compositions[id])+"\n")
        id += 1

    file.close()

def run_analysis(img, directory, weights='ssd300_0712_4000.pth'):
    # Load the weights
    net = build_ssd('test', 300, 3)    # initialize SSD
    net.load_weights(weights)

    # Load the image
    sample = cv2.imread(directory + '/' + img, cv2.IMREAD_COLOR)

    # Generate predictions
    predictions = analyze_sample(sample, net, [300, 300])


    rgb_image = cv2.cvtColor(sample, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(10, 10))
    colors = plt.cm.hsv(np.linspace(0, 1, 3)).tolist()
    plt.imshow(rgb_image)  # plot the image for matplotlib
    currentAxis = plt.gca()

    species = {}

    for specie in species_names:
        species[specie] = 0

    for prediction in predictions:

        j = 0

        # Get the score for the class
        score = prediction[0]
        id = prediction[1]
        coords = (prediction[2][0][1],prediction[2][0][0]),prediction[2][2],prediction[2][1]

        # Add to specie counter
        species[str(species_names[id-1])] += 1

        # Get the label for the class
        color = colors[id]

        currentAxis.add_patch(plt.Rectangle(*coords, fill=False, edgecolor=color, linewidth=2))
        #currentAxis.text(coords[0][0], coords[0][1], display_txt, bbox={'facecolor': color, 'alpha': 0.5})
        j += 1

    # Save the image
    plt.savefig(directory + '/result.png')

    total_seeds = 0

    # Determine statistics
    for specie in species:
        total_seeds += species[specie]

    compositions = []

    for specie in species:
        compositions.append(species[specie]/total_seeds)

    id = 0

    results = ''
    for specie in compositions:
        results += (str(species_names[id])+":"+str(compositions[id])+"\n")
        id += 1

    return results

if __name__ == '__main__':

    # Get the arguements
    args = parser.parse_args()

    # Load the image
    sample = cv2.imread(args.image[0], cv2.IMREAD_COLOR)

    # Load the weights
    net = build_ssd('test', 300, 3)    # initialize SSD
    net.load_weights(args.weights[0])

    # Generate the predictions
    predicitions = analyze_sample(sample, net, [300,300])

    # Save the predictions
    save_predicitons(sample, predicitions)
