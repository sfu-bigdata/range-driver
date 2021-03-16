import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd


def plot_feature_heatmap(feature_df, method='pearson'):
    """
    Plots and displays a heat-map showing the correlation between features of interest.

    :param feature_df: Dataframe where each column is a feature being compared.
    :type feature_df: pandas.DataFrame

    :param method: Method of correlation. As described in detail `here
        <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.corr.html>`_.
        Defaults to 'pearson'. This method will be applied to each pair of features (columns) in
        feature_df.
    :type method: str {'pearson', 'kendall', 'spearman'} or callable, optional

    :return: None. Displays the heatmap.

    """
    # Find the correlation matrix
    corr = feature_df.corr(method=method)

    # Create the mask for the upper triangle
    mask = np.triu(np.ones_like(corr, dtype=np.bool))

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(10, 10))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(240, 10, as_cmap=True)
    sns.heatmap(corr, mask=mask,
                cmap=cmap, vmax=.3, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5})

    return f