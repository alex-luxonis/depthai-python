#!/usr/bin/env python3

import cv2
import depthai as dai
import time
import math

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
imu = pipeline.create(dai.node.IMU)
xlinkOut = pipeline.create(dai.node.XLinkOut)

xlinkOut.setStreamName("imu")

# enable ROTATION_VECTOR at 400 hz rate
imu.enableIMUSensor(dai.IMUSensor.ROTATION_VECTOR, 10)
# above this threshold packets will be sent in batch of X, if the host is not blocked and USB bandwidth is available
imu.setBatchReportThreshold(1)
# maximum number of IMU packets in a batch, if it's reached device will block sending until host can receive it
# if lower or equal to batchReportThreshold then the sending is always blocking on device
# useful to reduce device's CPU load  and number of lost packets, if CPU load is high on device side due to multiple nodes
imu.setMaxBatchReports(10)

# Link plugins IMU -> XLINK
imu.out.link(xlinkOut.input)

# Script node
script = pipeline.create(dai.node.Script)
script.setScript("""
    while True:
        imuData = node.io['imu'].get()
        imuPackets = imuData.packets
        for imuPacket in imuPackets:
            rVvalues = imuPacket.rotationVector
            ts = rVvalues.timestamp.get().total_seconds()
            tsDev = rVvalues.tsDevice.get().total_seconds()
            seq = rVvalues.sequence
            node.warn(f'Got pkt {seq}, ts {ts}, tsDev {tsDev}')
""")
imu.out.link(script.inputs['imu'])

# Pipeline is defined, now we can connect to the device
with dai.Device(pipeline) as device:
    # Output queue for imu bulk packets
    imuQueue = device.getOutputQueue(name="imu", maxSize=50, blocking=False)
    prevDiff = None
    while True:
        imuData = imuQueue.get()  # blocking call, will wait until a new data has arrived

        imuPackets = imuData.packets
        for imuPacket in imuPackets:
            rVvalues = imuPacket.rotationVector
            ts = rVvalues.timestamp.get().total_seconds()
            tsDev = rVvalues.tsDevice.get().total_seconds()
            seq = rVvalues.sequence
            print(f'==================== HOST ========================= Got pkt {seq}, ts {ts}, tsDev {tsDev}')
            if 1: # Just checking timesync...
                diff = round(ts - tsDev, 6) * 1000
                if prevDiff != None and prevDiff != diff:
                    print()
                    print(f'===== Timesync diff changed!!! ===== delta from previous {diff - prevDiff:.3f} ms')
                    print()
                prevDiff = diff

        if cv2.waitKey(1) == ord('q'):
            break
