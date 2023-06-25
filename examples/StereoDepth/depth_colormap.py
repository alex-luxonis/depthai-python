#!/usr/bin/env python3

import cv2
import depthai as dai
import numpy as np

# Closer-in minimum depth, disparity range is doubled (from 95 to 190):
extended_disparity = False
# Better accuracy for longer distance, fractional disparity 32-levels:
subpixel = False
# Better handling for occlusions:
lr_check = True

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
monoLeft = pipeline.create(dai.node.ColorCamera)
monoRight = pipeline.create(dai.node.ColorCamera)
depth = pipeline.create(dai.node.StereoDepth)
xout = pipeline.create(dai.node.XLinkOut)

xout.setStreamName("disparity")

# Properties
monoLeft.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1200_P)
monoLeft.setCamera("left")
monoLeft.setIspScale(800, 1200)
monoRight.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1200_P)
monoRight.setCamera("right")
monoRight.setIspScale(800, 1200)

# Create a node that will produce the depth map (using disparity output as it's easier to visualize depth this way)
depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
# Options: MEDIAN_OFF, KERNEL_3x3, KERNEL_5x5, KERNEL_7x7 (default)
depth.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
depth.setLeftRightCheck(lr_check)
depth.setExtendedDisparity(extended_disparity)
depth.setSubpixel(subpixel)

# Create a colormap
colormap = pipeline.create(dai.node.ImageManip)
colormap.initialConfig.setColormap(dai.Colormap.STEREO_TURBO, depth.initialConfig.getMaxDisparity())
colormap.initialConfig.setFrameType(dai.ImgFrame.Type.NV12)
colormap.setMaxOutputFrameSize(1280*800*3//2)

# Linking
monoLeft.isp.link(depth.left)
monoRight.isp.link(depth.right)
depth.disparity.link(colormap.inputImage)
colormap.out.link(xout.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Output queue will be used to get the disparity frames from the outputs defined above
    q = device.getOutputQueue(name="disparity", maxSize=4, blocking=False)

    while True:
        inDisparity = q.get()  # blocking call, will wait until a new data has arrived
        frame = inDisparity.getCvFrame()
        cv2.imshow("disparity", frame)

        if cv2.waitKey(1) == ord('q'):
            break
