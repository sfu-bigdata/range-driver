import pandas as pd
import numpy as np

from .metadata import *
from .tidal import *
from acoustic_tracking.geo_utils import dist_m
from acoustic_tracking.utils import *
from acoustic_tracking.pandas_utils import *
from acoustic_tracking.dict_utils import *

from .metadata import read_otn_metadata
from .environment import add_kadlu_env_data

# ----------------------------------------------------------------------------
# receiver/tag metadata enhancements
# - functions here are note in the metadata module, since they are customizable for the study

def rt_name(grdf, metadata, dist_str=None):
    """ Construct a name for given receiver/tag combination

    Args:
        grdf: dataframe with 'Transmitter', 'Tag Family', and 'Power' columns
        metadata: bunch dict with 'transmitter'
        dist_str (optional): function handle that returns a string representation when given a distance in m
    Returns:
        String that combines info, such as tag/receiver names, power-level, and distance
    """
    try:
        metainf = metadata.transmitter.loc[grdf.iloc[0]["Transmitter"], ['Tag Family','Power']]
        metainf = "/" + "-".join(metainf.values)
        if dist_str:
            metainf += "-" + dist_str(rt_dist(grdf, metadata))
    except:
        metainf = ''
    # look at first row of grouped dataframe
    rt = grdf.iloc[0][["Receiver","Transmitter"]]
    rt["Transmitter"] = "tag-%d" % get_device_id(rt["Transmitter"])
    dscr = "/".join(rt) + metainf
    return dscr

def dist_str_th(dist, dist_th):
    """Determine 'F'ar, 'N'ear, or 'U'nknown string for distances above or below dist_th

    Args:
        dist (float): distance in meters
        dist_th (float): distance threshold

    Returns:
        Short string or single char that classifies distance
    """
    if np.isnan(dist):
        return "U"
    elif dist > dist_th:
        return "F"
    else:
        return "N"


# ----------------------------------------------------------------------------
def calc_station_dists_m(deploy_lat_lon):
    """
    Calculate geodesic distances between stations.

    :param deploy_lat_lon: DataFrame with station latitude and longitude columns (in that order).
    :type deploy_lat_lon: pandas.DataFrame

    :return: A dataframe containing the distance (in meters) between each pair of stations.
    :rtype: pandas.DataFrame

    """

    station_dists_m = pd.DataFrame(None, columns=deploy_lat_lon.index, index=deploy_lat_lon.index)
    # uses geodesic distance calculation from geo_utils module
    for stationA in deploy_lat_lon.index:
        station_dists_m.loc[stationA, stationA] = 0
        next_station = get_next_index(deploy_lat_lon, stationA)
        for stationB in deploy_lat_lon.loc[next_station:, :].index:
            dABm = dist_m(deploy_lat_lon.loc[stationA, :].values,
                          deploy_lat_lon.loc[stationB, :].values)
            station_dists_m.loc[stationA, stationB] = dABm
            station_dists_m.loc[stationB, stationA] = dABm
    return station_dists_m

def estimate_det_max(drs):
    """Estimate maximum detection rate over majority of time
       ignoring higher detection rate during init sequence
    
       Use this in case the true tag interval length programming is unknown.
    """
    drcdf = drs.sort_values().reset_index(drop=True)
    # slope of cdf of detection counts or rates
    drdd = pd.Series(drcdf.diff()).sort_values().reset_index(drop=True)
    # determine an often occurring value of drdd, high values are well above median
    low_val = drdd[drdd > 1e-8].reset_index(drop=True).median()
    # determine where dr cdf starts to increase rapidly
    # indicating that these values are from a different distribution
    # (not due to detection fluctuations), but for instance, because the rate
    # programming is different for a short period of time
    large_vals = drdd[drdd>3*low_val]
    if not large_vals.empty:
        drmax = drcdf.iloc[get_next_index(drcdf, large_vals.index[0], True, -1)]
        # use dr at this transition point as dr estimate
        return drmax

