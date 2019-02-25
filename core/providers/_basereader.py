"""
Module with base class to provide essential methods for data reading and
formatting processes.
"""

import pandas as pd


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
    def drop_na(data):
        """
        Drop all rows and columns that contain NA values.

        :param data: Data for analysis.
        :type data: DataFrame
        """
        data.dropna(axis=1, how='any', inplace=True)
        data.dropna(axis=0, how='any', inplace=True)

    @staticmethod
    def get_numeric_columns(data):
        """
        Get the list of columns of a numeric type.

        :param data: Data for analysis.
        :type data: DataFrame
        :return: Numeric columns.
        :rtype: list
        """

        output = []

        for item in data:
            if data[item].dtypes in ['int64', 'float']:
                output.append(item)

        return output
