"""Enable parent folder imports relative from current work directory (e.g. notebook launch path)
Drop this module into any sub-folder of the repo that is not part of the published module code.
"""

import os

module_path = os.path.dirname(__file__)

def module_path_join(*relpath):
    """Use module_path_join("..") to construct a path relative (e.g, parent folder) from
the location of this_path.py"""
    return os.path.join(module_path, *relpath)

def sys_path_append(*relpath):
    """Extend sys.path with folder relative to module path, e.g. sys_path_append('..')"""
    import sys
    addpath = module_path_join(*relpath)
    sys.path.append(addpath)
    return addpath
