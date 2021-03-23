import pandas as pd
from bisect import bisect_left


def index_columns(df, none_name=None):
    """Return list of column names that form the (multi-)index or None, if index is a single unnamed
    column."""
    try:
        return [l.name for l in df.index.levels]
    except AttributeError:
        name = df.index.name
        if name is not None:
            return [name]
        elif none_name is not None:
            return [none_name]


def split_by_index(df, split_idx):
    """
    Split DataFrame df at or around the given index value

    :param df: DataFrame with a sorted index
    :type df: pandas.DataFrame

    :param split_idx: The index value to split df by.
    :type split_idx: int

    :return: - **low_df** (`pandas.DataFrame`) - DataFrame containing index values below split_idx
             - **high_df** (`pandas.DataFrame`) - DataFrame containing index values greater than or
               equal to split_idx.
    """
    try:
        idx = df.index.get_loc(split_idx)
    except KeyError:
        idx = bisect_left(df.index, split_idx)
    return df.iloc[:idx, :], df.iloc[idx:, :]


def update_on(df, dfu, on=None):
    """Use DataFrame.update() function inplace, matching on any set of columns."""
    if on:
        inames = index_columns(df)
        uinames = index_columns(dfu)
        df.reset_index(inplace=True)
        df.set_index(on, inplace=True)
        if uinames is not None:
            df.update(dfu.reset_index().set_index(on))
        else:
            # id dfu index is unnamed, drop it to avoid collision with df index
            df.update(dfu.set_index(on))
        if inames is None:
            df.reset_index(inplace=True)
            df.set_index('index', inplace=True)
            df.index.name = None
        else:
            df.reset_index(inplace=True)
            df.set_index('index', inplace=True)
    else:
        df.update(dfu)


def dataframe_schema(columns, dtypes):
    """Create empty pd.DataFrame with columns of given datatypes"""
    df_dict = {cname: pd.Series([], dtype=dtype) for cname, dtype in zip(columns, dtypes)}
    return pd.DataFrame(df_dict)


def remove_microsecond(ts):
    return pd.Timestamp(year=ts.year, month=ts.month, day=ts.day, hour=ts.hour, second=ts.second)


def get_next_index(df, index_val, lock_bound=False, inc=+1):
    """Determine the index value that follows `index_val`
    Args:
        df         - dataframe or series, having df.index
        index_val  - index value to start from
        lock_bound - if true return same index if reaching bounds
        inc        - increment default +1, use -1 to get previous index
    Returns:
        neighbouring index value
    """
    index_value_iloc = df.index.get_loc(index_val)
    next_iloc = index_value_iloc + inc
    try:
        next_index_value = df.index[next_iloc]
    except IndexError:
        if lock_bound:
            return index_value_iloc
        else:
            next_index_value = None

    return next_index_value
