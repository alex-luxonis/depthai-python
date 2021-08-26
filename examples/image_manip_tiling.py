#!/usr/bin/env python3

import cv2
import depthai as dai

# Create pipeline
pipeline = dai.Pipeline()

camRgb = pipeline.createColorCamera()
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
camRgb.setPreviewSize(3840, 2160)
camRgb.setInterleaved(False)

manip1 = pipeline.createImageManip()
# Crop result: (0.9-0.1, 1.0-0.0) * (3840, 2160) = (3072, 2160) - width too large for ImageManip
manip1.initialConfig.setCropRect(0.1, 0.0, 0.9, 1.0)
if 1: # Downscale to fit ImageManip max 1920 line width constraint
    factor = 1920 / 3072
    # TODO: resize only if `factor < 1`
    manip1.setResize(int(3072 * factor), int(2160 * factor))
manip1.setMaxOutputFrameSize(1920*2160*3) # Note: don't set larger than needed - wastes memory
camRgb.preview.link(manip1.inputImage)

manip2 = pipeline.createImageManip()
if 0: # For NN
    manip2.initialConfig.setResize(300, 300)
else: # For test, to keep the 4K FOV - helping to visualize the crop area
    manip2.initialConfig.setResize(640, 360)
manip2.setMaxOutputFrameSize(640*360*3) # Note: don't set larger than needed - wastes memory
camRgb.preview.link(manip2.inputImage)

xout1 = pipeline.createXLinkOut()
xout1.setStreamName('cropped')
manip1.out.link(xout1.input)

xout2 = pipeline.createXLinkOut()
xout2.setStreamName('resized')
manip2.out.link(xout2.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:
    # Output queue will be used to get the rgb frames from the output defined above
    q1 = device.getOutputQueue(name=xout1.getStreamName(), maxSize=4, blocking=False)
    q2 = device.getOutputQueue(name=xout2.getStreamName(), maxSize=4, blocking=False)

    while True:
        in1 = q1.tryGet()
        if in1 is not None:
            cv2.imshow(q1.getName(), in1.getCvFrame())

        in2 = q2.tryGet()
        if in2 is not None:
            cv2.imshow(q2.getName(), in2.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break
