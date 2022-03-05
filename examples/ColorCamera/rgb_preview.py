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

# Linking
camRgb.preview.link(xoutRgb.input)

# updateInterval: in seconds
# name: if provided, will be verbose, printing FPS when it updates
class FPS:
    def __init__(self, updateInterval=1, name=None):
        self.fps = 0
        self.count = 0
        self.timePrev = None
        self.interval = updateInterval
        self.name = name

    # timestamp: optional to not use current time (but e.g. device timestamp)
    def update(self, timestamp=None):
        import time
        if timestamp is None: timestamp = time.monotonic()
        # When called first, just store the timestamp and return
        if self.timePrev is None:
            self.timePrev = timestamp
            return
        self.count += 1
        tdiff = timestamp - self.timePrev
        if tdiff >= self.interval:
            self.fps = self.count / tdiff
            if self.name:
                print(f'FPS {self.name}: {self.fps:.2f}')
            self.count = 0
            self.timePrev = timestamp

    def get(self):
        return self.fps

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    print('Connected cameras: ', device.getConnectedCameras())
    # Print out usb speed
    print('Usb speed: ', device.getUsbSpeed().name)

    # Output queue will be used to get the rgb frames from the output defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

    fpsHost   = FPS(name='host  ')
    fpsDevice = FPS(name='device')
    while True:
        inRgb = qRgb.get()  # blocking call, will wait until a new data has arrived
        fpsHost.update()
        fpsDevice.update(inRgb.getTimestamp().total_seconds())

        # Retrieve 'bgr' (opencv format) frame
        cv2.imshow("rgb", inRgb.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break
