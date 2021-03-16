""" 
    tidal table processing
"""

import pandas as pd
import numpy as np
from range_driver.utils import *


def flatten_tidal_table(df, year, format_str="%d %B %Y %H%M", display=False):
    """ Convert a multi-column tidal table (up to 4 extrema per day) into a flat
        datetime indexed DataFrame.
        `df` is expected to have time1, height1, time2, height2, ..., height4 columns
    """
    dflat = None
    for cn in range(1,5):
        tc = "time{}".format(cn)
        hc = "height{}".format(cn)
        timehhmm = df[tc]
        heights = df[hc]
        if False: # don't interpolate, just drop NaN's
            heights = heights.interpolate("linear")
            timehhmm = timehhmm.interpolate("pad")
        is_miss = df[hc].isnull()
        dff = pd.concat([pd.to_datetime(
                            df['Day'].map(int).map(str) + " " + df['Month'] + " {} ".format(year) + timehhmm,
                            format=format_str).rename("time"),
                         heights.rename("height")],
                        axis=1).set_index("time")
        if dflat is None:
            dflat = dff
        else:
            dflat = dflat.append(dff)
    dflat = dflat.dropna().sort_values(by="time")
    rising = (dflat["height"].diff(-1) < 0).values   # diff(-1) is current - next value, last is NaN
    rising[-1] = not rising[-2]
    dflat['highlow'] = np.array(['h','l'])[rising.astype(int)] # tide that's not rising is 'h'
    if display:
        display_full_df(dflat)
    return dflat


def ipf_cos(t):
    """ Interpolation function based on cosine smoothly progressing in t = [0,1]
    First derivative at interval end points is 0 (flat).
    
    Returns:
        0 - if t=0
        1 - if t=1
    """
    return 0.5 * (1-np.cos(t*np.pi))


def tidal_phase(dflat, new_times=None, interpolation_func=ipf_cos):
    """ Calcualte tidal phase and tidal height changes
        `dflat` DataFrame is expected to have datetime index and columns
        'height', 'highlow' where dflat['highlow'] == 'h' indicates high tide
    
    Returns:
        DataFrame based on `dflat` with additional columns
        'time_start', 'duration', 'height_start', 'height_change',
        and 'dheight_cm_per_hr'"""
    
    dflat["duration"] = 0 #np.nan
    durcol = dflat.columns.get_loc("duration")
    dflat.iloc[:-1, durcol] = dflat.index[1:] - dflat.index[:-1]
    dflat.iloc[-1, durcol] = dflat.iloc[-2, durcol]
    dflat["time_start"] = dflat.index
    dflat["height_start"] = dflat['height']
    dflat["height_change"] = -dflat['height'].diff(-1)

    #new_times = pd.date_range("2016-03-07 00:18", "2016-04-05 18:23", freq="300s")
    #new_times = df_detections_merged.datetime
    if new_times is not None:
        # .astype(...) is needed to ensure the index doesn't loose its datetime type (pandas bug?)
        new_index = dflat.index.union(new_times).drop_duplicates().astype(dflat.index.dtype)
        dfi = dflat.reindex(new_index)

        for col in ['highlow', 'duration', 'time_start', 'height_start', 'height_change']:
            dfi[col].interpolate("pad", inplace=True)
    else:
        dfi = dflat

    dfi['t'] = (dfi.index - dfi['time_start']) / dfi['duration']
    dfi['t2'] = dfi['t'] + (dfi['highlow'] == 'h')
    dfi['height'] = dfi['height_start'] + (dfi['height_change'] * interpolation_func(dfi['t']))

    #len(dfi), len(-dfi.height.diff(-1)[:-1] / ((dfi.index[1:] - dfi.index[:-1]) / pd.Timedelta("1h")))
    #dfi["dheight_cm_per_hr"] = dheight_cm_per_hr

    dfi['dheight_cm_per_hr'] = -dfi['height'].diff(-1)[:-1] / ((dfi.index[1:] - dfi.index[:-1]) / pd.Timedelta("1h"))
    return dfi
