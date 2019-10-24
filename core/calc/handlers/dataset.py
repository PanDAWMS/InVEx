"""
Class DatasetHandler provides methods to store, examine and transform
the original dataset, and to process it according to the required view.
"""

import json
import logging
import os

import pandas as pd

from ...providers import LocalReader

from .. import data_converters
from ..basicstatistics import BasicStatistics
from ..lod_generator import LoDGenerator
from ..operationshistory import OperationHistory

from ._base import BaseDataHandler
from .groupeddata import GroupedDataHandler

FILE_EXTENSION_DEFAULT = 'csv'
HISTORY_FILE_EXTENSION = 'history'

local_reader = LocalReader()
logger = logging.getLogger(__name__)


class DatasetHandler(BaseDataHandler):

    def __init__(self, did, group_ids=None, use_normalized_dataset=False, **kwargs):
        """
        Initialization.

        :param did: Dataset sample id.
        :type did: int/str
        :param group_ids: Group ids (if dataset groups were created).
        :type group_ids: list/None

        :keyword dataset: Initial dataset sample.
        :keyword features: Selected features (for further analysis).
        :keyword lod_data: Level-of-Detail Generator descriptive data.
        :keyword load_initial_dataset: Flag to load initial dataset only.
        :keyword process_initial_dataset: Flag to process initial dataset.
        :keyword load_history_data: Flag to load history data.
        """
        super().__init__(did=did)

        self._group_ids = group_ids  # possible values: None, empty list, list
        self._origin = None
        self._modifications = {}
        self._property_set = {}
        self._use_normalized_dataset = use_normalized_dataset

        if (isinstance(kwargs.get('dataset'), pd.DataFrame) and \
                not kwargs['dataset'].empty):
            self._origin = kwargs['dataset']

        elif (kwargs.get('load_initial_dataset', False) or \
                kwargs.get('process_initial_dataset', False)):

            features = kwargs.get('features') or []
            lod_data = kwargs.get('lod_data') or {}
            all_checked_features = list(dict.fromkeys(
                features + (lod_data.get('features') or [])))

            options = {}
            if all_checked_features:
                options['usecols'] = all_checked_features
            dataset = self._get_initial_dataset(**options)

            if kwargs.get('process_initial_dataset', False):
                self._property_set = {
                    'features': features or dataset.columns.tolist(),
                    'lod': lod_data,  # if set then will be extended with groups
                    'op_history': None}

                self._form_dataset_modifications(dataset=dataset)
            else:
                self._origin = dataset

        elif kwargs.get('load_history_data', False):
            self._load_history_data()

    def _get_full_file_name(self, is_history_file=False):
        """
        Form full file name with initial dataset or with history information.

        :param is_history_file: Flag to get file name with history data.
        :type is_history_file: bool
        :return: Full file name.
        :rtype: str
        """
        if is_history_file:
            group_ids = self._group_ids or []
            file_name = '{}{}.{}'.format(
                self._did,
                ''.join(['.group{}'.format(i) for i in group_ids]),
                HISTORY_FILE_EXTENSION)
        else:
            file_name = '{}.{}'.format(
                self._did,
                FILE_EXTENSION_DEFAULT)

        return os.path.join(self._get_full_dir_name(), file_name)

    def _get_initial_dataset(self, **kwargs):
        """
        Get initial dataset sample (load from the storage file).

        :keyword usecols: Requested features from the initial dataset.

        :return: Initial or grouped dataset sample.
        :rtype: pandas.DataFrame/None
        """
        if self._group_ids is None:
            full_file_name = self._get_full_file_name(is_history_file=False)
            if kwargs.get('usecols'):
                kwargs['usecols'].insert(0, local_reader.read_df(
                    file_path=full_file_name,
                    file_format='csv',
                    **{'nrows': 1}).columns.tolist()[0])
            output = local_reader.read_df(file_path=full_file_name,
                                          file_format='csv',
                                          **{'index_col': 0,
                                             'header': 0,
                                             'usecols': kwargs.get('usecols')})
        elif self._group_ids:
            output = GroupedDataHandler(did=self._did,
                                        group_ids=self._group_ids[:-1]).\
                get_group(group_id=int(self._group_ids[-1]))
        else:
            output = None
            logger.error('[DatasetHandler._get_initial_dataset] '
                         'Group ids are not set - did: {}, group_ids: {}'.
                         format(self._did, self._group_ids))
        return output

    @property
    def _normalized(self):
        return self._modifications.get('normalized')

    @property
    def _auxiliary(self):
        return self._modifications.get('auxiliary')

    @property
    def clustering_dataset(self):
        if not self._modifications:
            logger.error('[DatasetHandler.clustering_dataset] '
                         'Dataset for clustering is not prepared')
            raise

        _dataset = self._normalized if self._use_normalized_dataset else self._origin

        if (self._mode == 'numeric'):
            _set = set(_dataset.columns.tolist())
            _features = [x for x in self._property_set['features'] if x in _set]
            # TODO: Re-check that feature selection is needed here
            #  (it was processed at _form_dataset_modifications for _origin dataset)
            #  (Note: for LoD _origin dataset it might behave differently)
            return _dataset.loc[:, _features]
        elif (self._mode == 'all'):
            return pd.concat([_dataset, self._auxiliary], axis=1, sort=True)

    @property
    def operation_history(self):
        return self._property_set.get('op_history')

    @operation_history.setter
    def operation_history(self, value):
        self._property_set['op_history'] = value

    def _form_dataset_modifications(self, dataset):
        """
        Process initial dataset sample and form corresponding modifications.

        :param dataset: Initial dataset sample.
        :type dataset: pandas.DataFrame
        """
        local_reader.drop_na(dataset)

        if self._property_set.get('lod'):
            lod = LoDGenerator(dataset=dataset,
                               mode=self._property_set['lod']['mode'],
                               num_groups=self._property_set['lod']['value'],
                               features=self._property_set['lod']['features'])

            self._origin = local_reader.get_numeric_data(lod.grouped_dataset)
            self._modifications['auxiliary'] = lod.grouped_dataset.drop(
                self._origin.columns.tolist(), 1)
            self._property_set['lod']['groups'] = lod.get_groups_metadata()

            GroupedDataHandler(did=self._did, group_ids=self._group_ids).\
                set_groups(
                    dataset=dataset.loc[:, self._property_set['features']],
                    groups_metadata=self._property_set['lod']['groups'],
                    save_to_file=True)
        else:
            self._origin = local_reader.get_numeric_data(dataset)
            _set = set(self._origin.columns.tolist())
            _features = [x for x in self._property_set['features'] if x in _set]
            self._origin = self._origin.loc[:, _features]
            self._modifications['auxiliary'] = dataset.drop(
                self._origin.columns.tolist(), 1)

        self._modifications['normalized'] = local_reader.scaler(self._origin)

        basic_statistics = BasicStatistics()
        basic_statistics.process_data(self._normalized)
        operation_history = OperationHistory()
        operation_history.append(self._normalized, basic_statistics)
        self.operation_history = operation_history

    def _save_history_data(self):
        """
        Save modifications of the in initial dataset and corresponding data.

        1st line - origin (numeric) dataset
        2nd line - normalized dataset
        3rd line - auxiliary data (not numeric values)
        4th line - selected features
        5th line - Level-of-Detail Generator metadata
        6th line - operations history (list of clustering operations)
        """
        file_name = self._get_full_file_name(is_history_file=True)
        self._remove_file(file_name=file_name)

        try:
            with open(file_name, 'w') as f:
                f.write('{}\n'.format(self._origin.to_json(orient='table')))
                f.write('{}\n'.format(self._normalized.to_json(orient='table')))
                f.write('{}\n'.format(self._auxiliary.to_json(orient='table')))

                f.write('{}\n'.format(
                    json.dumps(self._property_set['features'])))
                f.write('{}\n'.format(json.dumps(self._property_set['lod'])))

                f.write('{}'.format(self.operation_history.save_to_json()))
        except Exception as e:
            logger.error('[DatasetHandler._save_history_data] '
                         'Failed to save data ({}): {}'.format(file_name, e))
            raise

    def _load_history_data(self):
        """
        Load dataset modifications and corresponding data from history file.

        1st line - origin (numeric) dataset
        2nd line - normalized dataset
        3rd line - auxiliary data (not numeric values)
        4th line - selected features
        5th line - Level-of-Detail Generator metadata
        6th line - operations history (list of clustering operations)
        """
        err_msg_subj = '[DatasetHandler._load_history_data]'

        file_name = self._get_full_file_name(is_history_file=True)
        if not os.path.isfile(file_name):
            logger.error('{} Failed to find the file ({})'
                         .format(err_msg_subj, file_name))

        try:
            with open(file_name, 'r') as f:
                self._origin = data_converters.table_to_df(f.readline())
                self._modifications.update({
                    'normalized': data_converters.table_to_df(f.readline()),
                    'auxiliary': data_converters.table_to_df(f.readline())})

                self._property_set.update({
                    'features': json.loads(f.readline()),
                    'lod': json.loads(f.readline())})

                operation_history = OperationHistory()
                operation_history.load_from_json(f.readline())
                self._property_set['op_history'] = operation_history
        except Exception as e:
            logger.error('{} Failed to load data ({}): {}'.
                         format(err_msg_subj, file_name, e))
            raise

    def save(self):
        """
        Public method to save changes into the history file.
        """
        if (self._origin is not None and \
                self._modifications and self._property_set):
            self._save_history_data()
