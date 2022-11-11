#!/usr/bin/env python3

import cv2
import depthai as dai

# Create pipeline
pipeline = dai.Pipeline()

# Define source and output
camRgb = pipeline.create(dai.node.ColorCamera)
xoutRgb = pipeline.create(dai.node.XLinkOut)

xoutRgb.setStreamName("rgb")

# Properties
camRgb.setPreviewSize(300, 300)
camRgb.setInterleaved(False)
camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)

script = pipeline.create(dai.node.Script)
script.setScript("""
    while True:
        f = node.io['in'].get()

        w, h, d = f.getWidth(), f.getHeight(), f.getData()
        node.warn(f'{w}x{h}, size {len(d)}')

        if 0: # invert the color of first pixel
            for i in range(3): # 3 planes
                d[w*h*i] = 255 - d[w*h*i]
        else: # invert full image in-place
            for i in range(len(d)):
                d[i] = 255 - d[i]

        node.io['out'].send(f)
""")

# Linking
camRgb.preview.link(script.inputs['in'])
script.outputs['out'].link(xoutRgb.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    print('Connected cameras: ', device.getConnectedCameras())
    # Print out usb speed
    print('Usb speed: ', device.getUsbSpeed().name)
    # Bootloader version
    if device.getBootloaderVersion() is not None:
        print('Bootloader version: ', device.getBootloaderVersion())

    # Output queue will be used to get the rgb frames from the output defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

    while True:
        inRgb = qRgb.get()  # blocking call, will wait until a new data has arrived

        # Retrieve 'bgr' (opencv format) frame
        cv2.imshow("rgb", inRgb.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break
