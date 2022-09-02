#!/usr/bin/env python3

import cv2
import depthai as dai

print("Press C to capture a set of frames, Q to quit")

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
monoVertical = pipeline.create(dai.node.MonoCamera)
xoutLeft = pipeline.create(dai.node.XLinkOut)
xoutRight = pipeline.create(dai.node.XLinkOut)
xoutVertical = pipeline.create(dai.node.XLinkOut)

xoutLeft.setStreamName('left')
xoutRight.setStreamName('right')
xoutVertical.setStreamName('vertical')

# Properties
monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
monoVertical.setBoardSocket(dai.CameraBoardSocket.VERTICAL)
monoVertical.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

# Linking
monoRight.out.link(xoutRight.input)
monoLeft.out.link(xoutLeft.input)
monoVertical.out.link(xoutVertical.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Output queues will be used to get the grayscale frames from the outputs defined above
    qLeft = device.getOutputQueue(name="left", maxSize=30, blocking=True)
    qRight = device.getOutputQueue(name="right", maxSize=30, blocking=True)
    qVertical = device.getOutputQueue(name="vertical", maxSize=30, blocking=True)

    cnt = 0
    prevL, prevR, prevV = 0, 0, 0
    tFrame = 1 / monoLeft.getFps()  # 0.033s, for 30fps
    print("Diff: L-prevL-FT R-prevR-FT V-prevV-FT L-R L-V   (FT=frametime)")
    while True:
        # Instead of get (blocking), we use tryGet (non-blocking) which will return the available data or None otherwise
        inL = qLeft.get()
        inR = qRight.get()
        inV = qVertical.get()
        tstampL = inL.getTimestamp().total_seconds()
        tstampR = inR.getTimestamp().total_seconds()
        tstampV = inV.getTimestamp().total_seconds()
        if 0:
            print(f'>>> L:{inL.getSequenceNum()} t:{tstampL}')
            print(f'    R:{inR.getSequenceNum()} t:{tstampR}')
            print(f'    V:{inV.getSequenceNum()} t:{tstampV}')
        jitterL = (tstampL - prevL - tFrame) * 1000
        jitterR = (tstampR - prevR - tFrame) * 1000
        jitterV = (tstampV - prevV - tFrame) * 1000
        diffLR = (tstampL - tstampR) * 1000
        diffLV = (tstampL - tstampV) * 1000
        print(f'{jitterL:7.3f} {jitterR:7.3f} {jitterV:7.3f} {diffLR:6.3f} {diffLV:6.3f}')
        prevL = tstampL
        prevR = tstampR
        prevV = tstampV

        frameL = inL.getCvFrame()
        frameR = inR.getCvFrame()
        frameV = inV.getCvFrame()

        cv2.imshow("left", frameL)
        cv2.imshow("right", frameR)
        cv2.imshow("vertical", frameV)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif 0 or key == ord('c'):
            print("Saving, iter", cnt)
            cv2.imwrite(str(cnt)+"_left_"    +str(tstampL)+".png", frameL)
            cv2.imwrite(str(cnt)+"_right_"   +str(tstampR)+".png", frameR)
            cv2.imwrite(str(cnt)+"_vertical_"+str(tstampV)+".png", frameV)
            cnt += 1
