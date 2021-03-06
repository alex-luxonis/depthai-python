02 - Mono Preview
=================

This example shows how to set up a pipeline that outputs the left and right grayscale camera
images, connects over XLink to transfer these to the host real-time, and displays both using OpenCV.

Demo
####

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/NLIIazhE6O4" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Setup
#####

Please run the following command to install the required dependencies

.. code-block:: bash

  python3 -m pip install --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-snapshot-local/ depthai==0.0.2.1+8fd7384f6658c57dd1a439e4801bfe2718e5a25c numpy==1.19.5 opencv-python==4.5.1.48

For additional information, please follow :ref:`Python API installation guide <Installation - Python>`

Source code
###########

Also `available on GitHub <https://github.com/luxonis/depthai-python/blob/gen2_develop/examples/02_mono_preview.py>`__

.. literalinclude:: ../../../examples/02_mono_preview.py
   :language: python
   :linenos:

.. include::  /includes/footer-short.rst
