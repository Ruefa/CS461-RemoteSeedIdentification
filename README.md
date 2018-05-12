# CS461 - Remote Seed Analytics

The Remote Seed Analytics project brings deep learning to the grass seed industry using an NVIDIA Jetson TX2 and an Android phone. Once the Android application is downloaded, clients can take pictures of seed samples using their smartphone camera (12 megapixels) and a 3D-printed 4" x 3" tray. A remote Jetson processor uses state-of-the-art deep learning methods to analyze the sample and send back a report. Once analysis is completed, clients can view metrics such as species composition and seed count of their sample and save the results to a remote database for later retrieval. 

Also included in this repository is a custom seed annotation tool, which was used to build a database of over 15,000 seeds to train the neural network. 

## Features

This project can be split up into three main categories: the Android application, the classifier, and the web server/database. All three components have been designed to seamlessly work together to provide a intuitive, secure, and accurate seed analytics tool.

### Android Application

* Login screen with account creation and forgot password capabilities
* Take live photos of samples and send for analysis
* View account-specific analysis reports
* Save reports as a PDF
* Reports include an image of the processed sample, and a pie chart graphically showing the species composition

### Classifier

* A VGG-16 base network is used in the Single-Shot Detector (SSD) to analyze the sample in small slices
* A novel Interest Region Processing (IRP) method ensures processing time is proportional to the # of seeds in the sample
* 99.6% precision and 98.1% recall was achieved on a test set of 2,500 seeds
* Custom auto-annotation tool used to build large datasets. A dataset of over 15,000 seeds was created using this. 
* Can detect four species of seeds: Red clover, flax, wheat, and tall fescue grass
* Can analyze thousands of seeds at one time

### NVIDIA Jetson TX2 Server/Database

* TCP Socket Server
* Custom message protocol
* Encrypted connection using SSL/TLS
* Support for many concurrent connections
* Individual user accounts
* Cookie-like persistent login feature
* Email based forgot password support
* Local database
* Industry standard password protection (Password hashing)

## Authors

* **Alexander Ruef** 
* **Ethan Takla** 
* **Quanah Green** 

## License

Copyright (c) 2018

## Acknowledgments

* Special thanks to Max deGroot and Ellis Brown for developing an [awesome python implementation](https://github.com/amdegroot/ssd.pytorch/blob/master/README.md) of the Single Shot Detector 