def dr_estimate_and_cutoff(drs):
    """Estimate unknown detection rate and determine init sequence cutoff point
    Args:
        drs - detection rate sequence over fixed time intervals
    Returns:
        dr_max     - maximum detection rate for majority of time
        cutoff     - date of first valid detection bin
        cutoff_loc - raw index of first valid detection bin
    """
    dr_max = estimate_det_max(drs)
    if dr_max is None:
        cutoff_loc = 0
        dr_max = drs.max()
    else:
        cutoff = drs[drs>dr_max*1.05].index[-1]
        cutoff_loc = min(drs.index.get_loc(cutoff)+1, len(drs)-1)
    return dr_max, drs.index[cutoff_loc], cutoff_loc

# ----------------------------------------------------------------------------
# calculate interval length between detections; move init sequence to separate df
def process_intervals(detection_df, metadata):
    """
    Calculate detection interval lengths and split out init sequences

    :param detection_df: Cleaned detection data as returned by py:clean_raw_detections() or
        read_otn_data()
    :type detection_df: pd.DataFrame

    :param metadata: Metadata dictionary as returned by read_otn_data(). New member rt_groups will
        be added to metadata.
    :type metadata: dict

    :return: - **df_dets** (`pandas.DataFrame`) - DataFrame containing the detection events.
             - **df_inits** (`pandas.DataFrame`) - DataFrame containing the detections from the
               short-interval initial sequence
             - **rt_groups** (`pandas.DataFrame`) - DataFrame containing the summary of
               receiver/transmitter groups
    """


    df_dets = []
    df_inits = []
    metadata.rt_groups = (
        dataframe_schema(['Receiver', 'Transmitter', 'tstart', 'tend'],
                            ['str', 'str', 'datetime64[ns]', 'datetime64[ns]'])
        .set_index(['Receiver','Transmitter']))

    for gn, tdf in detection_df.groupby(['Receiver','Transmitter']):
        #print(" / ".join(gn))
        min_delay = metadata.transmitter.loc[gn[1], 'Transmitter.Min delay'] * 0.9
        tdf['interval'] = calc_intervals(tdf.set_index("datetime")).values
        if len(tdf) <= 1:
            continue
        interval_col = tdf.columns.get_loc('interval')
        tdf.iloc[-1, interval_col] = tdf.iloc[-2, interval_col]
        # ignore time range with short signal intervals at beginning
        init_split = tdf[tdf.interval < min_delay].index.max()
        if np.isnan(init_split):
            init_split = tdf.index[0]
        else:
            init_split = get_next_index(tdf, init_split)

        cutoff_t = tdf.loc[init_split, "datetime"]
        tdf_init = tdf[tdf.datetime<cutoff_t]
        tdf = tdf[tdf.datetime>=cutoff_t]
        if not tdf.empty:
            df_dets.append(tdf)
            df_inits.append(tdf_init)
            metadata.rt_groups.loc[gn, :] = [cutoff_t, tdf.iloc[-1, :]['datetime']]
        else:
            print("Removing group {} - no valid detections".format(" - ".join(gn)))
    df_dets = pd.concat(df_dets)
    df_inits = pd.concat(df_inits)
    return df_dets, df_inits, metadata.rt_groups


