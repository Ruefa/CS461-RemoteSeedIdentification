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
from matplotlib import pyplot as plt
from data import VOCDetection, VOCroot, AnnotationTransform
from ssd import build_ssd
import math

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

if torch.cuda.is_available():
    torch.set_default_tensor_type('torch.cuda.FloatTensor')

net = build_ssd('test', 300, 3)    # initialize SSD
net.load_weights('weights/ssd300_0712_10000.pth')

image = cv2.imread('./data/IMG_1248.jpg', cv2.IMREAD_COLOR)  # uncomment if dataset not downloaded

# Chop up an sample image into smaller, overlapping windows
def partition_image(im, shape):

    partitions_x = math.floor(im.shape[0]/shape[0]) * 2
    partitions_y = math.floor(im.shape[1]/shape[1]) * 2

    image_set = []

    for x in range(partitions_x):
        for y in range(partitions_y):

            start_x = int(x * shape[0] / 2)
            start_y = int(y * shape[1] / 2)
            end_x = start_x + shape[0]
            end_y = start_y + shape[1]

            image_set.append([im[start_x:end_x, start_y:end_y,:],[start_x,start_y]])

    for im2 in image_set:

        im2 = im2[0]
        # image = cv2.imread("/home/ethan/Documents/deeplearning/ssd/pytorch/ssd.pytorch/test_images/IMG_1247.jpg")
        rgb_image = cv2.cvtColor(im2, cv2.COLOR_BGR2RGB)
        # View the sampled input image before transform
        # plt.figure(figsize=(10,10))
        # plt.imshow(rgb_image)
        # plt.show()

        x = cv2.resize(im2, (300, 300)).astype(np.float32)
        x -= (104.0, 117.0, 123.0)
        x = x.astype(np.float32)
        x = x[:, :, ::-1].copy()
        # plt.imshow(x)
        x = torch.from_numpy(x).permute(2, 0, 1)

        xx = Variable(x.unsqueeze(0))  # wrap tensor in Variable
        if torch.cuda.is_available():
            xx = xx.cuda()
        y = net(xx)
        top_k = 10

        plt.figure(figsize=(10, 10))
        colors = plt.cm.hsv(np.linspace(0, 1, 3)).tolist()
        plt.imshow(rgb_image)  # plot the image for matplotlib
        currentAxis = plt.gca()

        detections = y.data

        print(detections)
        # scale each detection back up to the image
        scale = torch.Tensor([rgb_image.shape[1::-1], rgb_image.shape[1::-1]])
        for i in range(detections.size(1)):
            j = 0
            while detections[0, i, j, 0] >= 0.6:
                score = detections[0, i, j, 0]
                label_name = labels[i - 1]
                display_txt = '%s: %.2f' % (label_name, score)
                pt = (detections[0, i, j, 1:] * scale).cpu().numpy()
                coords = (pt[0], pt[1]), pt[2] - pt[0] + 1, pt[3] - pt[1] + 1
                color = colors[i]
                currentAxis.add_patch(plt.Rectangle(*coords, fill=False, edgecolor=color, linewidth=2))
                currentAxis.text(pt[0], pt[1], display_txt, bbox={'facecolor': color, 'alpha': 0.5})
                j += 1

        plt.show()

    return image_set

def gen_slice_predictions(image_slice):

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
        while detections[0,i,j,0] >= 0.6:

            # Get the score of the prediction
            score = detections[0,i,j,0]

            # Get the centroid of the bouding box
            pt = (detections[0,i,j,1:]*scale).cpu().numpy()

            # Get the bounding box coordinates
            coords = [(pt[0], pt[1]), pt[2]-pt[0]+1, pt[3]-pt[1]+1]

            predictions.append([score,i,coords])

            j+=1

    return predictions


def analyze_sample(image, slice_shape):

    predictions = []

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image_set = partition_image(rgb_image,slice_shape)

    for im in image_set:

        raw_predictions = gen_slice_predictions(im[0])

        for prediction in raw_predictions:

            centroid_x = (prediction[2][0][0] + prediction[2][1])/2
            centroid_y = (prediction[2][0][1] + prediction[2][2])/2

            if slice_shape[0] * 0.75 > centroid_x > slice_shape[0] * 0.25 and slice_shape[1] * 0.75 > centroid_y > slice_shape[1] * 0.25:

                shifted_pred = [prediction[0],prediction[1], [(prediction[2][0][0]+im[1][0], prediction[2][0][1]+im[1][1]), prediction[2][1], prediction[2][2]]]

                predictions.append(shifted_pred)

    return predictions

def show_predicitons(image, predictions):

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(10, 10))
    colors = plt.cm.hsv(np.linspace(0, 1, 3)).tolist()
    plt.imshow(rgb_image)  # plot the image for matplotlib
    currentAxis = plt.gca()

    for prediction in predictions:

        j = 0

        # Get the score for the class
        score = prediction[0]
        id = prediction[1]
        coords = (prediction[2][0][0],prediction[2][0][1]),prediction[2][1],prediction[2][2]

        # Get the label for the class
        label_name = labels[id-1]
        display_txt = '%s: %.2f' % (label_name, score)
        color = colors[id]

        currentAxis.add_patch(plt.Rectangle(*coords, fill=False, edgecolor=color, linewidth=2))
        currentAxis.text(coords[0][0], coords[0][1], display_txt, bbox={'facecolor': color, 'alpha': 0.5})
        j += 1

    plt.show()


predicitions = analyze_sample(image, [512,512])

#show_predicitons(image, predicitions)







