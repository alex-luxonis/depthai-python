#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai

if 0: rgb_scale = (1920, 1920)  # 1920x1200 -> 1920x1200
else: rgb_scale = (1280, 1920)  # 1920x1200 -> 1280x800

if 0: stereo_scale = (1280, 1920)  # 1920x1200 -> 1280x800
else: stereo_scale = ( 640, 1920)  # 1920x1200 ->  640x400

fps = 30

# Create pipeline
pipeline = dai.Pipeline()
queueNames = []

# Define sources and outputs
camRgb = pipeline.create(dai.node.ColorCamera)
left = pipeline.create(dai.node.ColorCamera)
right = pipeline.create(dai.node.ColorCamera)
stereo = pipeline.create(dai.node.StereoDepth)

rgbOut = pipeline.create(dai.node.XLinkOut)
depthOut = pipeline.create(dai.node.XLinkOut)

rgbOut.setStreamName("rgb")
queueNames.append("rgb")
depthOut.setStreamName("depth")
queueNames.append("depth")

#Properties
camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1200_P)
camRgb.setFps(fps)
camRgb.setIspScale(rgb_scale)

# For now, RGB needs fixed focus to properly align with depth.
# This value was used during calibration
# camRgb.initialControl.setManualFocus(130)

left.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1200_P)
left.setBoardSocket(dai.CameraBoardSocket.LEFT)
left.setFps(fps)
left.setIspScale(stereo_scale)
right.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1200_P)
right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
right.setFps(fps)
right.setIspScale(stereo_scale)

stereo.initialConfig.setConfidenceThreshold(245)
# LR-check is required for depth alignment
stereo.setLeftRightCheck(True)
stereo.setDepthAlign(dai.CameraBoardSocket.RGB)
# Setting input resolution as temp workaround with color cams
stereo.setInputResolution(left.getIspSize())

# Linking
camRgb.isp.link(rgbOut.input)
left.isp.link(stereo.left)
right.isp.link(stereo.right)
stereo.disparity.link(depthOut.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    device.getOutputQueue(name="rgb",   maxSize=4, blocking=False)
    device.getOutputQueue(name="depth", maxSize=4, blocking=False)

    frameRgb = None
    frameDepth = None

    jet_custom = cv2.applyColorMap(np.arange(256, dtype=np.uint8), cv2.COLORMAP_JET)
    jet_custom[0] = [0, 0, 0]

    while True:
        latestPacket = {}
        latestPacket["rgb"] = None
        latestPacket["depth"] = None

        queueEvents = device.getQueueEvents(("rgb", "depth"))
        for queueName in queueEvents:
            packets = device.getOutputQueue(queueName).tryGetAll()
            if len(packets) > 0:
                latestPacket[queueName] = packets[-1]

        if latestPacket["rgb"] is not None:
            frameRgb = latestPacket["rgb"].getCvFrame()
            cv2.imshow("rgb", frameRgb)

        if latestPacket["depth"] is not None:
            frameDepth = latestPacket["depth"].getFrame()
            maxDisparity = stereo.initialConfig.getMaxDisparity()
            # Optional, extend range 0..95 -> 0..255, for a better visualisation
            if 1: frameDepth = (frameDepth * 255. / maxDisparity).astype(np.uint8)
            # Optional, apply false colorization
            if 1: frameDepth = cv2.applyColorMap(frameDepth, jet_custom)
            frameDepth = np.ascontiguousarray(frameDepth)
            cv2.imshow("depth", frameDepth)

        # Blend when both received
        if frameRgb is not None and frameDepth is not None:
            # Need to have both frames in BGR format before blending
            if len(frameDepth.shape) < 3:
                frameDepth = cv2.cvtColor(frameDepth, cv2.COLOR_GRAY2BGR)
            # TODO add a slider to adjust blending ratio
            blended = cv2.addWeighted(frameRgb, 0.6, frameDepth, 0.4 ,0)
            cv2.imshow("rgb-depth", blended)
            frameRgb = None
            frameDepth = None

        if cv2.waitKey(1) == ord('q'):
            break
