#!/usr/bin/env python3

import os
#os.environ["DEPTHAI_LEVEL"] = "debug"

import cv2
import argparse
import depthai as dai
import time
import collections

parser = argparse.ArgumentParser()
parser.add_argument('-mres', '--mono-resolution', type=int, default=800, choices={400, 720, 800},
                    help="Select mono camera resolution (height). Default: %(default)s")
parser.add_argument('-cres', '--color-resolution', default='800', choices={'720', '800', '1080', '4k', '12mp'},
                    help="Select color camera resolution / height. Default: %(default)s")
parser.add_argument('-rot', '--rotate', const='all', choices={'all', 'rgb', 'mono'}, nargs="?",
                    help="Which cameras to rotate 180 degrees. All if not filtered")
args = parser.parse_args()

# TODO as args
cam_list = ['left', 'right']

print("DepthAI version:", dai.__version__)
print("DepthAI path:", dai.__file__)

cam_socket_opts = {
    'rgb'  : dai.CameraBoardSocket.RGB,
    'left' : dai.CameraBoardSocket.LEFT,
    'right': dai.CameraBoardSocket.RIGHT,
}

rotate = {
    'rgb'  : args.rotate in ['all', 'rgb'],
    'left' : args.rotate in ['all', 'mono'],
    'right': args.rotate in ['all', 'mono'],
}

mono_res_opts = {
    400: dai.MonoCameraProperties.SensorResolution.THE_400_P,
    720: dai.MonoCameraProperties.SensorResolution.THE_720_P,
    800: dai.MonoCameraProperties.SensorResolution.THE_800_P,
}

color_res_opts = {
    '720':  dai.ColorCameraProperties.SensorResolution.THE_720_P,
    '800':  dai.ColorCameraProperties.SensorResolution.THE_800_P,
    '1080': dai.ColorCameraProperties.SensorResolution.THE_1080_P,
    '4k':   dai.ColorCameraProperties.SensorResolution.THE_4_K,
    '12mp': dai.ColorCameraProperties.SensorResolution.THE_12_MP,
}

# Start defining a pipeline
pipeline = dai.Pipeline()

cam = {}
xout = {}
for c in cam_list:
    xout[c] = pipeline.createXLinkOut()
    xout[c].setStreamName(c)
    xout[c].input.setBlocking(True)
    xout[c].input.setQueueSize(1)
    if 1:  # c == 'rgb':
        cam[c] = pipeline.createColorCamera()
        cam[c].setResolution(color_res_opts[args.color_resolution])
    else:
        cam[c] = pipeline.createMonoCamera()
        cam[c].setResolution(mono_res_opts[args.mono_resolution])
        cam[c].out.link(xout[c].input)
    cam[c].setBoardSocket(cam_socket_opts[c])
    if rotate[c]:
        cam[c].setImageOrientation(dai.CameraImageOrientation.ROTATE_180_DEG)
    # The sync mechanism inside StereoDepth has a hardcoded tolerance of 16.67ms
    # (1/2 of 30 fps). Setting FPS slightly less than 60 for that to work well...
    cam[c].setFps(55)

if 1: # stereo sync
    stereo = pipeline.createStereoDepth()
    stereo.setInputResolution(640, 400) # For less computations. 1280x800 actually
    cam['left'].isp.link(stereo.left)
    cam['right'].isp.link(stereo.right)
    stereo.syncedLeft.link(xout['left'].input)
    stereo.syncedRight.link(xout['right'].input)
    stereo.left.setBlocking(False)
    stereo.left.setQueueSize(1)
    stereo.right.setBlocking(False)
    stereo.right.setQueueSize(1)
else:
    cam['left'].isp.link(xout['left'].input)
    cam['right'].isp.link(xout['right'].input)

if 0:
    print("=== Using custom camera tuning, and limiting RGB FPS to 10")
    pipeline.setCameraTuningBlobPath("/home/user/Downloads/tuning_color_low_light.bin")
    # TODO: change sensor driver to make FPS automatic (based on requested exposure time)
    cam['rgb'].setFps(10)

# Calculates FPS over a moving window, configurable
class FPS:
    def __init__(self, window_size=30):
        self.dq = collections.deque(maxlen=window_size)
        self.fps = 0

    def add(self, timestamp=None):
        if timestamp == None: timestamp = time.monotonic()
        count = len(self.dq)
        if count > 0: self.fps = count / (timestamp - self.dq[0])
        self.dq.append(timestamp)

    def get(self):
        return self.fps

# Pipeline is defined, now we can connect to the device
with dai.Device(pipeline) as device:
    q = {}
    for c in cam_list:
        q[c] = device.getOutputQueue(name=c, maxSize=1, blocking=True)

    prev_seq = -1
    fps = FPS()
    while True:
        tstamp = {}
        seq = {}
        for c in cam_list:
            pkt = q[c].get()
            tstamp[c] = pkt.getTimestamp().total_seconds()
            seq[c] = pkt.getSequenceNum()
            if 0:
                frame = pkt.getCvFrame()
                cv2.imshow(c, frame)
        fps.add()
        latency = (time.monotonic() - tstamp['left']) * 1000
        r_l_diff = (tstamp['right'] - tstamp['left']) * 1000
        seq_diff = seq['left'] - prev_seq
        prev_seq = seq['left']

        print(f'fps: {fps.get():5.2f} ', end='')
        print(f'latency left: {latency:7.3f} ms. ', end='')
        print(f'right-left time diff: {r_l_diff:7.3f} ms. ', end='')
        if seq_diff != 1: print(f'left lost frames: {seq_diff - 1}', end='')
        print()

        if cv2.waitKey(1) == ord('q'):
            break
