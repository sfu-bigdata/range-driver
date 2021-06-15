from .ipython_utils import *
from .mpl_utils import *
from .plotting import *
from .plotting import heatmaps
from .data_prep import environment
from .data_prep import *
from .config import *


def kadlu_source_map():
    return environment.kadlu.source_map


def report_station_info(mdb):
    """
    Displays a report of station information. This report shows the metadata associated with each
    transmitter type, a summary of detections by receiver/transmitter pairs, and some documentation
    on how to interpret the report.

    :param mdb: Bunch containing the metadata associated with the detection events.
    :type mdb: sklearn.utils.Bunch

    :return: None. Displays a report of station information.
    """

    show_details = True
    if show_details:
        display(Markdown("""**Station distances** are geodesic, in meters, ignoring depth difference.  
        The distance between stations 2 and 3 does not occur in detections, since there are no receivers 
        these stations.
        """))
        mdb.station_dists_m

    if show_details:
        
        displaymd("""### Processing of other metadata (custom format extracted from vendor info)

    The first part of metadata stems from vendor CSV files, simply copying the relevant rows from different source CSVs into one table.
    This contains High and Low power mode. This information is then added to the OTN deployment metadata.""")

        
        displaymd("""### Merge tag ID Code with INS_SERIAL_NO to get metadata
    The tags that have missing info here, turn out to be unimportant later, due to insufficient detection count.
    """)
        
        display_full_df(mdb.tag_specs)

    if show_details:
        d_min, d_max = mdb.rt_groups['dist_m'].max(), mdb.rt_groups['dist_m'].min()
        displaymd("""# Summary of detections by Receiver/Transmitter pair  
        
    **R/T name format:**  
    Receiver/Transmitter/Tag Family/Power(H,L)/Distance(Near,Far)

    **Distances:**  
    near = %.2f m  
    far = %.2f m
    """ % (d_min, d_max))

        display(mdb.rt_groups.sort_values(by="Receiver/Transmitter", ascending=False))


def report_group_info(dets):
    if dets.config.settings.show_details:
        report_station_info(dets.mdb)

    if dets.config.view.show_dr_plots:
        displaymd("# Detection rate plots for data screening")
        for gn, tgroup in dets.bins_df.reset_index().groupby(['Transmitter', 'Receiver']):
            gn = tuple(reversed(gn)) # TODO check this when changing T/R groupby key order
            plot_group_dr(gn, tgroup, dets.mdb)
            plt.show()


def show_tidal_plots(dflat, df_tidal_interp,
                     tidal_times_output_csv,
                     tidal_interpolation_output_csv):
    """
    Displays a graph showing tidal height, velocity of tidal change, and tidal phase compared to
    time.
    """
    show_details = True
    if show_details:
        displaymd("""## Tidal data for Halifax
Linear interpolation
""")
        dflat["height"].plot()
        plt.ylabel("height (cm)")
        plt.xlabel(None)
        plt.grid()

    if show_details:
        df_tidal_interp.to_csv(tidal_interpolation_output_csv)
        displaymd("Wrote data to `{}`".format(tidal_interpolation_output_csv))

    #end_datetime = "2016-03-15 01:18"
    if show_details:
        with plt.rc_context({'figure.figsize': (16, 5), 'lines.linewidth': 2}):
            end_datetime = df_tidal_interp.index.max()
            displaymd("Display data until {}".format(end_datetime))
            df_tidal_interp.loc[:end_datetime].height.plot()
            df_tidal_interp.loc[:end_datetime].dheight_cm_per_hr.plot()
            (df_tidal_interp.loc[:end_datetime].t*10).plot()
            plt.title("Tidal data for Halifax with Cosine interpolation")
            plt.legend(loc=1)
            plt.grid()
        displaymd("""
The variable $t$ above indicates tidal phase within each of high-to-low and low-to-high portion. 
Its range is in $[0,1]$, but has been magnified by a factor of $10$ in the plot to show more clearly 
in comparison to the other variables.  
Below, a new variable $t2$ is introduced that ranges from $0$ to $2$, from high tide to the next high tide, 
with $1$ corresponding to low tide.""")


