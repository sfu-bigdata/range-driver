"""Convenience functions for dictionary access and YAML"""

from sklearn.utils import Bunch
from collections import OrderedDict
from collections.abc import Mapping
import copy
import yaml

# ----------------------------------------------------------------------------
# manipulate class objects

def set_class_dict(cls, clsdict):
    """Set builtin class properties"""
    return type(cls.__name__, (cls,), clsdict)

def set_docstr(cls, docstr, **kwargs):
    """Modify the docstring of a class `cls`"""
    return set_class_dict(cls, {'__doc__': docstr, **kwargs})


# ----------------------------------------------------------------------------
# working with dict and Bunch
def deep_update(d1, d2):
    """
    Recursively updates `d1` with `d2`

    :param d1: A dictionary (possibly nested) to be updated.
    :type d1: dict

    :param d2: A dictionary (possibly nested) which will be used to update d1.
    :type d2: dict

    :return: An updated version of d1, where d2 values were used to update the values of d1. Will
             add d2 keys if not present in d1. If a key does exist in d1, that key's value will be
             overwritten by the d2 value. Works recursively to update nested dictionaries.
    :rtype: dict
    """
    if all((isinstance(d, Mapping) for d in (d1, d2))):
        for k, v in d2.items():
            d1[k] = deep_update(d1.get(k), v)
        return d1
    return d2


def nested_value(d, keys):
    """Access an element in nested dictioary `d` with path given by list of `keys`"""
    for k in keys:
        d = d[k]
    return d


def select_keys(d, keys):
    """Returns the items in dict `d` whose keys are listen in `keys`"""
    return {k: v for k, v in d.items() if k in keys}


def merge_dicts(d1, d2):
    """
    Performs a deep_update() of d1 using d2.
    Recursively updates `d1` with `d2`, while also making a deep copy of d1.

    :param d1: A dictionary (possibly nested) to be updated.
    :type d1: dict

    :param d2: A dictionary (possibly nested) which will be used to update d1.
    :type d2: dict

    :return: An updated & deep-copied version of d1, where d2 values were used to update the values
             of d1. Will add d2 keys if not present in d1. If a key does exist in d1, that key's
             value will be overwritten by the d2 value. Works recursively to update nested
             dictionaries.
    :rtype: dict
    """
    """Recursively update `d1` with `d2` using a deep copy of `d1`"""
    md = copy.deepcopy(d1)
    return deep_update(md, d2)


def make_Bunch(docstr, *args, **kwargs):
    '''Construct a Bunch collection with alternative doc string
       All arguments after `docstr` are passed to the Bunch dict constructor.
       The main appeal of a bunch d over a dict, is that keys can be accessed 
       via d.key rather than just d['key']

    Example:
        B = make_Bunch("""Container for special custom data""",a=1)
        B.b = 3
        print(B)
        help(B)
    '''
    # TODO: the docstring modification causes issue with pickle serialization
    # If you might want to use pickle, consider to just construct the sklearn.utils.Bunch
    # object directly and don't use this construciton method here.
    return set_docstr(Bunch, docstr)(*args, **kwargs)


# ----------------------------------------------------------------------------
# YAML functions
class YAMLProcessingError(Exception):
    """Indicate downstream processing error of loaded YAML structure"""
    pass


def _map_from_ordered_pairs(pairs, MapType=Bunch):
    """Construct a custom dict type (e.g. Bunch) from pairs."""
    return MapType(**dict(pairs)) # dict in python >= 3.6, preserves insertion order


def _ordered_load(stream, Loader=yaml.Loader, MapType=Bunch, **kwargs):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return _map_from_ordered_pairs(loader.construct_pairs(node), MapType=MapType)

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader, **kwargs)


def _dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


def _setup_yaml():
    """Have custom dict types produce standard format YAML output for dicts"""
    yaml.add_multi_representer(OrderedDict, _dict_representer)
    yaml.add_multi_representer(Bunch, _dict_representer)


def yload(datastr, Loader=yaml.SafeLoader, MapType=Bunch, **kwargs):
    """
    Load object from YAML input string or stream

    :param datastr: A string or stream containing YAML formatted text
    :type datastr: str or stream

    :param Loader: The yaml loader object to use, defaults to yaml.SaveLoader
    :type Loader: yaml.Loader Object, optional

    :param MapType: type of dictionary to construct, defaults to Bunch
    :type MapType: type, optional

    :param kwargs: Further keyword args are passed on to yaml.load()

    :return: Python object representation of the YAML string/stream
    :rtype: Specified in MapType parameter
    """

    return _ordered_load(datastr, Loader=Loader, MapType=MapType, **kwargs)


def ydump(data, *args, sort_keys=False, **kwargs):
    """
    Create YAML output string for data object. If data is an OrderedDict, original key ordering
    is preserved in internal call to yaml.dump().

    :param data:
    :type data: dict or Bunch

    :param args: Additional args passed on to yaml.dump()

    :param sort_keys: defaults to False
    :type sort_keys: bool

    :param kwargs: Further keyword args are passed on to yaml.dump()

    :return: YAML string representation of data
    :rtype: str
    """

    return yaml.dump(data, *args, sort_keys=sort_keys, **kwargs)


_setup_yaml()
