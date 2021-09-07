#!/usr/bin/env python3

''' Run as:
python3 examples/rgb_encoding.py | ffplay -framerate 60 -fflags nobuffer -flags low_delay -framedrop -strict experimental -

'''

import depthai as dai
import sys

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and output
camRgb = pipeline.createColorCamera()
# TODO need to test more if 30 FPS can be achieved realtime (without lag) at 4K
camRgb.setFps(28) # 29, 30
videoEnc = pipeline.createVideoEncoder()
xout = pipeline.createXLinkOut()

xout.setStreamName('h265')

# Properties
camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
# H.265 decoding seems to be slower on some hardware, change to H.264 for now. Might be ffplay related
videoEnc.setDefaultProfilePreset(3840, 2160, 30, dai.VideoEncoderProperties.Profile.H264_MAIN)

# Linking
camRgb.video.link(videoEnc.input)
videoEnc.bitstream.link(xout.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Output queue will be used to get the encoded data from the output defined above
    q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)

    # The .h265 file is a raw stream file (not playable yet)
    with open('video.h265', 'wb') as videoFile:
        print("Press Ctrl+C to stop encoding...")
        try:
            while True:
                h265Packet = q.get()  # Blocking call, will wait until a new data has arrived
                data = h265Packet.getData()
                data.tofile(videoFile)  # Appends the packet data to the opened file
                sys.stdout.buffer.write(data) # Write to stdout, note need to pipe into a player
        except KeyboardInterrupt:
            # Keyboard interrupt (Ctrl + C) detected
            pass

    print("To view the encoded data, convert the stream file (.h265) into a video file (.mp4) using a command below:")
    print("ffmpeg -framerate 30 -i video.h265 -c copy video.mp4")