def show_group_plots(dets, gn, gr, params, column_name):
    """Show a collection of plots that give a summary for one receiver/transmitter group"""
    # rt_name = dets.mdb.rt_groups.loc[gn, 'Receiver/Transmitter']
    rt_name = gn
    events_df, bins_df = dets.get_events_bins(gr)
    tdfok = bins_df
    if tdfok.empty:
        displaymd("Skipping ")
        displaymd("{}".format(rt_name))
        return
    process_detections(events_df, params)
    if True:
        plot_with_dr(tdfok, params, column_name=column_name, rt_name=rt_name)
    fig, axs = plt.subplots(nrows=1, ncols=3)
    fig.suptitle(rt_name)
    plot_tidal_phase(tdfok, ax=axs[0])
    plot_with_detection_count(params.out.tdfcount, params.out.tdfmean,
                              params, column_name=column_name,
                              ax=axs[0])    # interval lengths over date range
    if False:
        # comparison in single plot
        #broken: plot_with_detection_interval(tdfok, params, column_name=column_name, ax=axs[1])
        ax = params.out.tdfmean.plot("t2","interval", alpha=1, ax=axs[1], c="darkgrey", linewidth=2)
    elif False:
        # old plot type focussing on interval lengths rather than DR
        plot_with_detection_interval_and_rate(events_df, params, column_name=column_name, ax=axs[1])
    else:
        # stacked plot for comparison of quantities
        plot_stack_with_dr(tdfok, params, column_name=column_name, mainax=axs[1])
    plot_per_detection_rate(bins_df, params, column_name=column_name, ax=axs[2])
    #plot_per_detection_density(events_df, params, column_name=column_name, ax=axs[2])
    plt.subplots_adjust(wspace=.3)


def report_all_group_plots(dets, groups=None, grouping_feature=None, column=None):
    """

    :param dets: The Detections object containing study and environmental data.
    :type dets: range_driver.detections.Detections

    :param groups: The GroupBy object containing the groups to plot. Optional, defaults to None.
    :type groups: pandas.core.groupby.generic.DataFrameGroupBy

    :param grouping_feature: The feature (column) in dets to use for grouping. Only used if groups
    is None. Optional, defaults to None.
    :type grouping_feature: str

    :param column: The column to plot for comparison to detection rate.
    :type column: str

    :return: Nothing. Plots are displayed.
    """
    rcParams.update(dets.config.view.rcParams)
    params = make_params(dets.config)

    # Find the column to plot for comparison
    _, colnames, ccolumn = get_column_info(dets.config)
    if column is None:
        column = ccolumn
    column_name = (column, colnames[column])

    # If groups aren't provided, try to use the grouping_feature to cluster the data. If that isn't
    # provided, don't group the data and instead plot all the data together.
    if groups is None:
        if grouping_feature is None:
            groups = [("All Detections", dets.df_detections_env)]
        else:
            groups = dets.df_detections_env.groupby(grouping_feature, as_index=False)

    # Plot each group
    for group_name, group_data in groups:
        if len(group_data) < params.min_detections:
            displaymd("**Skipping groups that have insufficient detections:**")
        else:
            show_group_plots(dets, group_name, group_data, params, column_name)


def report_map_view(dets):
    plot_bounds(dets.bounds, dets.receiver_locations, dets.receiver_info, dets.node_locations)


def report_heatmap(dets, groups=None, grouping_feature=None):
    """
    Generate & display a series of heat-maps showing the correlation between the quantitative
    features in Detections object's event data.

    One heat-map will be created for each group of data, specified by groups or grouping_feature. If
    neither groups or grouping_featuer are specified, a single heat-map will be created, showing the
    correlation of features across the entire dataset.

    :param dets: The Detections object containing study & environmental data.
    :type dets: range_driver.detections.Detections

    :param groups: The GroupBy object containing the groups to plot. Optional, defaults to None.
    :type groups: pandas.core.groupby.generic.DataFrameGroupBy

    :param grouping_feature: The feature (column) in dets to use for grouping. Only used if groups
    is None. Optional, defaults to None.
    :type grouping_feature: str

    :return: Nothing is returned. Plots are displayed.
    """
    default_exclude_cols = ['datetime', 'Receiver', 'Transmitter', 'Receiver.ID', 'Transmitter.ID',
                            'Receiver.lat', 'Receiver.lon', 'STATION_NO', 'DEPLOY_LONG',
                            'DEPLOY_LAT', 'INS_SERIAL_NO', 'interval', 'datetimeb',
                            'Transmitter.Tag Family', 'Transmitter.Power', 'Transmitter.Min delay',
                            'Transmitter.Max delay', 'Transmitter.Avg delay']

    if groups is None:
        if grouping_feature is None:
            groups = [("All Detections", dets.df_detections_env)]
        else:
            groups = dets.df_detections_env.groupby(grouping_feature, as_index=False)

    for name, group in groups:
        feature_cols = [c for c in group.columns if (c not in default_exclude_cols) |
                        (c == grouping_feature)]
        features = group[feature_cols]
        if grouping_feature:
            name = f"{grouping_feature} == {name}"
        if grouping_feature in features.columns:
            features = features.drop(grouping_feature, axis=1)
        heatmaps.plot_feature_heatmap(features, title=name)


def report_tidal(dets):
    if dets.config.view.tidal:
        displaymd("""# Determine tidal heights via interpolation of tidal time tables
In addition to ocean and weather model data, historic tidal tables are available and used here to provide 
additional information about environmental cycles that could be factors of influence on the acoustic data.
""")
        show_tidal_plots(dets.df_tidal_flat, dets.df_tidal_interp,
                         **select_keys(dets.config.data.tidal,
                                       ['tidal_times_output_csv', 'tidal_interpolation_output_csv']))
