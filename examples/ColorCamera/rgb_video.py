#!/usr/bin/env python3

import cv2
import depthai as dai
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-tun', '--cameraTuning', type=Path, 
                    help="Path to camera tuning blob to use, overriding the built-in tuning")
parser.add_argument('-opt', '--optimizeNoise', action='store_true', 
                    help="Optimize camera noise levels")
args = parser.parse_args()

# Create pipeline
pipeline = dai.Pipeline()
if args.cameraTuning:
    print('Overriding camera tuning with:', args.cameraTuning)
    pipeline.setCameraTuningBlobPath(args.cameraTuning)

# Define source and output
camRgb = pipeline.create(dai.node.ColorCamera)
xoutVideo = pipeline.create(dai.node.XLinkOut)

xoutVideo.setStreamName("video")

# Properties
camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)

if args.optimizeNoise:
    print('Optimizing camera noise, by tweaking sharpness and denoise controls')
    camRgb.initialControl.setSharpness(0)     # range: 0..4, default: 1
    camRgb.initialControl.setLumaDenoise(0)   # range: 0..4, default: 1
    camRgb.initialControl.setChromaDenoise(4) # range: 0..4, default: 1

# Not needed to set video size, unless cropping.
# Would crash with sensors like OV9782 that have a lower resolution...
#camRgb.setVideoSize(1920, 1080)

xoutVideo.input.setBlocking(False)
xoutVideo.input.setQueueSize(1)

# Linking
camRgb.video.link(xoutVideo.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    video = device.getOutputQueue(name="video", maxSize=1, blocking=False)

    while True:
        videoIn = video.get()

        # Get BGR frame from NV12 encoded video frame to show with opencv
        # Visualizing the frame on slower hosts might have overhead
        cv2.imshow("video", videoIn.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break
