#!/usr/bin/env python3

import depthai as dai
from contextlib import ExitStack

# Create pipeline
pipeline = dai.Pipeline()

# Comment out to disable any cameras
cam_list = [
    'rgb',
    'left',
    'right',
    'camd',
]

cam_socket_opts = {
    'rgb'  : dai.CameraBoardSocket.RGB,   # Or CAM_A
    'left' : dai.CameraBoardSocket.LEFT,  # Or CAM_B
    'right': dai.CameraBoardSocket.RIGHT, # Or CAM_C
    'camd' : dai.CameraBoardSocket.CAM_D,
}

# Define sources and outputs
camRgb, ve, veOut = {}, {}, {}

for c in cam_list:
    camRgb[c] = pipeline.createColorCamera()
    ve[c] = pipeline.createVideoEncoder()
    veOut[c] = pipeline.createXLinkOut()

    # Properties
    camRgb[c].setBoardSocket(cam_socket_opts[c])
    if 0: # 4K -> 1080p. Note at most 2 cams could be processed at this rate
        camRgb[c].setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
        camRgb[c].setIspScale(1, 2)
    ve[c].setDefaultProfilePreset(1920, 1080, 30, dai.VideoEncoderProperties.Profile.H264_MAIN)
    veOut[c].setStreamName(c)

    # Linking
    camRgb[c].video.link(ve[c].input)
    ve[c].bitstream.link(veOut[c].input)

# Connect to device and start pipeline
with dai.Device(pipeline) as dev:

    # Output queues will be used to get the encoded data from the output defined above
    outQ, fname, file = {}, {}, {}
    for c in cam_list:
        outQ[c] = dev.getOutputQueue(c, maxSize=30, blocking=True)
        fname[c] = c + '.h264'

    # Processing loop
    with ExitStack() as stack:
        for c in cam_list:
            file[c] = stack.enter_context(open(fname[c], 'wb'))
            print("Opened for writing:", fname[c])
        print("Press Ctrl+C to stop encoding...")
        while True:
            try:
                # Empty each queue
                for c in cam_list:
                    while outQ[c].has(): outQ[c].get().getData().tofile(file[c])
            except KeyboardInterrupt:
                break
