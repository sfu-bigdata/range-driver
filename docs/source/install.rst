.. _installation_instructions:

Install
=============

The Acoustic Tracking package remains in development phase. During this time, the easiest way to install the package is throug it's GitLab repository. 

 1. Clone the repository

 2. From within the range_driver directory, install dependencies using Anaconda. ::

	conda env create -f environment.yml python=3.6

 3. Activate the conda environment. ::

	conda activate acoustic_env

 4. From within the range_driver repository, install Acoustic Tracking. ::

	pip install -e .
