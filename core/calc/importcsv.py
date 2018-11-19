import os
import pandas as pd


def import_csv_file(path_to_file, index=False, column_names=False):

    if column_names:
        column_names = 0
    else:
        column_names = None
    return pd.read_csv(path_to_file, index_col=index, header=column_names)


def normalization(df, cols_to_norm):
    return (df[cols_to_norm] - df[cols_to_norm].min()) / (df[cols_to_norm].max() - df[cols_to_norm].min()) * 100


def clean_dataset(df):
    to_drop = []
    for item in df:
        if df[item].dtypes == 'object':
            to_drop.append(item)
    df.drop(to_drop, 1, inplace=True)
    df.drop('Unnamed: 0', 1, inplace=True)


def dropNA(df):
    df.dropna(axis=1, how='any', inplace=True)
    df.dropna(axis=0, how='any', inplace=True)
