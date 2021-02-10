"""
    Tools for acoustic tracking performance studies

    Features:
    - merge detection data with external, environmental data
    - data cleaning and preparation for statistical analysis
    - calculation of detection rate from range test data
    - visualization for data screening
    - [TODO] calculation of factor importance to explain variations in detection performance
    - [TODO] help with placement of receivers to ensure detection performance within area of interest
"""

from .data_prep import *
from .ipython_utils import *
from .dict_utils import *
from .utils import *
from .plotting import *
from .reporting import *
from .config import *
from .detections import Detections, read_ods
