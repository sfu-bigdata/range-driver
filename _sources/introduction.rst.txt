Introduction
============

This is the documentation for a currently unnamed (suggestions welcome!) acoustic telemetry toolkit. This Python package
is meant to provide the tools for analyzing underwater acoustic range test data to determine what factors have the
largest impact on detection range. This toolkit provides functionality for integrating environmental data (wave height,
wind speed, salinity, etc) from both public data sources (using
`kadlu <https://docs.meridian.cs.dal.ca/kadlu/index.html>`_) and any private data sets a user might have access to.
Once these datasets have been integrated, our toolkit's plotting submodule can be used to visually examine
the relationships between environmental variables and the detection performance of the acoustic arrays. 


We are preparing to release this toolkit (with a real name) during the first quarter of 2021 under the `GNU GPLv3
license <https://www.gnu.org/licenses/>`_. This means it (and its code) will be freely available for anyone to use or
modify for their own purposes. Initially, the package will be available for download from a public git repository. In
the future, it will also be available on PyPI, Python's package index.

This toolkit is being developed by the `MERIDIAN <http://meridian.cs.dal.ca/>`_ team at `Simon Fraser University's
Big Data Initiative <https://www.sfu.ca/big-data/>`_ in collaboration with the the `MERIDIAN 
<http://meridian.cs.dal.ca/>`_ Data Analytics Team at the `Institute for Big Data Analytics 
<https://bigdata.cs.dal.ca/>`_ at Dalhousie University and Jon Pye from `Ocean Tracking Network 
<https://oceantrackingnetwork.org>`_.
