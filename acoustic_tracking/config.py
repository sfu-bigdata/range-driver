import pandas as pd
import numpy as np

from .dict_utils import *
from acoustic_tracking.utils import *


# ----------------------------------------------------------------------------
# configuration processing
def prepare_bounds(bounds):
    try:
        bounds.update(dict(
            south=bounds.lat_center - bounds.s_offset,
            north=bounds.lat_center + bounds.n_offset))
    except AttributeError:
        pass
    try:
        bounds.update(dict(
            west=bounds.lon_center - bounds.w_offset, 
            east=bounds.lon_center + bounds.e_offset))
    except AttributeError:
        pass
    bounds['start'] = pd.to_datetime(bounds['start']).to_pydatetime()
    bounds['end'] = pd.to_datetime(bounds['end']).to_pydatetime()


def make_params(config):
    """
    Creates a params object from our configuration, for use during plotting and reporting.
    """
    params = copy.deepcopy(config.view.params)
    params.t2bins = np.arange(0, params.t2bin_max + 1e-4, params.t2bin_stepsize)
    params.out = make_Bunch("State and output of detection processing") # outputs are not parameters, maybe separate 
    return params


def get_column_info(config):
    """
    Retreives the column information from the configuration object, including which columns have
    been indicated for further analysis.
    """
    columns = config.view.columns
    colnames = dict(zip(columns, list(s.replace("_", " ") for s in columns)))
    colnames.update(config.view.colnames)
    column = config.view.column
    return columns, colnames, column


path_vars = {'repo_path': repo_path()}


def prepend_data_dir(d, keys=None, data_dir_key='data_dir'):
    if data_dir_key in d:
        data_dir = d[data_dir_key]
        if data_dir:
            data_dir = data_dir.format(**path_vars)
        del d[data_dir_key]
    else:
        data_dir = ''
    if keys == None:
        keys = set(d.keys()).difference(data_dir_key)
    for key in keys:
        d[key] = os.path.join(data_dir, d[key].format(**path_vars))


config_prepare_hooks = {
    'file_map': prepend_data_dir,
    'bounds': prepare_bounds,
    'reader:otn': lambda otn: prepend_data_dir(otn, keys=['detections_csv',
                                                          'otn_metadata',
                                                          'vendor_tag_specs']),
    'reader:nsog': lambda nsog: prepend_data_dir(nsog, keys=['detections_csv',
                                                             'vendor_tag_specs']),
    'data:tidal': lambda otn: prepend_data_dir(otn, keys=['tidal_times_ods',
                                                          'tidal_times_output_csv',
                                                          'tidal_interpolation_output_csv']),
    }


def prepare_config(config, config_prepare_hooks=config_prepare_hooks):
    """
    Apply transformations to config dicts to make them easier to use.

    :param config: Configuration dictionary to transform
    :type config: dict

    :param config_prepare_hooks: Dictionary of the functions.  which will be used to transform the
           config dictionaries. Keys can contain ":" separators to access nested elements.
    :type config_prepare_hooks: dict

    :return: A new dictionary which is created by applying the config_prepare_hooks functions to the
             config dictionary.
    :rtype: dict

    """
    keysep = ":"
    for nkey, func in list(config_prepare_hooks.items()):
        keys = nkey.split(keysep)
        try:
            dv = nested_value(config, keys)
        except:
            continue
        func(dv)