def detection_rate_grid(detection_df, time_bin_length, metadata, auto_dr=False):
    """
    Group detections into timestamp bins and analyze the detections on a group-level. Append
    aggregated bin data to the end of the detections DF.

    :param detection_df: Dataframe containing the detection events
    :type detection_df: pandas.DataFrame

    :param time_bin_length: A string that can be coerced/converted into a pandas.Timedelta object
        (e.g. "60Min", "1day")
    :type time_bin_length: str

    :param metadata: Metadata associated with the detection events
    :type metadata: sklearn.utils.Bunch

    :param auto_dr: Automatically estimate tag rate programming
    :type auto_dr: bool

    :return: - **detection_df** (`pandas.DataFrame`) - DataFrame containing the detection events,
               grouped into timestamp bins. New columns have been added that include the detection
               rate and counts for that bin. New rows have been added, containingaggregated data for
               the timestamp bins.
             - **event_bin_split** (`int`) - The row number of the first new row.

    """
    time_bin_length = pd.Timedelta(time_bin_length)
    df_drs = []
    df_detg = []
    tgrouper = detection_df.set_index('datetime').groupby(pd.Grouper(freq=time_bin_length))
    for tg, tgroup in tgrouper:
        # detection count in time window
        df_tdr = tgroup.groupby(['Receiver', 'Transmitter']).size()
        rt_detected = df_tdr.index
        # determine which transmitters are still between their first and last detection
        active_rt = metadata.rt_groups[(metadata.rt_groups['tstart'] <= tg+time_bin_length) & 
                                  (metadata.rt_groups['tend'] >= tg)]
        # append zero counts for missing detections
        missing_rt = pd.Series(0, index=active_rt.index.difference(rt_detected.values))
        df_tdr = df_tdr.append(missing_rt)
        df_tdr = pd.DataFrame(df_tdr, columns=['detection_count'])
        df_tdr['interval'] = time_bin_length.seconds / df_tdr.loc[rt_detected, 'detection_count']
        df_tdr['datetimeb'] = tg
        df_tdr = df_tdr.set_index(['datetimeb'], append=True)
        
        df_drs.append(df_tdr)
        # individual detection events within this time window
        tgroup = tgroup.reset_index()
        tgroup['datetimeb'] = tg
        df_detg.append(tgroup)
    df_drs = pd.concat(df_drs)
    df_detg = pd.concat(df_detg)

    #if 'Receiver.ID' not in df_drs:
    drs_idx = index_columns(df_drs)
    df_drs = (
        clean_raw_detections(df_drs.reset_index(),
            dates=False, rt_ids=True, select_cols=False)
        .merge(metadata.receiver).merge(metadata.transmitter))
    df_drs.set_index(drs_idx, inplace=True)

    df_drs['detection_rate'] = df_drs['detection_count'] * (df_drs['Transmitter.Avg delay'] / time_bin_length.seconds)
    #df_drs['interval'] = df_drs['Transmitter.Avg delay'] / df_drs['detection_rate']

    if auto_dr:
        drs = []
        dfield = 'detection_rate' # 'detection_count'
        for _, df_tdr in df_drs.groupby(['Transmitter', 'Receiver']):
            d_max, cutoff, cutoff_loc = dr_estimate_and_cutoff(df_tdr[dfield])
            #print(d_max, cutoff, cutoff_loc)
            df_tdr = df_tdr.iloc[cutoff_loc:].copy()
            # TODO: the following brute force correction is not needed in most cases
            d_max = df_tdr[dfield].max()
            df_tdr['detection_rate'] = df_tdr[dfield] / d_max
            drs.append(df_tdr)
        df_drs = pd.concat(drs)

    #if 'detection_rate' not in df_detg: # always True
    df_detg = df_detg.merge(df_drs[['detection_rate']], 
                            left_on=['Receiver','Transmitter','datetimeb'],
                            right_index=True)
    #if 'datetime' not in df_drs:
    df_drs['datetime'] = df_drs.index.get_level_values('datetimeb')

    detection_df = pd.concat((df_detg,
                             df_drs.reset_index())).reset_index(drop=True)
    event_bin_split = df_detg.shape[0]
    #same as: event_bin_split = detection_df.index[detection_df['interval'].isna()][0]
    return detection_df, event_bin_split

# ----------------------------------------------------------------------------
# detection interval calculation

sec1 = pd.Timedelta("1s")

def calc_intervals(grdf, field="datetime"):
    """Calculate time intervals between adjacent detection events"""
    return -grdf.reset_index()[field].diff(-1) / sec1

# ----------------------------------------------------------------------------
# derived metadata

def group_info(grdf=None, metadata=None):
    """Information about a Receiver/Transmitter group

    Args:
        grdf - DataFrame with detections and 'interval' column or None
        metadata - metadata dict as returned by read_otn_metadata

    Returns:
        info tuple about r/t group OR
        tuple element names, if grdf is None    
    """
    if grdf is None:
        return "count", "min_interval", "max_interval", "Receiver/Transmitter", "dist_m"
    assert metadata is not None, "Please provide metadata argument"
    ivs = grdf['interval']
    return len(grdf), ivs.min(), ivs.max(), rt_name(grdf, metadata), rt_dist(grdf, metadata)

