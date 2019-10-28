"""
Class DatasetHandler provides methods to store, examine and transform
the original dataset, and to process it according to the required view.
"""

import json
import logging
import os

import h5py
import numpy as np
import pandas as pd

from datetime import datetime

from ...providers import LocalReader

from ..lod_generator import LoDGenerator

from ._base import BaseDataHandler
from .groupeddata import GroupedDataHandler
from .operation import OperationHandler

FILE_EXTENSION_DEFAULT = 'h5'

local_reader = LocalReader()
logger = logging.getLogger(__name__)


def json_default_int(o):
    if isinstance(o, np.integer):
        return int(o)
    raise TypeError


class DatasetHandler(BaseDataHandler):

    def __init__(self, did, group_ids=None, **kwargs):
        """
        Initialization.

        :param did: Dataset sample id.
        :type did: int/str
        :param group_ids: Group ids (if dataset groups were created).
        :type group_ids: list/None

        :keyword features: Selected features (for further analysis).
        :keyword lod_data: Level-of-Detail Generator descriptive data.
        :keyword load_initial_dataset: Flag to load initial dataset only.
        :keyword process_initial_dataset: Flag to process initial dataset.
        :keyword load_history_data: Flag to load history data.
        :keyword use_normalized_dataset: Flag to use normalized dataset.
        :keyword operation_id: Operation id to be loaded.
        """
        super().__init__(did=did)

        self._group_ids = group_ids  # possible values: None, empty list, list
        self._origin = None
        self._modifications = {}
        self._property_set = {}

        self._mode = 'all'
        self._use_normalized_dataset = kwargs.get(
            'use_normalized_dataset', False)

        self.features_description = []
        self.operation_handler = OperationHandler()

        if (kwargs.get('load_initial_dataset', False) or
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
                    'lod': lod_data}  # if set then will be extended with groups

                self._form_dataset_modifications(dataset=dataset)
            else:
                self._origin = dataset

        elif kwargs.get('load_history_data', False):
            self._load_data_stack(operation_id=kwargs.get('operation_id'))

    def create_dataset_storage(self, df):
        """
        Create storage-file for defined DataFrame data.

        :param df: Input [raw] dataset sample.
        :type df: pandas.DataFrame
        """
        with h5py.File(self._file_name, 'w') as f:

            # "base" group
            base_group = f.create_group('base')
            base_group.attrs['user'] = ''
            base_group.attrs['date'] = str(datetime.utcnow())

            # "default" dataset
            base_group.create_dataset(
                name='default',
                data=np.array(df.to_records(
                    column_dtypes=dict(zip(df.columns.to_list(), map(
                        lambda x: h5py.special_dtype(vlen=str)
                        if x in [np.dtype('O'), np.dtype('S'), np.dtype('U')]
                        else x, df.dtypes.to_list()))),
                    index=True)))
            base_group['default'].attrs['index'] = df.index.name

            # "features_description" dataset
            # TODO: Check - is it necessary to apply "dropNA"?
            df.dropna(axis=1, how='all', inplace=True)
            df.dropna(axis=0, how='all', inplace=True)
            base_group.create_dataset(
                name='features_description',
                data=json.dumps(self._get_dataset_features_description(df),
                                default=json_default_int))

    def _get_initial_dataset(self, **kwargs):
        """
        Get initial dataset sample (load from the storage file).

        :keyword usecols: Requested features from the initial dataset.

        :return: Initial or grouped dataset sample.
        :rtype: pandas.DataFrame/None
        """
        if self._group_ids is None:

            with h5py.File(self._file_name, 'r') as f:

                output = pd.DataFrame.from_records(f['base']['default'][()])
                output.set_index(f['base']['default'].attrs['index'],
                                 inplace=True)

                if kwargs.get('usecols'):
                    output = output.loc[:, kwargs['usecols']]

                self.features_description = json.loads(
                    f['base']['features_description'][()])

        elif self._group_ids:
            output = GroupedDataHandler(did=self._did,
                                        group_ids=self._group_ids[:-1]).\
                get_group(group_id=int(self._group_ids[-1]))
        else:
            output = None
            logger.error('[DatasetHandler._get_initial_dataset] '
                         'Group ids are not set - '
                         f'did: {self._did}, group_ids: {self._group_ids}')
        return output

    @property
    def _file_name(self):
        return os.path.join(self._get_storage_dir_name(),
                            f'{self._did}.{FILE_EXTENSION_DEFAULT}')

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

        _dataset = self._normalized if self._use_normalized_dataset \
            else self._origin

        if self._mode == 'numeric':
            _set = set(_dataset.columns.tolist())
            _features = [x for x in self._property_set['features'] if x in _set]
            # TODO: Re-check that feature selection is needed here
            #  (it was processed at _form_dataset_modifications for _origin dataset)
            #  (Note: for LoD _origin dataset it might behave differently)
            return _dataset.loc[:, _features]
        elif self._mode == 'all':
            return pd.concat([_dataset, self._auxiliary], axis=1, sort=True)

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

    def _save_data_stack(self, reprocess=False):
        """
        Save modifications of the initial dataset and corresponding data.

        :param reprocess: Flag to force re-creation of dataset modifications.
        :type reprocess: bool
        """
        err_msg_subj = '[DatasetHandler._save_data_stack]'

        if not os.path.isfile(self._file_name):
            logger.error(f'{err_msg_subj} Failed to find the file '
                         f'({self._file_name})')

        if reprocess:
            with h5py.File(self._file_name, 'a') as f:
                if f['base'].get('modified') is not None:
                    del f['base']['modified']

        try:
            with h5py.File(self._file_name, 'r+') as f:

                # "modified" group
                modified_group = f['base'].get('modified')
                if modified_group is None:
                    modified_group = f['base'].create_group('modified')
                    modified_group.attrs['date'] = str(datetime.utcnow())
                    modified_group.attrs['selected_features'] = json.dumps(
                        self._property_set['features'])
                    modified_group.attrs['operations_count'] = 0

                    # "numeric_real" dataset
                    modified_group.create_dataset(
                        name='numeric_real',
                        data=np.array(self._origin.to_records(index=True)))

                    # "numeric_norm" dataset
                    modified_group.create_dataset(
                        name='numeric_norm',
                        data=np.array(self._normalized.to_records(index=True)))

                    # "auxiliary" dataset
                    modified_group.create_dataset(
                        name='auxiliary',
                        data=np.array(self._auxiliary.to_records(
                            column_dtypes=dict(map(
                                lambda x: (x, h5py.special_dtype(vlen=str)),
                                self._auxiliary.columns.to_list())),
                            index=True)))

                    # "lod" dataset
                    modified_group.create_dataset(
                        name='lod',
                        data=json.dumps(self._property_set['lod'],
                                        default=json_default_int))

                # "operation" group
                self.operation_handler.save_to_hdf5(root_group=modified_group)

        except Exception as e:
            logger.error(f'{err_msg_subj} Failed to save data '
                         f'({self._file_name}): {e}')
            raise

    def _load_data_stack(self, **kwargs):
        """
        Load dataset modifications and corresponding data from the storage file.

        :keyword operation_id: Operation id to be loaded.
        """
        err_msg_subj = '[DatasetHandler._load_data_stack]'

        if not os.path.isfile(self._file_name):
            logger.error(f'{err_msg_subj} Failed to find the file '
                         f'({self._file_name})')

        try:
            with h5py.File(self._file_name, 'r') as f:
                modified_group = f['base']['modified']

                self._origin = pd.DataFrame.from_records(
                    modified_group['numeric_real'][()])
                self._origin.set_index(f['base']['default'].attrs['index'],
                                       inplace=True)

                self._modifications.update({
                    'normalized': pd.DataFrame.from_records(
                        modified_group['numeric_norm'][()]),
                    'auxiliary': pd.DataFrame.from_records(
                        modified_group['auxiliary'][()])})

                self._normalized.set_index(f['base']['default'].attrs['index'],
                                           inplace=True)
                self._auxiliary.set_index(f['base']['default'].attrs['index'],
                                          inplace=True)

                self._property_set.update({
                    'features': json.loads(
                        modified_group.attrs['selected_features']),
                    'lod': json.loads(
                        modified_group['lod'][()])})

                if kwargs.get('operation_id') is not None:
                    self.operation_handler.load_from_hdf5(
                        root_group=modified_group,
                        operation_id=int(kwargs['operation_id']))

        except Exception as e:
            logger.error(f'{err_msg_subj} Failed to load data '
                         f'({self._file_name}): {e}')
            raise

    @staticmethod
    def _get_dataset_features_description(df):
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
                            'distribution':
                                df[column].value_counts().to_dict()})
                    else:
                        item.update({
                            'measure_type': 'non-categorical',
                            'unique_values': unique_values[:10]})

            output.append(item)
        return output

    def save(self, reprocess=False):
        """
        Public method to save changes into the storage file.

        :param reprocess: Flag to force re-creation of dataset modifications.
        :type reprocess: bool
        """
        if (self._origin is not None and
                self._modifications and self._property_set):
            self._save_data_stack(reprocess=reprocess)
