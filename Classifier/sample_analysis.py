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


parser = argparse.ArgumentParser(description='Seed sample analzyer')
parser.add_argument('image', metavar='img', type=str, nargs='+',
                   help='path to the sample image')
parser.add_argument('weights', metavar='wts', type=str, nargs='+',
                   help='path to the weights file')

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

if torch.cuda.is_available():
    torch.set_default_tensor_type('torch.cuda.FloatTensor')

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

            window_size = 0.75
            max_bound = (window_size/2)+0.5
            min_bound = 0.5-(window_size/2)

            if slice_shape[0] * max_bound > centroid_x > slice_shape[0] * min_bound \
                    and slice_shape[1] * max_bound > centroid_y > slice_shape[1] * min_bound:

                shifted_pred = [prediction[0],prediction[1], [(prediction[2][0][1]+im[1][0],
                                                               prediction[2][0][0]+im[1][1]),
                                                              prediction[2][2], prediction[2][1]]]

                predictions.append(shifted_pred)

    return predictions


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
