"""Generic utility functions"""

import os
import subprocess
import sys
import importlib

# ----------------------------------------------------------------------------
# file path management
# interact with shell (to get git info)

def eval_shell(cmdargs):
    """ Run command in shell and return string output.
        Input `cmdargs` is list of command and individual args."""
    return (subprocess.
            Popen(cmdargs,
                  stdout=subprocess.PIPE)
            .communicate()[0]
            .rstrip()
            .decode('utf-8')
            )

_repo_path = None

def repo_path():
    global _repo_path
    if not _repo_path:
        _repo_path = eval_shell('git rev-parse --show-toplevel'.split())
    return _repo_path

def repo_file_path(*fn, folder="data"):
    return os.path.join(repo_path(), folder, *fn)

def load_file(filename):
    """
    Loads and returns the contents of filename.

    :param filename: A string containing the filepath of the file to be loaded/
    :type filename: str

    :return: Contents of the loaded file.
    :rtype: str
    """
    with open(filename, "r") as fh:
        return fh.read()

# ----------------------------------------------------------------------------

# Python 2 + 3 compatible string type
try:
    basestring
except NameError:
    basestring = str

# ----------------------------------------------------------------------------
# module reloading

def reload_all(module_name):
    """Reload all modules that have `module_name` in their path."""
    def num_dots(st):
        return sum(l=='.' for l in st[0])
    def get_modules():
        for mn, mo in sys.modules.items():
            try:
                if mn[:2] == '__':
                    continue
                if module_name in mo.__file__:
                    yield mn, mo
            except:
                pass
    for mn, mo in sorted(get_modules(), key=num_dots, reverse=True):
        #print('import {}'.format(mn))
        importlib.reload(mo)

def reload_acoustic(module_name="acoustic", env_name="acoustic_env"):
    for _, mo in sys.modules.copy().items():
        try:
            if module_name in mo.__file__.split(env_name)[-1]:
                importlib.reload(mo)
        except:
            pass
