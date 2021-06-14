import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import rcParams


def set_heatmap_rcParams():
    rcParams['figure.figsize'] = 3, 1.5
    rcParams['font.size'] = 2.5

    # rcParams['ytick.left'] = True
    rcParams['ytick.major.size'] = 0
    rcParams['ytick.major.width'] = 0.3
    rcParams['ytick.major.pad'] = 0.5

    # rcParams['xtick.bottom'] = True
    rcParams['xtick.major.pad'] = 0.5
    rcParams['xtick.major.size'] = 0
    rcParams['xtick.major.width'] = 0.3

    rcParams['figure.titlesize'] = 10


def plot_feature_heatmap(feature_df, title=None, method='pearson'):
    """
    Plots and displays a heat-map showing the correlation between features of interest.

    :param feature_df: Dataframe where each column is a feature being compared.
    :type feature_df: pandas.DataFrame

    :param title: Title to use on the heatmap.
    :type title: str

    :param method: Method of correlation. As described in detail `here
        <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.corr.html>`_.
        Defaults to 'pearson'. This method will be applied to each pair of features (columns) in
        feature_df.
    :type method: str {'pearson', 'kendall', 'spearman'} or callable, optional

    :return: matplotlib figure object.

    """
    # Find the correlation matrix
    corr = feature_df.corr(method=method)

    # Create the mask for the upper triangle
    mask = np.triu(np.ones_like(corr, dtype=np.bool))

    # Set up the matplotlib figure
    set_heatmap_rcParams()
    f, ax = plt.subplots()

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(240, 10, as_cmap=True)
    sns.heatmap(corr,
                mask=mask,
                cmap=cmap,
                vmin=-1, vmax=1, center=0,
                linewidths=.1,
                cbar_kws={'ticks': [-1, 0, 1],
                          'shrink': 0.8}
                )
    ax.set_title(title)
    plt.show()

    return f
