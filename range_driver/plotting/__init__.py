import numpy as np
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt
from range_driver.mpl_utils import *
from range_driver.ipython_utils import displaymd
from range_driver.data_prep import unpack_column_name
from .maps import *


# ----------------------------------------------------------------------------
# functions for acoustic tracking data
def plot_with_dr(tdfok, params, column_name, rt_name=None):
    """
    Display a plot that shows how detection rate and `column_name` (a specified column) change over
    time.
    """
    column, colname = unpack_column_name(column_name)
    tdfok.set_index("datetime")[["detection_rate", column]].plot(grid=True)
    if rt_name == None:
        rt_name = params.rt_name_dist(tdfok)
    plt.title(rt_name, fontsize=24)
    plt.xlabel(None)


def plot_tidal_phase(tdfok, ax):
    """
    Adds interval lengths to the plot showing how detection density, water_velocity, and interval
    lengths all vary with tidal phase (t2).
    """
    ax = tdfok.plot.scatter("t2", "interval", alpha=0.3, ax=ax)
    ax.set_yscale("log", base=2)
    ax.set_ylabel(None)
    ax.set_xlabel("tidal phase")
    ax.set_title("interval lengths\ndetection count\nmean water velocity", fontsize=12)


def plot_with_detection_count(tdfcount, tdfmean, params, column_name, ax):
    """
    Adds detection count & water velocity to the plot showing how detection density, water_velocity,
    and interval lengths all vary with tidal phase (t2).
    """
    column, colname = unpack_column_name(column_name)
    #tfivs = (tdfok.datetime.max()-tdfok.datetime.min())/sec1/(len(tdfok)/len(t2bins))/tdfcount["t2"].values
    tfivs = tdfcount["t2"].values
    ax.plot(tdfcount["bins"].tolist(), tfivs, c="black")
    #ax = tdfmean.plot("t2", "water_vel", alpha=1, ax=axs[0], c="darkgreen", linewidth=1)
    ax = tdfmean.plot("t2", column, alpha=1, ax=ax, c="darkgreen", linewidth=1)
    ax.legend(["detection count", colname],
              loc=0)
    ax.grid()
    ax.set_xlim(xmin=0, xmax=2)


def plot_with_detection_interval(tdfok, params, column_name, ax=None):
    column, colname = unpack_column_name(column_name)
    try:
        tdf = params.out.tdf
        ax = tdf.set_index("datetime")["interval"].plot(style=".", ax=ax, alpha=.1)
    except:
        ax = plt.axes()
    tdfok.set_index("datetime")[column].plot(ax=ax, c="darkgreen")
    try:
        ax.plot([params.out.cutoff_t]*2, [tdfok['interval'].min(), tdfok['interval'].max()], c="darkorange", linewidth=4)
    except:
        pass
    ax.set_yscale("log", base=2)
    ax.grid()
    ax.legend(['interval (blue dots)', colname])
    ax.xaxis.label.set_visible(False)


def plot_with_detection_interval_and_rate(tdfok, params, column_name, ax=None):
    column, colname = unpack_column_name(column_name)
    ax = params.out.tdf.set_index("datetime")["interval"].plot(style=".", ax=ax, alpha=.1)
    tdfok.set_index("datetime")[[column, "detection_rate"]].plot(ax=ax)
    ax.set_yscale("log", base=2)
    ax.grid()
    ax.legend(['interval (blue dots)', colname, 'detection rate'])


def plot_stack_with_dr(tdfok, params, column_name, mainax=None):
    """
    Plot detection_rate and water_velocity in two vertically stacked plots.
    These plots show how water velocity * detection rate vary according to time.
    """
    #tdfok.set_index("datetime")[["water_vel", "detection_rate"]].plot(ax=mainax, grid=True)
    column, colname = unpack_column_name(column_name)
    l,b,w,h = mainax.get_position().bounds
    mainax.axis("off")
    ax1 = plt.axes([l, b, w, h*.45])
    ax2 = plt.axes([l, b + h/2, w, h*.45])
    ax = tdfok.set_index("datetime")[column].plot(ax=ax1, color="darkorange", grid=True)
    ax.xaxis.label.set_visible(False)
    ax.legend(loc=2)
    ax.set_ylim(ymin=0)
    ax = tdfok.set_index("datetime")["detection_rate"].plot(ax=ax2, color="gray", grid=True)
    plt.tick_params("x", labelbottom=False, bottom="off")
    ax.xaxis.label.set_visible(False)
    ax.legend(loc=2)
    ax.set_ylim(ymin=0)


def plot_per_detection_rate(bins_df, params, column_name, ax=None):
    """
    Create a scatter plot showing the chosen column_name on the X-axis (e.g. water velocity) and
    detection rate on the Y-axis.
    """
    if ax is None:
        ax = plt.gca()
    column, colname = unpack_column_name(column_name)
    ax.scatter(bins_df[column], bins_df['detection_rate'],
                alpha=params.scatter_alpha)
    ax.set_xlabel(colname)
    ax.set_ylabel('detection rate')
    ax.grid(True)


def plot_per_detection_density(tdfok, params, column_name, ax=None):
    column, colname = unpack_column_name(column_name)
    # calculate detection density per water_vel density
    #division = np.arange(0, 0.25001, 0.25/100)
    v_min = tdfok[column].min()
    v_max = tdfok[column].max()
    division = np.arange(v_min, v_max+1e-5, (v_max-v_min)/100)
    counts, _ = np.histogram(tdfok[column], bins=division)
    vel_grid = pd.date_range(tdfok["datetime"].min(), tdfok.datetime.max(), freq="1h")
    count_denom, _ = np.histogram(tdfok.set_index("datetime").reindex(vel_grid, method="nearest")[column], bins=division)
    nzi = count_denom != 0
    counts_norm = counts
    counts_norm[nzi] = counts[nzi] / (count_denom[nzi] / sum(count_denom))
    counts_norm = counts_norm / sum(counts_norm)
    # print(counts)

    # plotting
    #tdfok["water_vel"].hist(bins=division)
    #plt.bar(x=division[1:], height=counts, width=0.25/100)    #text=ax.text(0,0, "", va="bottom", ha="left")
    ax.scatter(x=division[1:][nzi], y=counts_norm[nzi])    #text=ax.text(0,0, "", va="bottom", ha="left")
    plt.ylim(ymin=0)
    ax.grid()
    ax.set_xlabel(colname)
    ax.set_ylabel("detection rate")
    ax.set_title(params.rt_name_dist(tdfok), fontsize=12)


def plot_group_dr(gn, tgroup, mdb, with_details=True, figsize=(15,1)):
    """
    Displays a line graph showing detection rates for a particular receiver/transmitter pair over
    time. Also shows the metadata associated with the receiver/transmitter pair.
    """
    timefield = 'datetimeb'
    ratefield = 'detection_rate'
    #title = ' '.join(gn)
    if with_details:
        displaymd("### {}".format(mdb.rt_groups.loc[gn, "Receiver/Transmitter"]))
        display(pd.DataFrame(mdb.rt_groups.loc[gn, :]).T)
    #display(mdb.transmitter.loc[gn[1]])
    plt.figure(figsize=figsize)
    # size() - show number of events per group
    #display(tgroup)
    tgroup[ratefield] = tgroup[ratefield].astype(float)
    g = sns.lineplot(x=timefield, y=ratefield, data=tgroup)
    g.set(xlim=(mdb.rt_groups['tstart'].min(), mdb.rt_groups['tend'].max()))
    #plt.title(title)
    plt.xlabel(None)