def get_all_group_info(detections_df, metadata):
    """Create a dataframe with group_info() for each group in detections_df"""
    rt_groupby = detections_df.groupby(["Receiver","Transmitter"])
    groups = [rt_groupby.get_group(x) for x in rt_groupby.groups]
    return pd.DataFrame((group_info(grdf, metadata) for grdf in groups),
                        columns=[*group_info()], index=rt_groupby.groups)


def add_rt_group_info(events_df, metadata):
    """Calls get_all_group_info() for `events_df` and merges the info into `metadata`.rt_groups"""
    gsdf = get_all_group_info(events_df, metadata)
    gsdf.index.names = index_columns(metadata.rt_groups)
    gsdf = metadata.rt_groups.join(gsdf).join(metadata.transmitter)

    d_min, d_max = gsdf['dist_m'].max(), gsdf['dist_m'].min()
    dist_th = np.mean((d_min, d_max))
    def dist_str(dist):
        return dist_str_th(dist, dist_th)
    gsdf['Receiver/Transmitter'] = (gsdf['Receiver/Transmitter'] 
        + "-" + gsdf['dist_m'].apply(dist_str)
        + "-" + gsdf['Transmitter.Power'])

    metadata.rt_groups = gsdf

# ----------------------------------------------------------------------------
# detection cleanup, processing, and rate calculation

def old_make_detection_rate(tdfok, exp_interval_s=300, num_time_bins=200):
    """calculate detection rate"""
    # shift time stamps to start at 0 for first measurement iloc[0]
    time_stamps = (tdfok.datetime - tdfok.datetime.iloc[0]) / sec1
    dtcnt, bins_dt = np.histogram(time_stamps, bins=num_time_bins)
    expcount = np.ceil((bins_dt[1]-bins_dt[0]) / exp_interval_s) # expected count per bin if no ping is lost
    bins_rt = bins_dt[:-1] * sec1 + np.datetime64(tdfok.datetime.iloc[0]) # shift bin timestamps back to actual time
    det_rate = pd.Series(data=dtcnt/expcount,  # detected count normalized by expected count (may be > 1)
                         index=bins_rt,
                         name="detection_rate")
    return det_rate

def old_resample_detection_rate(tdfok, det_rate):
    """Add detection rate to full dataframe"""
    tdfok = pd.concat([tdfok.set_index("datetime"), det_rate], axis=1).interpolate(type="pad")
    tdfok.index.name = "datetime"
    return tdfok.reset_index()

# ----------------------------------------------------------------------------
# custom column creation

def unpack_column_name(column_name):
    """ Returns unpacked tuple of 1. column name in DF and 2. full column name for reporting.
        If `column_name` is a tuple, then just upack. Otherwise, use `column_name` string for both
        dataframe column id and print name.
    """
    if isinstance(column_name, tuple):
        return column_name
    else:
        assert isinstance(column_name, basestring)
        return column_name, column_name

def make_column(tdf, column_name):
    """ Modify DataFrame `tdf` to add variable with name `column`
        `tdf` remains unchanged if column is already available.
    """
    column, colname = unpack_column_name(column_name)
    if column == 'water_vel':
        tdf['water_vel'] = (tdf.water_u**2+tdf.water_v**2).apply(np.sqrt)
    elif column == 'water_vel_bottom':
        tdf["water_vel_bottom"] = (tdf.water_u_bottom**2+tdf.water_v_bottom**2).apply(np.sqrt)
    else:
        assert column in tdf.columns, "Requested a column that is not available in the merged dataframe"
        #colnames = ['salinity_bottom', 'water_temp_bottom', 'water_u_bottom', 'water_v_bottom',
        #            'salinity', 'water_temp', 'water_u', 'water_v']


# ----------------------------------------------------------------------------
# Read & process OTN data

