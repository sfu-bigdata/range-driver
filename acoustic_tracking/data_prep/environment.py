"""
    Functions to help integrate environmental data processing. Includes kadlu integration.
"""
from scipy.interpolate import griddata
import kadlu
import copy
import numpy as np
import pandas as pd
import xarray as xr


def add_kadlu_env_data(bounds, sources, detection_df):
    """
    Fetches the requested environmental data for the given region & time. The data is interpolated
    across space (2D or 3D) and time before being merged into a new version of detection_df.

    :param bounds: Dictionary containing the boundaries (space & time) which will be used to fetch
                   data from kadlu. Must include `north`, `south`, `east`, `west`, `start`, `end`,
                   `top`, and `bottom`.
    :type bounds: dict

    :param sources: Dictionary containing a variable -> source mapping.
    :type sources: dict.

    :param detection_df: Dataframe containing detection data.
    :type detection_df: pandas.DataFrame

    :return: - **detection_df_env** (`pandas.DataFrame`) - A copy of detection_df where interpolated
               environment data has been added.
             - **kadlu_result** (`numpy.array`) - The raw result from kadlu (not interpolated)
    """
    detection_df_copy = copy.copy(detection_df)

    axes_to_interpolate = [detection_df_copy['Receiver.lat'],
                           detection_df_copy['Receiver.lon'],
                           [d.timestamp() for d in detection_df_copy['datetime']],
                           detection_df_copy['Receiver.depth']]

    for load_func, source in sources.items():
        col_name = '_'.join(load_func.split('_')[1:])
        kadlu_result = kadlu.load(source=source, var=col_name, **bounds)
        interpolations = interpolate(kadlu_result, axes_to_interpolate)

        detection_df_copy[col_name] = interpolations

    # TODO: kadlu_result is currently only the last result. Should probably be a list of results
    return detection_df_copy, kadlu_result


def add_custom_env_data(axes_to_interpolate, variable_file_map, detection_df):
    """
    Loads the specified custom environmental data. The loaded data is interpolated across space
    (2D or 3D) and time before being merged into a new version of detection_df.

    :param axes_to_interpolate: List of axes to interpolate over. The axes correspond to (1)
                                latitude, (2) longitude, (3) time, and (4) depth. The axes must be
                                provided in this order. The first 3 axes are mandatory, depth is
                                optional.
    :type axes_to_interpolate: list

    :param variable_file_map: A bunch dictionary specifying which files should be used to load
                              environmental data. Keys are the names of variables to load while
                              values are the paths to the files containing the data.
    :type variable_file_map: sklearn.utils.Bunch

    :param detection_df: Dataframe containing detection data.
    :type detection_df: pandas.DataFrame

    :return: A copy of detection_df where the interpolated custom environment data has been added.
    :rtype: pandas.DataFrame
    """

    for colname, file in variable_file_map.items():
        # Read in the XArray & Convert into a DF
        data_set = xr.open_dataset(file)
        df = data_set.to_dataframe()
        df_no_nans = df[~df[colname].isna()]
        df_no_index = df_no_nans.reset_index()

        # Retrieve the data to interpolate
        df_no_index['time_int'] = df_no_index['time'].astype('int64') // 1e9
        try:
            data_to_interpolate = df_no_index[[colname, 'lat', 'lon', 'time_int', 'depth']]
        except KeyError:
            data_to_interpolate = df_no_index[[colname, 'lat', 'lon', 'time_int']]

        # Do the interpolation
        interpolations = interpolate(data_to_interpolate, axes_to_interpolate)

        # Set the column
        detection_df[colname] = interpolations

    return detection_df


def interpolate(data_to_interpolate, axes_to_interpolate):
    # Check if time is timestamp or not
    if isinstance(data_to_interpolate, pd.DataFrame):
        data_to_interpolate = np.array([list(data_to_interpolate[x]) for x in data_to_interpolate])
        val = data_to_interpolate[0]
        lat = data_to_interpolate[1]
        lon = data_to_interpolate[2]
        ts = data_to_interpolate[3]

    else:
        val = data_to_interpolate[0]
        lat = data_to_interpolate[1]
        lon = data_to_interpolate[2]
        ts_tmp = pd.Series(map(kadlu.epoch_2_dt, data_to_interpolate[3]))
        ts = pd.Series([d.timestamp() for d in ts_tmp])

    # Interpolate
    try:
        # 4D Grid Data
        depth = data_to_interpolate[4]
        points = np.array(list(zip(lat, lon, ts, depth)))
        values = np.array(val)
        points_to_interpolate = list(zip(*axes_to_interpolate))
        requests = np.array(points_to_interpolate)
        interpolations = griddata(points, values, requests, method='nearest')
    except IndexError:
        # 3D Grid Data
        points = np.array(list(zip(lat, lon, ts)))
        values = np.array(val)
        points_to_interpolate = list(zip(*axes_to_interpolate[:3]))
        requests = np.array(points_to_interpolate)
        interpolations = griddata(points, values, requests, method='nearest')

    return interpolations

