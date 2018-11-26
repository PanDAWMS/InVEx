import os
import pandas as pd


def import_csv_file(path_to_file, index=False, column_names=False):

    if index:
        index = 0
    else:
        index = None

    if column_names:
        column_names = 0
    else:
        column_names = None
    return pd.read_csv(path_to_file, index_col=index, header=column_names)


def normalization(df, cols_to_norm):
    return (df[cols_to_norm] - df[cols_to_norm].min()) / (df[cols_to_norm].max() - df[cols_to_norm].min()) * 100


def dropNA(df):
    df.dropna(axis=1, how='any', inplace=True)
    df.dropna(axis=0, how='any', inplace=True)

def numeric_columns(df):
    aux = []
    for item in df:
        if df[item].dtypes in ['int64','float'] :
            aux.append(item)
    return aux