def read_otn_data(detections_csv,
                  otn_metadata=None,
                  vendor_tag_specs=None,
                  merge=True,
                  bunch=False):
    """ All in one function to read OTN data

    Args:
        detections_csv      - csv file name for detection data
        otn_metadata        - xls file name for OTN-style metadata
        vendor_tag_specs    - xls file name for vendor extracted metadata
        merge               - bool whether to merge metadata into detections 
        bunch               - bool whether to return metadata as Bunch dict

    Returns:
        df_detections, df_deploy_meta, transmitter  - if bunch == False, else
        df_decetions, metadata                      - where metadata is a dict with metadata
    """
    # Read & clean raw detections
    df_detections_raw = pd.read_csv(detections_csv)
    df_detections = clean_raw_detections(df_detections_raw)
    metadata = Bunch()
    metadata.receiver, metadata.transmitter, metadata.datadict = (None, ) * 3

    if otn_metadata:
        # Read deployment information for receivers
        metadata.datadict, metadata.deploy = read_otn_metadata(otn_metadata)
        deploy_cols = ['DEPLOY_LAT', 'DEPLOY_LONG', 'BOTTOM_DEPTH', 'INSTRUMENT_DEPTH', 'INS_SERIAL_NO']
        metadata.receiver = metadata.deploy[deploy_cols]
        metadata.receiver.columns = ['Receiver.lat', 'Receiver.lon', 'Receiver.bottom_depth',
                                'Receiver.depth', 'Receiver.ID']
        if merge:
            # Merge Metadata & Detection Data
            df_detections = df_detections.merge(metadata.receiver)

    if vendor_tag_specs:
        metadata.transmitter = pd.read_excel(vendor_tag_specs)
        metadata.transmitter = clean_vendor_tag_specs(metadata.transmitter)
        metadata.transmitter['Transmitter.Avg delay'] = (metadata.transmitter['Transmitter.Min delay'] + metadata.transmitter['Transmitter.Max delay'])/2
        if merge:
            df_detections = df_detections.merge(metadata.transmitter)
        metadata.transmitter.set_index('Transmitter', inplace=True)
        if otn_metadata:
            ## Merge tag ID Code with INS_SERIAL_NO
            iname = metadata.transmitter.index.name
            if iname == None:
                iname = 'index'
            metadata.tag_specs = (
                metadata.transmitter.reset_index()
                .merge(metadata.deploy, 'left', left_on='Transmitter.ID', right_on='INS_SERIAL_NO')
                .set_index(iname))

    if bunch:
        return df_detections, metadata
    else:
        return df_detections, metadata.receiver, metadata.transmitter

def clean_raw_detections(df_detections_raw, dates=True, rt_ids=True, select_cols=True):
    # Deal with Dates
    if dates:
        detection_datetimes = pd.to_datetime(df_detections_raw['Date and Time (UTC)'])
        #df_detections_raw['Date'] = detection_datetimes.dt.strftime('%Y-%m-%d')
        #df_detections_raw['Time'] = detection_datetimes.dt.strftime('%I:%M:%S %p')
        #df_detections_raw['Date and Time'] = df_detections_raw['Date and Time (UTC)']
        df_detections_raw['datetime'] = detection_datetimes

    # Receiver & Transmitter IDs
    if rt_ids:
        df_detections_raw['Receiver.ID'] = get_device_id(df_detections_raw['Receiver'])
        df_detections_raw['Transmitter.ID'] = get_device_id(df_detections_raw['Transmitter'])

    # Reorganize Columns
    if select_cols:
        #cols = ['Date', 'Time', 'Date and Time', 'datetime', 'Receiver', 'Transmitter', 'Receiver_ID', 'Transmitter_ID']
        cols = ['datetime', 'Receiver', 'Transmitter', 'Receiver.ID', 'Transmitter.ID']
        return df_detections_raw[cols]
    else:
        return df_detections_raw


