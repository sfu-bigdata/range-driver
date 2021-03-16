.. _installation_instructions:

Install
=============

The range-driver package remains in development phase. During this time, the easiest way to install the package is
through it's `GitHub repository <https://github.com/sfu-bigdata/range-driver/>`_. From the command line follow these
steps:

#. Clone the repository to your local machine.

#. From within the ``range_driver`` directory, install dependencies using Anaconda.

   .. code-block :: bash

	conda env create -f environment.yml

#. Activate the conda environment.

   .. code-block :: bash

	conda activate range-driver

#. From within the ``range-driver`` repository, install range-driver.

   .. code-block :: bash

	pip install -e .

