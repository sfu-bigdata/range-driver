from matplotlib.pyplot import rcParams


def mpl_set_notebook_params():
    """
    Initializes sensible MatPlotLib parameters for viewing plots in the Jupyter notebook interface.

    :return: None. Makes preset changes to MatPlotLib's runtime configuration parameters.

    """
    rcParams['figure.figsize'] = 16, 8
    rcParams['font.size'] = 14
    rcParams["legend.framealpha"] = 0.6
    rcParams['figure.dpi'] = 300