def read_nsog_data(detections_csv,
                   vendor_tag_specs=None,
                   merge=False,
                   bunch=False):
    """ All in one function to read NSOG data

    Args:
        detections_csv      - csv file name for detection data
        otn_metadata        - xls file name for OTN-style metadata
        vendor_tag_specs    - xls file name for vendor extracted metadata
        merge               - bool whether to merge metadata into detections
        bunch               - bool whether to return metadata as Bunch dict

    Returns:
        df_detections, df_deploy_meta, transmitter  - if bunch == False, else
        df_detections, metadata                      - where metadata is a dict with metadata
    """
    # Read & clean raw detections
    df_detections_raw = pd.read_csv(detections_csv)
    df_detections_raw = df_detections_raw[df_detections_raw['rcvrcatnumber'].str.contains("NSOG")] # Filter for the specific region
    df_detections = clean_nsog_raw_detections(df_detections_raw)
    metadata = Bunch()
    metadata.receiver, metadata.transmitter, metadata.datadict = (None, ) * 3

    # Read deployment information for receivers
    metadata.deploy = df_detections
    pd.options.mode.chained_assignment = None  # default='warn'
    metadata.deploy['STATION_NO'] = df_detections_raw['station']
    metadata.deploy['DEPLOY_LONG'] = metadata.deploy['Receiver.lon']
    metadata.deploy['DEPLOY_LAT'] = metadata.deploy['Receiver.lat']
    metadata.deploy['INS_SERIAL_NO'] = metadata.deploy['Receiver.ID']
    metadata.deploy = metadata.deploy.drop_duplicates(subset=['INS_SERIAL_NO'])
    pd.options.mode.chained_assignment = 'warn'

    receiver_cols = ['Receiver.lat', 'Receiver.lon', 'Receiver.bottom_depth',
                     'Receiver.depth', 'Receiver']
    metadata.receiver = metadata.deploy[receiver_cols]
    metadata.receiver.columns = ['Receiver.lat', 'Receiver.lon', 'Receiver.bottom_depth',
                                 'Receiver.depth', 'Receiver']
    if merge:
        # Merge Metadata & Detection Data
        df_detections = df_detections.merge(metadata.receiver)

    # Add the transmitter information
    if vendor_tag_specs:
        metadata.transmitter = pd.read_excel(vendor_tag_specs)
        metadata.transmitter = clean_vendor_tag_specs(metadata.transmitter)
        metadata.transmitter['Transmitter.Avg delay'] = (metadata.transmitter['Transmitter.Min delay'] + metadata.transmitter['Transmitter.Max delay'])/2
        if merge:
            df_detections = df_detections.merge(metadata.transmitter)
        metadata.transmitter.set_index('Transmitter', inplace=True)

        # Merge tag ID Code with
        iname = metadata.transmitter.index.name
        if iname is None:
            iname = 'index'
        metadata.tag_specs = (
            metadata.transmitter.reset_index()
            .merge(metadata.deploy, 'left', left_on='Transmitter', right_on='Transmitter')
            .set_index(iname))

    if bunch:
        return df_detections, metadata
    else:
        return df_detections, metadata.receiver, metadata.transmitter


def clean_nsog_raw_detections(df_detections_raw, dates=True, rt_ids=True, select_cols=True):
    # Deal with Dates
    if dates:
        detection_datetimes = pd.to_datetime(df_detections_raw['datecollected'])
        df_detections_raw['datetime'] = detection_datetimes

    # Receiver & Transmitter IDs
    if rt_ids:
        df_detections_raw['Receiver'] = df_detections_raw['rcvrcatnumber'] + '-' + df_detections_raw['collectornumber'].astype(str)
        df_detections_raw['Transmitter'] = get_device_from_catalog(df_detections_raw['catalognumber'])
        df_detections_raw['Receiver.ID'] = get_device_id(df_detections_raw['Receiver'])
        df_detections_raw['Transmitter.ID'] = get_device_id(df_detections_raw['Transmitter'])

    # Reorganize Columns
    if select_cols:
        # Detections
        cols = ['datetime', 'Receiver', 'Transmitter', 'Receiver.ID', 'Transmitter.ID',
                'latitude', 'longitude', 'bottom_depth', 'receiver_depth']
        col_names = ['datetime', 'Receiver', 'Transmitter', 'Receiver.ID', 'Transmitter.ID',
                     'Receiver.lat', 'Receiver.lon', 'Receiver.bottom_depth', 'Receiver.depth']
        df_clean = df_detections_raw[cols]
        df_clean.columns = col_names

        # Detections
        # det_cols = ['datetime', 'Receiver', 'Transmitter', 'Receiver.ID', 'Transmitter.ID']
        # df_detections = df_detections_raw[det_cols]
        #
        # # Deployment
        # cols = ['Receiver', 'Transmitter', 'Receiver.ID', 'Transmitter.ID',
        #         'latitude', 'longitude', 'bottom_depth', 'receiver_depth']
        # col_names = ['datetime', 'Receiver', 'Transmitter', 'Receiver.ID', 'Transmitter.ID',
        #              'Receiver.lat', 'Receiver.lon', 'Receiver.bottom_depth', 'Receiver.depth']
        # df_clean = df_detections_raw[cols]
        # df_clean.columns = col_names

        deploy_cols = ['latitude', 'longitude', 'bottom_depth', 'receiver_depth', 'Receiver']
        return df_clean

    else:
        return df_detections_raw


