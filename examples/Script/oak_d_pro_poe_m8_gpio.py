#!/usr/bin/env python3
import depthai as dai
import time

pipeline = dai.Pipeline()

script = pipeline.create(dai.node.Script)
script.setScript("""
import GPIO
import time

# Configure AUX_GPIO_3V3 mode as output, or input if False
auxOutput = True
# auxOutput = False

FSYNC_GPIO = 41  # Note: inverted due to isolation circuitry
AUX_GPIO_3V3 = 52  # or 61, or 63
AUX_GPIO_DIR = 6

if 1:  # Fix up GPIO 61 being driven output-low from FW initialization
    GPIO.setup(61, GPIO.IN, GPIO.PULL_NONE)

if auxOutput:
    outVal = 0
    GPIO.setup(AUX_GPIO_3V3, GPIO.OUT, GPIO.PULL_NONE)
    GPIO.setup(AUX_GPIO_DIR, GPIO.OUT, GPIO.PULL_NONE)
    GPIO.write(AUX_GPIO_DIR, 1)
else:
    GPIO.setup(AUX_GPIO_3V3, GPIO.IN, GPIO.PULL_NONE)

GPIO.setup(FSYNC_GPIO, GPIO.IN, GPIO.PULL_NONE)

while True:
    node.warn('')  # separator
    if auxOutput:
        GPIO.write(AUX_GPIO_3V3, outVal)
        node.warn(f'AUX  output ({AUX_GPIO_3V3}) set to: {outVal}')
        outVal = 1 - outVal  # toggle for next iteration
    else:
        val = GPIO.read(AUX_GPIO_3V3)
        node.warn(f'AUX   input ({AUX_GPIO_3V3}) is: {val}')

    val = GPIO.read(FSYNC_GPIO)
    node.warn(f'FSYNC input ({FSYNC_GPIO}) is: {val}')

    time.sleep(1)
""")

with dai.Device(pipeline) as device:
    while True:
        time.sleep(0.1)
