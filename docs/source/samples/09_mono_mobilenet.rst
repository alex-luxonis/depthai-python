09 - Mono & MobilenetSSD
========================

This example shows how to run MobileNetv2SSD on the left grayscale camera and how to display the
neural network results on a preview of the right camera stream.

Demo
####

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/liTGGyJwZ_8" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Setup
#####

Please run the following command to install the required dependencies

.. code-block:: bash

  python3 -m pip install --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-snapshot-local/ depthai==0.0.2.1+8fd7384f6658c57dd1a439e4801bfe2718e5a25c numpy==1.19.5 opencv-python==4.5.1.48

For additional information, please follow :ref:`Python API installation guide <Installation - Python>`

This example also requires MobilenetSDD blob (:code:`mobilenet.blob` file) to work - you can download it from
`here <https://artifacts.luxonis.com/artifactory/luxonis-depthai-data-local/network/mobilenet.blob>`__

Source code
###########

Also `available on GitHub <https://github.com/luxonis/depthai-python/blob/gen2_develop/examples/09_mono_mobilenet.py>`__

.. literalinclude:: ../../../examples/09_mono_mobilenet.py
   :language: python
   :linenos:

.. include::  /includes/footer-short.rst