def process_detections(ev_df, params):
    """ Perform some computations on the detection event dataframe
    """
    # only needed by some old plot types, possibly remove this function
    t2groupby = ev_df.groupby(pd.cut(ev_df["t2"], params.t2bins))
    tdfmean = t2groupby.mean()
    tdfcount = t2groupby.count()
    tdfcount["bins"] = tdfcount.index.map(lambda i: (i.left+i.right)/2)
    params.out.update(dict(
        tdfcount = tdfcount,
        tdfmean = tdfmean,
        cutoff_t = ev_df.index[0],
        tdf = ev_df
    ))

def old_process_detections(gr, params):
    """ Add interval length to dataframe

    Returns:
        tdfok    - processed detections with detection rate
        cutoff_t - interval threshold determined to remove invalid lead pings
        tdf      - full dataframe with detection interval calculations
    """
    tdf = gr.copy(deep=False).reset_index()
    tdf["interval"] = calc_intervals(tdf.set_index("datetime"))

    # ignore date range with short signal intervals at beginning
    cutoff_t = tdf.loc[tdf[tdf.interval < 2**8].index.max()+1,
                       "datetime"]
    tdfok = tdf[tdf.datetime>cutoff_t].dropna()
    tdfok = tdfok.loc[tdfok["interval"] < 2**13]

    det_rate = old_make_detection_rate(tdfok, **params.mdr_params)
    tdfok = old_resample_detection_rate(tdfok, det_rate)

    # detection interval processing (TODO explain or remove)
    base_interval = tdfok.interval[tdfok.interval<params.base_interval_cutoff].mean() # should be 5 min = 300 sec
    tdfmean = tdfok.groupby(pd.cut(tdfok["t2"], params.t2bins)).mean()
    tdfcount = tdfok.groupby(pd.cut(tdfok["t2"], params.t2bins)).count()
    tdfcount["bins"] = tdfcount.index.map(lambda i: (i.left+i.right)/2)
    params.out.interval_all += tdfcount["t2"]
    params.out.update(dict(
        tdfok = tdfok,
        cutoff_t = cutoff_t,
        tdf = tdf,
        tdfcount = tdfcount,
        tdfmean = tdfmean
    ))
    return tdfok, cutoff_t, tdf


# ----------------------------------------------------------------------------
# invoke operations defined by config
def read_via_config(config):
    """
    Invoke configured data loading & processing.

    :param config: A Bunch dictionary containing the configuration parameters for data loading &
                   pre-processing. Created via yload() of the YAML config file.
    :type config: sklearn.utils.Bunch

    :return: - **detection_df** (`pandas.DataFrame`) - DataFrame containing the detection events.
             - **mdb** (`sklearn.utils.Bunch`) - Metadata associated with the detection events.

    """

    try:
        rdconf = config.reader
    except:
        raise YAMLProcessingError("Missing reader section in config YAML file")
    if 'otn' in rdconf.keys():
        return read_otn_data(**rdconf.otn, merge=True, bunch=True)
    elif 'nsog' in rdconf.keys():
        return read_nsog_data(**rdconf.nsog, merge=False, bunch=True)
    else:
        raise YAMLProcessingError("None of the available readers (otn, ...) found. "
                             "Instead the following readers were requested: {}".format(list(rdconf.keys())))
