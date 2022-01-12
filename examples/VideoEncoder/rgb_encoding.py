#!/usr/bin/env python3

import depthai as dai
import time

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and output
camRgb = pipeline.create(dai.node.ColorCamera)
videoEnc = pipeline.create(dai.node.VideoEncoder)
xout = pipeline.create(dai.node.XLinkOut)

xout.setStreamName('h265')

# Properties
camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
videoEnc.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H265_MAIN)

# Linking
camRgb.video.link(videoEnc.input)
videoEnc.bitstream.link(xout.input)

# Calculates FPS over a moving window, configurable
class FPS:
    def __init__(self, window_size=30):
        import collections
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

    # Output queue will be used to get the encoded data from the output defined above
    q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)

    seq_prev = -1
    fps = FPS()
    
    # The .h265 file is a raw stream file (not playable yet)
    with open('video.h265', 'wb') as videoFile:
        print("Press Ctrl+C to stop encoding...")
        try:
            while True:
                h265Packet = q.get()  # Blocking call, will wait until a new data has arrived
                h265Packet.getData().tofile(videoFile)  # Appends the packet data to the opened file
                
                fps.add()
                seqnum = h265Packet.getSequenceNum()
                tstamp = h265Packet.getTimestamp().total_seconds()
                latency = (time.monotonic() - tstamp) * 1000
                seq_diff = seqnum - seq_prev
                seq_prev = seqnum
                print(f"Host FPS: {fps.get():5.2f}. ", end="")
                print(f"Camera seqnum: {seqnum}, latency: {latency:7.3f} ms", end="")
                if seq_diff != 1: print(f". Lost {seq_diff - 1} frames", end="")
                print()
                
        except KeyboardInterrupt:
            # Keyboard interrupt (Ctrl + C) detected
            pass

    print("To view the encoded data, convert the stream file (.h265) into a video file (.mp4) using a command below:")
    print("ffmpeg -framerate 30 -i video.h265 -c copy video.mp4")
