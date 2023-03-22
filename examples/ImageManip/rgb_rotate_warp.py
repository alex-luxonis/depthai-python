#!/usr/bin/env python3

"""
This example shows usage of ImageManip to crop a rotated rectangle area on a frame,
or perform various image transforms: rotate, mirror, flip, perspective transform.
"""

import depthai as dai
import cv2
import numpy as np
import time

keyRotateDecr = 'z'
keyRotateIncr = 'x'
keyWarpTestCycle = 'c'

angleInc = 5.0

def printControls():
    print("=== Controls:")
    print(keyRotateDecr, "-rotated rectangle crop, decrease angle by", angleInc)
    print(keyRotateIncr, "-rotated rectangle crop, increase angle by", angleInc)
    print(keyWarpTestCycle, "-warp 4-point transform, cycle through modes")
    print("h -print controls (help)")

'''
The crop points are specified in clockwise order,
with first point mapped to output top-left, as:
    P0  ->  P1
     ^       v
    P3  <-  P2
'''

# Note: less than 10 size seems to fail with ImageManip!
w, h = 10, 10
#w, h = 11, 11

P0 = [0  ,   0]  # top-left
P1 = [w-1,   0]  # top-right
P2 = [w-1, h-1]  # bottom-right
P3 = [0  , h-1]  # bottom-left

warpList = [
    # points order, normalized cordinates, description
    # [[[0, 0], [1, 0], [1, 1], [0, 1]], True, "passthrough"],
    # [[[0, 0], [639, 0], [639, 479], [0, 479]], False, "passthrough (pixels)"],
    [[P0, P1, P2, P3], False, "1. passthrough"],
    [[P3, P0, P1, P2], False, "2. rotate 90"],
    [[P2, P3, P0, P1], False, "3. rotate 180"],
    [[P1, P2, P3, P0], False, "4. rotate 270"],
    [[P1, P0, P3, P2], False, "5. horizontal mirror"],
    [[P3, P2, P1, P0], False, "6. vertical flip"],
    [[[-0.1, -0.1], [1.1, -0.1], [1.1, 1.1], [-0.1, 1.1]], True, "7. add black borders"],
    [[[-0.3, 0], [1, 0], [1.3, 1], [0, 1]], True, "8. parallelogram transform"],
    [[[-0.2, 0], [1.8, 0], [1, 1], [0, 1]], True, "9. trapezoid transform"],
]

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
imageSrc = pipeline.create(dai.node.XLinkIn)
camRgb = pipeline.create(dai.node.ColorCamera)
manip = pipeline.create(dai.node.ImageManip)

manipOut = pipeline.create(dai.node.XLinkOut)
manipCfg = pipeline.create(dai.node.XLinkIn)

imageSrc.setStreamName("input")
manipOut.setStreamName("manip")
manipCfg.setStreamName("manipCfg")

# Linking
imageSrc.out.link(manip.inputImage)
manip.out.link(manipOut.input)
manipCfg.out.link(manip.inputConfig)

def show_status(msg):
    status = np.zeros((70, 1280, 3), np.uint8)
    cv2.putText(status, msg, (5,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1)
    cv2.imshow("status", status)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Create input & output queues
    qSource = device.getInputQueue(name="input", maxSize=4)
    qManip = device.getOutputQueue(name="manip", maxSize=4)
    qManipCfg = device.getInputQueue(name="manipCfg")

    key = -1
    angleDeg = 0
    testFourPt = False
    warpIdx = -1

    printControls()

    for c in ["input", "manip"]:
        cv2.namedWindow(c, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(c, (640, 640))

    while key != ord('q'):
        center = (w / 2, h / 2)
        # TBD center = ((w+1) // 2, (h+1) // 2)
        f = np.zeros((h, w), np.uint8)
        f[0, 0], f[0, 2], f[0, 4] = 255, 255, 255
        f[2, 0], f[2, 2], f[2, 4] = 255, 255, 255
        f[0, w-1] = 255
        f[h-1, 0] = 255
        f[h-1, w-1] = 255
        f[h//2, w//2] = 255
        img = dai.ImgFrame()
        img.setData(f)
        img.setTimestamp(time.monotonic())
        img.setWidth(w)
        img.setHeight(h)
        img.setType(dai.ImgFrame.Type.GRAY8)
        cv2.imshow("input", f)
        qSource.send(img)
        if key > 0:
            if key == ord(keyRotateDecr) or key == ord(keyRotateIncr):
                if key == ord(keyRotateDecr): angleDeg -= angleInc
                if key == ord(keyRotateIncr): angleDeg += angleInc
                testFourPt = False
                print("Crop rotated rectangle, angle: {:.1f} degrees".format(angleDeg))
            elif key == ord(keyWarpTestCycle):
                warpIdx = (warpIdx + 1) % len(warpList)
                testFourPt = True
                testDescription = warpList[warpIdx][2]
                print("Warp 4-point transform: ", testDescription)
            elif key == ord('h'):
                printControls()

        # Send an updated config with continuous rotate, or after a key press
        if key >= 0 or (not testFourPt):
            cfg = dai.ImageManipConfig()
            if testFourPt:
                test = warpList[warpIdx]
                points, normalized = test[0], test[1]
                point2fList = []
                for p in points:
                    pt = dai.Point2f()
                    pt.x, pt.y = p[0], p[1]
                    point2fList.append(pt)
                cfg.setWarpTransformFourPoints(point2fList, normalized)
                show_status(f"4-point {testDescription}: {points}")
            else:
                rotatedRect = (center, (w, h), angleDeg)
                show_status(f"rotatedRect: center {center}, size {w}x{h}, angle {angleDeg}")
                rr = dai.RotatedRect()
                rr.center.x, rr.center.y = rotatedRect[0]
                rr.size.width, rr.size.height = rotatedRect[1]
                rr.angle = rotatedRect[2]
                cfg.setCropRotatedRect(rr, False)
            # cfg.setWarpBorderFillColor(255, 0, 0)
            # cfg.setWarpBorderReplicatePixels()
            cfg.setFrameType(dai.ImgFrame.Type.GRAY8)
            qManipCfg.send(cfg)

        for q in [qManip]:
            pkt = q.get()
            name = q.getName()
            frame = pkt.getCvFrame()
            cv2.imshow(name, frame)
        key = cv2.waitKey(20)
