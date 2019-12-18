"""
Module with class to work with local data sources.
"""

import json
import os

import pandas as pd

from ._basereader import BaseReader


class LocalReader(BaseReader):

    SOURCE_FILE_FORMATS = ['csv', 'json']

    def read_df(self, file_path, file_format=None, **kwargs):
        """
        Read data of DataFrame format from the corresponding file.

        :param file_path: Full file path.
        :type file_path: str
        :param file_format: File format (e.g., csv, json).
        :type file_format: str/None
        :param kwargs: Additional parameters.
        :type kwargs: dict

        :keyword index_col: 0 (1st column is used as index), None (no indices).
        :keyword header: 0 (1st row is used as names), None (no column names).

        :keyword orient: Indication of expected JSON string format.

        :return: Data for analysis.
        :rtype: DataFrame
        """
        if not os.path.isfile(file_path):
            raise Exception('Provided file does not exist.')

        try:
            file_format = file_format or file_path.rsplit('.', 1)[1]
        except IndexError:
            raise Exception('File format is unknown.') from None
        else:
            if file_format not in self.SOURCE_FILE_FORMATS:
                raise Exception('File format is incorrect.')

        data = None

        if file_format == 'csv':
            data = pd.read_csv(file_path, **kwargs)

        elif file_format == 'json':
            if kwargs.get('orient'):
                # used if the original DatFrame was saved with "df.to_json"
                try:
                    data = pd.read_json(file_path, orient=kwargs.get('orient'))
                except:
                    pass

            if data is None:
                # used if json-file contains list of dict-records
                try:
                    with open(file_path) as fd:
                        data = json.load(fd)
                        if 'jobs' in data:
                            data = data['jobs']
                        data = self.to_df(data=data, **kwargs)
                except:
                    pass

        if data is None:
            data = pd.DataFrame()

        # check the consistency of data
        # self._check_data_format(data=data)

        # post processing
        # self._post_process(data=data)

        return data

    def _check_data_format(self, data):
        # TODO: check the consistency of the provided data.
        raise NotImplementedError

    def _post_process(self, data):
        """
        Post processing.

        :param data: Data for analysis.
        :type data: DataFrame
        :return: Processed data.
        :rtype: DataFrame
        """
        self.drop_na(data)
        return data
