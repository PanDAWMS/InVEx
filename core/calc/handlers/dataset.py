"""
Class DatasetHandler provides methods to store, examine and transform
the original dataset, and to process it according to the required view.
"""

import errno
import json
import logging
import os

import numpy as np
import pandas as pd

from django.conf import settings

from ...providers import LocalReader

from .. import data_converters
from ..basicstatistics import BasicStatistics, DESCRIPTION as STAT_DESCRIPTION
from ..lod_generator import LoDGenerator
from ..operationshistory import OperationHistory

from .groupeddata import GroupedDataHandler

FILE_EXTENSION_DEFAULT = 'csv'
HISTORY_FILE_EXTENSION = 'history'
STAT_FILE_EXTENSION = 'stat'

LOD_MODE_DEFAULT = 'minibatch'
LOD_VALUE_DEFAULT = 50

local_reader = LocalReader()
logger = logging.getLogger(__name__)


class DatasetHandler:

    def __init__(self, did, group_ids=None, **kwargs):
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
        self._did = did
        self._group_ids = group_ids  # possible values: None, empty list, list
        self._origin = None
        self._modifications = {}
        self._property_set = {}

        if (isinstance(kwargs.get('dataset'), pd.DataFrame) and
                not kwargs['dataset'].empty):
            self._origin = kwargs['dataset']

        elif (kwargs.get('load_initial_dataset', False) or
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

    def _get_full_file_name(self, is_history_file=False, is_stat_file=False):
        """
        Form full file name with initial dataset or with history information.

        :param is_history_file: Flag to get file name with history data.
        :type is_history_file: bool
        :param is_stat_file: Flag to get file name with statistics data.
        :type is_stat_file: bool
        :return: Full file name.
        :rtype: str
        """
        dir_name = os.path.join(settings.MEDIA_ROOT, '{}'.format(self._did))

        if is_history_file:
            group_ids = self._group_ids or []
            file_name = '{}{}.{}'.format(
                self._did,
                ''.join(['.group{}'.format(i) for i in group_ids]),
                HISTORY_FILE_EXTENSION)
        elif is_stat_file:
            file_name = '{}.{}'.format(
                self._did,
                STAT_FILE_EXTENSION)
        else:
            file_name = '{}.{}'.format(
                self._did,
                FILE_EXTENSION_DEFAULT)

        return os.path.join(dir_name, file_name)

    @staticmethod
    def _remove_file(file_name):
        """
        Remove file with provided full name.

        :param file_name: Full file name.
        :type file_name: str
        """
        try:
            os.remove(file_name)
        except OSError as e:
            # errno.ENOENT - no such file or directory
            if e.errno != errno.ENOENT:
                logger.error(
                    '[DatasetHandler._remove_file] Failed to remove file '
                    '({}): {}'.format(file_name, e))
                # re-raise exception if a different error occurred
                raise

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

        _set = set(self._normalized.columns.tolist())
        _features = [x for x in self._property_set['features'] if x in _set]
        # TODO: Re-check that feature selection is needed here
        #  (it was processed at _form_dataset_modifications for _origin dataset)
        #  (Note: for LoD _origin dataset it might behave differently)
        return self._normalized.loc[:, _features]

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

    @staticmethod
    def _get_features_description(df):
        """
        Get list of features with descriptive and statistical metrics.

        :param df: Dataset for features analysis.
        :type df: pandas.DataFrame
        :return: Feature descriptions.
        :rtype: list
        """
        output = []

        for column in df:

            if not df[column].count():
                continue
            # TODO: Re-check that feature with no values should be skipped

            item = {
                'feature_name': column,
                'feature_type': df[column].dtype.name,
                'percentage_missing':
                    (np.count_nonzero(df[column].isnull()) * 100.) /
                    len(df[column]),
                'measure_type': 'unknown'}
            # TODO: Re-check the formula for percentage_missing

            is_category = float(df[column].nunique()) / df[column].count() < .1

            if item['feature_type'] in ['int64', 'float64', 'int32',
                                        'float32', 'int', 'float']:

                if is_category:
                    unique_values = df[column].dropna().unique().tolist()
                    item.update({
                        'measure_type': 'ordinal',
                        'unique_values': unique_values,
                        'unique_number': len(unique_values),
                        'distribution': {str(k): v for k, v in df[column].
                                         value_counts().to_dict().items()},
                        'enabled': 'false'})
                else:
                    item.update({
                        'measure_type': 'continuous',
                        'min': df[column].min(),
                        'max': df[column].max(),
                        'mean': df[column].mean(),
                        'std': df[column].std(),
                        'q10': df[column].quantile(.1),
                        'q25': df[column].quantile(.25),
                        'q50': df[column].quantile(.5),
                        'q75': df[column].quantile(.75),
                        'q90': df[column].quantile(.9),
                        'enabled': 'true'})

            elif item['feature_type'] == 'object':

                item.update({
                    'measure_type': 'nominal',
                    'unique_number': len(df[column].dropna().unique().tolist()),
                    'distribution': {},
                    'enabled': 'false'})

                is_datetime_object = False
                if any(n in column for n in ['time', 'date', 'start', 'end']):
                    try:
                        dt_object = pd.to_datetime(df[column].dropna())
                    except ValueError:
                        pass
                    else:
                        item.update({
                            'measure_type': 'range',
                            'unique_values': [dt_object.min().isoformat(),
                                              dt_object.max().isoformat()]})
                        is_datetime_object = True

                if not is_datetime_object:

                    unique_values = df[column].dropna().unique().tolist()
                    if is_category:
                        item.update({
                            'unique_values': unique_values,
                            'distribution': df[column].value_counts().to_dict()})
                    else:
                        item.update({
                            'measure_type': 'non-categorical',
                            'unique_values': unique_values[:10]})

            output.append(item)
        return output

    def describe(self, save_to_file=False):
        """
        Get descriptive and statistical information.

        :param save_to_file: Flag to store dataset info into the file.
        :type save_to_file: bool
        :return: Descriptive and statistical information about origin dataset.
        :rtype: dict
        """
        output = {}
        if self._origin is not None:
            dataset = self._origin.copy()
            if self._auxiliary is not None:
                dataset = dataset.join(self._auxiliary)
            dataset.dropna(axis=1, how='all', inplace=True)
            dataset.dropna(axis=0, how='all', inplace=True)
            output.update({
                'index_name': dataset.index.name,
                'num_records': len(dataset.index),
                'features': self._get_features_description(df=dataset)})

            if save_to_file:
                file_name = self._get_full_file_name(is_stat_file=True)
                self._remove_file(file_name=file_name)
                with open(file_name, 'w') as f:
                    f.write(json.dumps({
                        'index_name': output['index_name'],
                        'num_records': output['num_records'],
                        'features': json.loads(
                            pd.DataFrame.from_records(output['features']).T.
                            to_json())}))
        return output

    def get_view_data(self, with_full_set=False, save_stats=False):
        """
        Get view data for UI representation (for the client side).

        :param with_full_set: Flag to get full set of parameters.
        :type with_full_set: bool
        :param save_stats: Flag to save dataset descriptive information (stats).
        :type save_stats: bool
        :return: Key-value pairs for UI representation.
        :rtype: dict
        """
        output = {
            'data_uploaded': True,
            'dsID': self._did,
            'lod_activated': False,
            'lod_mode': LOD_MODE_DEFAULT,
            'lod_value': LOD_VALUE_DEFAULT,
            'lod_data': None}
        output.update(self.describe(save_to_file=save_stats))

        if with_full_set:

            output.update({
                'data_is_ready': False,
                'cluster_ready': False,
                'clusters': [],
                'count_of_clusters': None,
                'algorithm': None,
                'visualparameters': None,
                'parameters': {},
                'filename': False,
                'type': 'datavisualization',
                'group_vis': False})
            # TODO: Check the consistency of the view_data key-value pairs.
            # TODO: Re-work view_data parameter names.

            try:
                output.update({
                    'index': [self._origin.index.name or 'id'],
                    'real_dataset': data_converters.pandas_to_js_list(
                        self._origin),
                    'norm_dataset': data_converters.pandas_to_js_list(
                        self._normalized),
                    'aux_dataset': data_converters.pandas_to_js_list(
                        self._auxiliary),
                    'dim_names': self._normalized.columns.tolist(),
                    'aux_names': self._auxiliary.columns.tolist(),
                    'operation_history': self.operation_history})

                real_dataset_stats_or = BasicStatistics().\
                    process_data(self._origin)
                real_dataset_stats = []
                for i in range(len(real_dataset_stats_or)):
                    real_dataset_stats.append(real_dataset_stats_or[i].tolist())
                output['real_metrics'] = [STAT_DESCRIPTION, real_dataset_stats]
                # TODO: Re-work this.

                corr_matrix = self._origin.corr()
                corr_matrix.dropna(axis=0, how='all', inplace=True)
                corr_matrix.dropna(axis=1, how='all', inplace=True)
                output['corr_matrix'] = corr_matrix.values.tolist()
            except Exception as e:
                logger.error('[DatasetHandler.get_view_data] '
                             'Failed to prepare basics of the view data: {}'.
                             format(e))
                raise

            # prepare LoD information
            lod_features = []
            if self._property_set.get('lod', {}).get('value'):
                output.update({
                    'lod_activated': True,
                    'lod_mode': self._property_set['lod']['mode'],
                    'lod_value': self._property_set['lod']['value'],
                    'lod_data': self._property_set['lod'].get('groups', [])})
                lod_features.extend(self._property_set['lod']['features'])

            # prepare information about checked features
            features = self._property_set.get('features', [])
            for feature in output['features']:
                if feature['feature_name'] in features:
                    feature['enabled'] = 'true'
                else:
                    feature['enabled'] = 'false'
                if feature['feature_name'] in lod_features:
                    feature['lod_enabled'] = 'true'

        return output

    def save(self):
        """
        Public method to save changes into the history file.
        """
        if (self._origin is not None and
                self._modifications and self._property_set):
            self._save_history_data()
