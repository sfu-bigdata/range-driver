"""
    Functions to handle different kinds of metadata, e.g. details about receiver and tag deployment, etc.

    TODO: Integrate with resonate metadata processing
"""

import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------
# OTN metadata
# TODO: replace with resonate metadata load function

sheet_skips = {'Data Dictionary': 4, 'Deployment': 0}


def read_otn_metadata(metadata_file, sheet_skips=sheet_skips):
    dfmeta_data = dict((sname,
                        pd.read_excel(metadata_file, sheet_name=sname, skiprows=skipr))
                       for sname, skipr in sheet_skips.items())

    dfmeta_datadict = dfmeta_data['Data Dictionary'].set_index('Field Name')
    dfmeta_deploy = dfmeta_data['Deployment']

    # address possibly inconsistent use of _NUMBER vs _NO, by renaming all to _NO
    dfmeta_datadict = dfmeta_datadict.set_index(dfmeta_datadict.index.str.replace('NUMBER','NO'))
    dfmeta_deploy.columns = dfmeta_deploy.columns.str.replace('NUMBER','NO')
    units_col = next(filter(lambda c: 'units' in c.lower(), dfmeta_datadict.columns))

    # remove (format) part from column names in deployment table
    col_names_split = dfmeta_deploy.columns.str.split(n=1)
    dfmeta_deploy.columns = col_names_split.str[0]
    col_formats = col_names_split.str[1]

    # add Format column to data dictionary
    ps_formats = pd.Series(col_formats, index=col_names_split.str[0])
    paren_regex = r'\((.*)\)'
    dfmeta_datadict['Format'] = ps_formats.str.extract(paren_regex)

    # remove NaN rows that do not have OTN_ARRAY specified
    dfmeta_deploy.dropna(subset=['OTN_ARRAY'], inplace=True)

    # determine columns that have format: integer ... in data dictionary
    integer_cols = (dfmeta_datadict.index[dfmeta_datadict[units_col].str.match(r".*format: (integer.*)")].tolist()
                    + ['INS_SERIAL_NO', 'AR_SERIAL_NO'])
    dfmeta_datadict.loc[integer_cols,'Format'] = 'integer'

    # perform type conversion of integer columns, use special int to fill NaNs
    NANINT = 0
    dfmeta_deploy[integer_cols] = dfmeta_deploy[integer_cols].replace({np.nan:NANINT}).astype(int)

    for col in dfmeta_datadict.index[dfmeta_datadict.index.str.match('.*DATE_TIME.*')]:
        #format_str = dfmeta_datadict.loc[col, 'Format']
        dfmeta_deploy[col.replace("DATE_TIME", "DATETIME")] = pd.to_datetime(dfmeta_deploy[col],
                                                                             infer_datetime_format=True)
    return dfmeta_datadict, dfmeta_deploy


# ----------------------------------------------------------------------------
# work on metadata extracted via row copy&paste from vendor CSV files

def clean_vendor_tag_specs(tag_specs_df):
    """Process metadata extracted via row copy & paste from vendor CSV files"""
    # columns = ['INTERVAL', 'STATUS', 'Time\ndy hr:min:sec', 'Power\n(L/H)',
    #    'Fixed Delay', 'Min \n(sec)', 'Max \n(sec)', 'Tag Family', 'Serial No.',
    #    'ID Code', 'VUE Tag ID\n(Freq-Space-ID)', 'Freq  (kHz)',
    #    'Precise \nDelay', 'Est. Tag Life \n(Days)', 'Spreadsheet']
    fields = {
        'Tag Family': 'Transmitter.Tag Family',
        'ID Code': 'Transmitter.ID',
        'VUE Tag ID\n(Freq-Space-ID)': 'Transmitter', #'VUE Tag',
        'Power\n(L/H)': 'Transmitter.Power',
        'Min \n(sec)': 'Transmitter.Min delay',
        'Max \n(sec)': 'Transmitter.Max delay'
    }
    rnfields = {key: value for (key,value) in fields.items() if value}
    tag_specs = tag_specs_df[fields.keys()].copy(deep=False)
    tag_specs.rename(columns=rnfields, inplace=True)
    return tag_specs


# ----------------------------------------------------------------------------
# receiver / transmitter ID string construction and metadata processing

def get_device_id(device_str):
    "Return last part of '-'-separated string as int. Works on str and DataFrames of strings."
    try:
        return device_str.str.split("-").str[-1].astype(int)
    except:
        return int(device_str.split("-")[-1])


def get_device_from_catalog(catalog_str):
    """Return 2nd last part of '-' separated string as an int. Works on str and DataFrames of
    strings"""
    try:
        return catalog_str.str.split("-").str[:-1].str.join("-")
    except:
        return '-'.join(catalog_str.split("-")[:-1])


def rt_info(grdf, metabunch):
    # get receiver and transmitter IDs of first detection and merge metadata
    rt_inf = pd.DataFrame(get_device_id(grdf.iloc[0,:][['Receiver','Transmitter']])).transpose()
    rt_inf = rt_inf.merge(metabunch.deploy.add_prefix('RECV_'), 'left', left_on='Receiver', right_on='RECV_INS_SERIAL_NO')
    rt_inf = rt_inf.merge(metabunch.deploy.add_prefix('TAG_'), 'left', left_on='Transmitter', right_on='TAG_INS_SERIAL_NO')
    rt_inf = rt_inf.iloc[0]
    try:
        rt_inf['RT_DISTANCE_M'] = metabunch.station_dists_m.loc[rt_inf['RECV_STATION_NO'], rt_inf['TAG_STATION_NO']]
    except:
        pass
    return rt_inf


def rt_dist(grdf, metabunch):
    rt_inf = rt_info(grdf, metabunch)
    try:
        return rt_inf['RT_DISTANCE_M']
    except:
        #print(rt_inf)
        return np.nan


def otn_transmitter_patch_1(mdb):
    """
    Applies a patch specific to the OTN Mahone Bay range test

    :param mdb: Metadata for the OTN Mahone Bay range test.
    :type mdb: sklearn.utils.Bunch

    :return: None. Applies the patch to the Transmitter information within the Metadata
    """

    fields = ['Transmitter.Min delay', 'Transmitter.Max delay', 'Transmitter.Avg delay']
    set_all_values(mdb.transmitter, fields, aggfun="max")


def set_all_values(df, columns, aggfun="max"):
    """Set all values of DataFrame `df` in given `columns` to aggregated value."""
    for field in columns:
        df[field] = df[field].agg(aggfun)

# functions for derived metadata are in .data_prep module
