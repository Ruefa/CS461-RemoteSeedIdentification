# ************************************************************************************************#
#                                                                                                 #
#   File: sample_analysis.py                                                                      #
#   Author: Ethan Takla                                                                           #
#   Last modified: 5/10/2018                                                                       #
#   Description: This file contains all the tools to localize and predict the species of          #
#                an arbitrary amount of seeds in an image. The large sample image is partitioned  #
#                into many small slices, which are each individually analyzed by the classifier.  #
#                A single-shot multibox detector (SSD) is used along with a VGG-16 base network   #
#                to run perform classification. Slice deltas are 1/3 of the slice width so seeds  #
#                caught on the edges will be guaranteed to appear wholly in at least one image.   #
#                Probability-based non-maximal suppression is used to merge any redundant         #
#                detections. A novel "Interest Region Processing" method is used to ensure        #
#                processing isn't wasted on empty slices.                                         #
#   Inputs:                                                                                       #
#           -img        Path to the image to be analzyed                                          #
#           -weights    Path to the weights file for the classifier                               #
#   Outputs:                                                                                      #
#           results.png     A .PNG image of all of the image overlaid with the seed detections    #
#           statistics.dat  A text-based file containing the possible species and their           #
#                           composition percentages                                               #
#                                                                                                 #
#                                                                                                 #
# ************************************************************************************************#


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

matplotlib.use('Agg')  # Needed to run without a display
from matplotlib import pyplot as plt
from data import VOCDetection, VOCroot, AnnotationTransform
from ssd import build_ssd
import math
import argparse

# Size of center-based inclusion square. BBox's are included if their centroids fit in this square. This is used
# mainly to eliminate seed detections that touch the edges of the slices
INCLUSION_WINDOW = 0.7

# Amount of overlap required for BBox's to be considered bounding the same object
# For extremely large seeds, a lower threshold is needed
OVERLAP_THRESHOLD = [0.75, 0.65, 0.6, 0.55, 0.6]

# Edge-to-background ratio required to analyze a sample
EDGE_THRESHOLD = 0.003

# Confidence required to consider a detection valid, different for each specie
DETECTION_THRESHOLDS = [0.7, 0.7, 0.9, 0.9, 0.9]

# DPI of the result image
RESULT_DPI = 200

# Slice overlap coefficient
SLICE_OVERLAP = 3

# Colors to use for the bounding boxes
COLORS = ["#000000", "#000000", "#067BC2", "#ECC30B", "#F37748", "#d56062"]

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
species_names = ['prg', 'tf', 'flax', 'wheat', 'rc']


# Chop up an sample image into smaller, overlapping windows
def partition_image(image, shape):
    # Step half the shape dimension to avoid losing seeds on the edges
    partitions_x = math.floor(image.shape[1] / shape[0]) * SLICE_OVERLAP
    partitions_y = math.floor(image.shape[0] / shape[1]) * SLICE_OVERLAP

    image_set = []

    for x in range(partitions_x):
        for y in range(partitions_y):

            start_x = int(x * (shape[0] / SLICE_OVERLAP))
            start_y = int(y * (shape[1] / SLICE_OVERLAP))
            end_x = start_x + shape[0]
            end_y = start_y + shape[1]

            # Extract a slice from the image
            img = image[start_y:end_y, start_x:end_x, :]

            # We only need to look within the inclusion window area for objects
            w_end_x = int(img.shape[1] * INCLUSION_WINDOW)
            w_end_y = int(img.shape[0] * INCLUSION_WINDOW)
            w_start_x = img.shape[1] - w_end_x
            w_start_y = img.shape[0] - w_end_y

            window = img[w_start_y:w_end_y, w_start_x:w_end_x, :]

            # Only analyze images with objects in them
            if detect(window) and np.shape(img) == (300, 300, 3):
                image_set.append([img, [start_y, start_x]])

    return image_set

