#!/usr/bin/env python3

import cv2
import depthai as dai
import numpy as np

# Create pipeline
pipeline = dai.Pipeline()

# Define source and output
camRgb = pipeline.create(dai.node.ColorCamera)
script = pipeline.create(dai.node.Script)
xinCtrl = pipeline.create(dai.node.XLinkIn)
xoutRgb = pipeline.create(dai.node.XLinkOut)

xinCtrl.setStreamName('control')
xoutRgb.setStreamName("rgb")

# Properties
camRgb.setPreviewSize(300, 300)
camRgb.setInterleaved(False)
camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)

script.setScript("""
toSend = 0

while True:
    frame = node.io['inFrame'].get()
    ctrl = node.io['inControl'].tryGet()

    if ctrl is not None:
        numFrames = ctrl.getData()[0]
        toSend += numFrames

    if toSend > 0:
        node.io['outFrame'].send(frame)
        toSend -= 1
""")

# Linking
camRgb.preview.link(script.inputs['inFrame'])
xinCtrl.out.link(script.inputs['inControl'])
script.outputs['outFrame'].link(xoutRgb.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    print('Connected cameras: ', device.getConnectedCameras())
    # Print out usb speed
    print('Usb speed: ', device.getUsbSpeed().name)

    # Output queue will be used to get the rgb frames from the output defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    controlQueue = device.getInputQueue('control')

    img = np.zeros((300, 300, 3), np.uint8)
    cv2.putText(img, "Press to capture:", (5,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1)
    cv2.putText(img, " 1 for one frame" , (5,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1)
    cv2.putText(img, " 2 for 30 frames" , (5,180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1)
    cv2.imshow('rgb', img)

    while True:
        inRgb = qRgb.tryGet()
        if inRgb is not None:
            # Retrieve 'bgr' (opencv format) frame
            cv2.imshow("rgb", inRgb.getCvFrame())

        key = cv2.waitKey(10)
        if key == ord('q'):
            break
        elif key in [ord('1'), ord('2')]:
            num = 1 if key == ord('1') else 30
            data = dai.Buffer()
            data.setData(num)
            controlQueue.send(data)
