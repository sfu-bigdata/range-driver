Introduction
============

This is the documentation for the Range Driver Python package. This Python package provides tools for analyzing
underwater acoustic range test data to determine what factors have the largest impact on detection range. This toolkit
provides functionality for integrating environmental data (wave height, wind speed, salinity, etc) from public data
sources (using `kadlu <https://docs.meridian.cs.dal.ca/kadlu/index.html>`_) and private datasets a user may have on
hand. Once these datasets have been integrated, our toolkit's plotting submodule can be used to visually examine the
relationships between environmental variables and the detection performance of the acoustic arrays.

We are preparing to release Range Driver under the `GNU GPLv3 license <https://www.gnu.org/licenses/>`_. This means it
(and its code) will be freely available for anyone to use or modify for their own purposes. Currently, Range Driver is
available for download from its `public GitHub repository <https://github.com/sfu-bigdata/range-driver>`_. In the
future, it will also be available on PyPI, Python's package index.

Range Driver is being developed by the `MERIDIAN <http://meridian.cs.dal.ca/>`_ team at `Simon Fraser University's
Big Data Initiative <https://www.sfu.ca/big-data/>`_ in collaboration with the the `MERIDIAN 
<http://meridian.cs.dal.ca/>`_ Data Analytics Team at the `Institute for Big Data Analytics 
<https://bigdata.cs.dal.ca/>`_ at Dalhousie University and Jon Pye from `Ocean Tracking Network 
<https://oceantrackingnetwork.org>`_.
