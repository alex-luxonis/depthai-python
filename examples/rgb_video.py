#!/usr/bin/env python3

import cv2
import depthai as dai
import time
import collections

# Create pipeline
pipeline = dai.Pipeline()

# Define source and output
camRgb = pipeline.createColorCamera()
xoutVideo = pipeline.createXLinkOut()

xoutVideo.setStreamName("video")

# Properties
camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camRgb.setVideoSize(1920, 1080)

# Disabling this would lead to latency build up with USB2
if 1:
    xoutVideo.input.setBlocking(False)
    xoutVideo.input.setQueueSize(1)

# Linking
camRgb.video.link(xoutVideo.input)


# Calculates FPS over a moving window, configurable
class FPS:
    def __init__(self, window_size=10):
        self.dq = collections.deque(maxlen=window_size)
        self.fps = 0

    def add(self, timestamp=None):
        if timestamp == None: timestamp = time.monotonic()
        count = len(self.dq)
        if count > 0: self.fps = count / (timestamp - self.dq[0])
        self.dq.append(timestamp)

    def get(self):
        return self.fps


# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    video = device.getOutputQueue(name="video", maxSize=1, blocking=False)

    seq_prev = -1
    fps = FPS()
    while True:
        # For testing, read packets with a delay
        if 0: time.sleep(0.5)

        videoIn = video.get()

        fps.add()
        seqnum = videoIn.getSequenceNum()
        tstamp = videoIn.getTimestamp().total_seconds()
        latency = (time.monotonic() - tstamp) * 1000
        seq_diff = seqnum - seq_prev
        seq_prev = seqnum
        print(f"Host FPS: {fps.get():5.2f}. ", end="")
        print(f"Camera seqnum: {seqnum}, latency: {latency:7.3f} ms", end="")
        if seq_diff != 1: print(f". Lost {seq_diff - 1} frames", end="")
        print()

        # Get BGR frame from NV12 encoded video frame to show with opencv
        # Visualizing the frame on slower hosts might have overhead
        cv2.imshow("video", videoIn.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break
