import pandas as pd
from sklearn import preprocessing


def import_csv_file(path_to_file, index=False, column_names=False, use_cols=False):
    if index:
        index = 0
    else:
        index = None

    if column_names:
        column_names = 0
    else:
        column_names = None
    if use_cols is False:
        return pd.read_csv(path_to_file, index_col=index, header=column_names)
    else:
        return pd.read_csv(path_to_file, index_col=index, header=column_names, usecols=use_cols)


def scaler(df):
    scaler = preprocessing.MinMaxScaler()
    scaled_df = scaler.fit_transform(df)
    return pd.DataFrame(scaled_df, index=df.index, columns=df.columns).multiply(100)


def normalization(df, cols_to_norm):
    return (df[cols_to_norm] - df[cols_to_norm].min()) / (df[cols_to_norm].max() - df[cols_to_norm].min()) * 100


def dropNA(df):
    df.dropna(axis=0, how='any', inplace=True)


def numeric_columns(df):
    aux = []
    for item in df:
        if df[item].dtypes in ['int64', 'float64', 'int32', 'float32', 'int', 'float']:
            aux.append(item)
    return aux
