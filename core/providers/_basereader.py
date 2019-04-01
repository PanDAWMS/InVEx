"""
Module with base class to provide essential methods for data reading and
formatting processes.
"""

from django.conf import settings
import os.path
from sklearn import preprocessing
from sklearn.impute import SimpleImputer
import pandas as pd
import numpy as np


class BaseReader(object):

    @staticmethod
    def to_df(data, **kwargs):
        """
        Transform data into DataFrame format.

        :param data: List of [dict]-records.
        :type data: list
        :param kwargs: Additional parameters.
        :type kwargs: dict

        :return: Data for analysis.
        :rtype: DataFrame
        """
        return pd.DataFrame(data, **kwargs)

    @staticmethod
    def normalization(data, cols_to_norm):
        """
        Normalization process.

        :param data:  Data for analysis.
        :type data: DataFrame
        :param cols_to_norm: Number of columns.
        :type cols_to_norm: int
        :return: Normalized data.
        :rtype: DataFrame
        """
        return ((data[cols_to_norm] - data[cols_to_norm].min())
                / (data[cols_to_norm].max() - data[cols_to_norm].min())) * 100.

    @staticmethod
    def scaler(df):
        """
        Scaling data.
        :param df: DataFrame
        :return:
        """
        imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
        df_imputer = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
        scaler = preprocessing.MinMaxScaler()
        scaled_df = scaler.fit_transform(df_imputer)
        scaled_df = pd.DataFrame(scaled_df, columns=df_imputer.columns).multiply(100)
        return scaled_df.set_index(df.index)

    @staticmethod
    def drop_na(data):
        """
        Drop all rows and columns that contain NA values.

        :param data: Data for analysis.
        :type data: DataFrame
        """
        # first remove all columns, where the number of NaNs
        # exceeds 80% (almost empty column)
        for column in data.columns.tolist():
            if (data[column].isna().sum() / data[column].count()) > 0.8:
                data.drop(column, 1, inplace=True)
        # then remove all rows, where all values are NaN
        data.dropna(axis=0, how='all', inplace=True)
        # and remove all rows, where any value is NaN
        data.dropna(axis=0, how='any', inplace=True)

    @staticmethod
    def get_numeric_data(data):
        return data._get_numeric_data()

    @staticmethod
    def get_numeric_columns(data):
        """
        Get the list of columns of a numeric type.

        :param data: Data for analysis.
        :type data: DataFrame
        :return: Numeric dataset
        :rtype: DataFrame
        """
        return data._get_numeric_data().columns.tolist()