# ******************************************** detect ********************************************#
#                                                                                                 #
#   Author: Ethan Takla                                                                           #
#   Last modified: 4/10/2018                                                                      #
#   Description: This function determines if any object (s) exist in the image. First, simple     #
#                edge detection is performed using a median blur and adaptive threshold, which    #
#                produces a near-binary image. The histogram of this is computed, which allows    #
#                once to extract the ratio between black (edge) and white (background) pixels.    #
#                If the edge-to-background pixel ratio is above a certain threshold, there is     #
#                most likely an object(s) present                                                 #
#   Inputs:                                                                                       #
#           img             Image to be analyzed                                                  #
#   Returns:                                                                                      #
#           bool            True if objects present, otherwise false                              #
#                                                                                                 #
# ************************************************************************************************#


def detect(img):

    # Blur to make segmenting easier
    img = cv2.medianBlur(img, 11)

    # Convert to greyscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Find edges of seeds by using an adaptive threshold
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,\
            cv2.THRESH_BINARY, 11, 10)

    # Find the histogram of the threshold image
    hist = cv2.calcHist([thresh], [0], None, [256], [0, 256])

    # Very simple measure of the presence of edges
    edge_factor = np.sum(hist[0:127])
    background_factor = np.sum(hist[128:256])
    f = edge_factor / background_factor

    if f >= EDGE_THRESHOLD:
        return True

    return False


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
    detections = y.data

    # scale each detection back up to the image
    scale = torch.Tensor([rgb_image.shape[1::-1], rgb_image.shape[1::-1]])
    for i in range(detections.size(1)):

        j = 0

        while detections[0, i, j, 0] >= DETECTION_THRESHOLDS[i-1]:

            # Get the score of the prediction
            score = detections[0, i, j, 0]

            # Get the centroid of the bounding box
            pt = (detections[0, i, j, 1:] * scale).cpu().numpy()

            # Get the bounding box coordinates
            coords = [(pt[0], pt[1]), pt[2] - pt[0] + 1, pt[3] - pt[1] + 1]

            predictions.append([score, i, coords])

            j += 1

    return predictions


def analyze_sample(image, net, slice_shape):

    predictions = []

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image_set = partition_image(rgb_image, slice_shape)

    for im in image_set:

        raw_predictions = gen_slice_predictions(im[0], net)

        for prediction in raw_predictions:

            centroid_x = (prediction[2][0][1] + prediction[2][2]) / 2
            centroid_y = (prediction[2][0][0] + prediction[2][1]) / 2

            max_bound = (INCLUSION_WINDOW / 2) + 0.5
            min_bound = 0.5 - (INCLUSION_WINDOW / 2)

            if slice_shape[0] * max_bound > centroid_x > slice_shape[0] * min_bound \
                    and slice_shape[1] * max_bound > centroid_y > slice_shape[1] * min_bound:
                shifted_pred = [prediction[0], prediction[1], [(prediction[2][0][1] + im[1][0],
                                                                prediction[2][0][0] + im[1][1]),
                                                               prediction[2][2], prediction[2][1]]]

                predictions.append(shifted_pred)

    # Contains predictions indexed by individual species
    indexed_bboxes = [[] for x in range(0, len(species_names))]
    indexed_scores = [[] for x in range(0, len(species_names))]
    final_bboxes = [[] for x in range(0, len(species_names))]

    # Index predictions by species
    for prediction in predictions:

        score = prediction[0]
        coords = prediction[2][0][1], prediction[2][0][0], prediction[2][0][1] + prediction[2][2],\
                 prediction[2][0][0] + prediction[2][1]

        indexed_bboxes[prediction[1]-1].append(coords)
        indexed_scores[prediction[1]-1].append(score)

    for specie in range(0, len(species_names)):

        if len(indexed_bboxes[specie]) > 0:

                final_bboxes[specie].append(non_max_suppression_fast(np.asarray(indexed_bboxes[specie]),
                                                                     np.asarray(indexed_scores[specie]),
                                                                     OVERLAP_THRESHOLD[specie]))
    return final_bboxes


