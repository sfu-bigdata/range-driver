import pandas as pd
from IPython.display import display, Markdown

def displaymd(strmd):
    """Display Markdown in notebook"""
    display(Markdown(strmd))

def display_full_df(df, max_rows=None, max_columns=None):
    with pd.option_context('display.max_rows', max_rows,
                           'display.max_columns', max_columns,
                           'display.max_colwidth', -1):
        display(df)