# Non-maximal supression from Adrian Rosebrock, based on Malisiewicz et al.
def non_max_suppression_fast(boxes, probs, overlapThresh):

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
    # boxes by the prediction confidences
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(probs)

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
    plt.axis('off')
    plt.imshow(rgb_image)  # plot the image for matplotlib
    currentAxis = plt.gca()

    currentAxis.xaxis.set_major_locator(matplotlib.ticker.NullLocator())
    currentAxis.yaxis.set_major_locator(matplotlib.ticker.NullLocator())

    species = {}
    hex_colors = {}
    specie_counter = 0

    for specie in species_names:
        species[specie] = 0

    for specie in predictions:

        name = str(species_names[specie_counter])

        if len(specie) > 0:

            for prediction in specie[0]:

                coords = (prediction[0], prediction[1]), prediction[2]-prediction[0], prediction[3]-prediction[1]

                # Add to specie counter
                species[name] += 1

                # Record the color
                hex_colors[name] = COLORS[specie_counter+1]

                currentAxis.add_patch(plt.Rectangle(*coords, fill=False, edgecolor=COLORS[specie_counter+1], linewidth=1))

        else:

            hex_colors[name] = matplotlib.colors.to_hex("#000000")

        specie_counter += 1

    # Save the image
    plt.savefig('result.png', bbox_inches='tight', pad_inches=0, dpi=RESULT_DPI)

    total_seeds = 0

    # Determine statistics
    for specie in species:
        total_seeds += species[specie]

    compositions = {}

    if total_seeds != 0:
        for specie in species:
            compositions[specie] = species[specie] / total_seeds
    else:
        for specie in species:
            compositions[specie] = 0.0

    file = open("statistics.dat", "w")

    # Save each specie and its corresponding statistics and colors to a file
    for specie in species:
        file.write(specie + ":" + str(round(compositions[specie], 3)) + ","
                   + str(round(total_seeds*compositions[specie])) + "," + str(hex_colors[specie]) + "\n")

    file.close()


def run_analysis(imgPath, resultPath, weights='ssd300_0712_4000.pth'):

    # Load the weights
    net = build_ssd('test', 300, len(species_names)+1)  # initialize SSD
    net.load_weights(weights)

    # Load the image
    sample = cv2.imread(imgPath, cv2.IMREAD_COLOR)

    # Generate predictions
    predictions = analyze_sample(sample, net, [300, 300])

    rgb_image = cv2.cvtColor(sample, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(10, 10))
    plt.axis('off')
    plt.imshow(rgb_image)  # plot the image for matplotlib
    currentAxis = plt.gca()

    currentAxis.xaxis.set_major_locator(matplotlib.ticker.NullLocator())
    currentAxis.yaxis.set_major_locator(matplotlib.ticker.NullLocator())

    species = {}
    hex_colors = {}
    specie_counter = 0

    for specie in species_names:
        species[specie] = 0

    for specie in predictions:

        name = str(species_names[specie_counter])

        if len(specie) > 0:

            for prediction in specie[0]:
                coords = (prediction[0], prediction[1]), prediction[2] - prediction[0], prediction[3] - prediction[1]

                # Add to specie counter
                species[name] += 1

                # Record the color
                hex_colors[name] = COLORS[specie_counter + 1]

                currentAxis.add_patch(plt.Rectangle(*coords, fill=False, edgecolor=COLORS[specie_counter + 1], linewidth=1))

        else:

            hex_colors[name] = matplotlib.colors.to_hex("#000000")

        specie_counter += 1

    # Save the image
    plt.savefig(resultPath, bbox_inches='tight', pad_inches=0, dpi=RESULT_DPI)

    total_seeds = 0

    # Determine statistics
    for specie in species:
        total_seeds += species[specie]

    compositions = {}

    if total_seeds != 0:
        for specie in species:
            compositions[specie] = species[specie] / total_seeds
    else:
        for specie in species:
            compositions[specie] = 0.0

    results = ''

    # Create the results string
    for specie in species:
        results += specie + ":" + str(round(compositions[specie], 3)) + "," \
                    + str(round(total_seeds * compositions[specie])) + "," + str(hex_colors[specie]) + "\n"

    return results


if __name__ == '__main__':

    # Get the arguements
    args = parser.parse_args()

    # Load the image
    sample = cv2.imread(args.image[0], cv2.IMREAD_COLOR)

    # Load the weights
    net = build_ssd('test', 300, len(species_names)+1)  # initialize SSD
    net.load_weights(args.weights[0])

    # Generate the predictions
    predicitions = analyze_sample(sample, net, [300, 300])

    # Save the predictions
    save_predicitons(sample, predicitions)
