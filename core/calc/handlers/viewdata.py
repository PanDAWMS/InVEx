"""
Class ViewDataHandler provides methods for preparing output for
UI representation (at the client side).
"""

import json
import logging
import os

import numpy as np
import pandas as pd

from sklearn import preprocessing
from sklearn.impute import SimpleImputer

from datetime import datetime

from ...settings.base import BASE_DIR

from .. import data_converters
from ..basicstatistics import BasicStatistics, DESCRIPTION as STAT_DESCRIPTION

from ._base import BaseDataHandler

DATASET_FILES_PATH = BASE_DIR + '/datasets/'
FILES_LIST_NAME = 'files_list.json'

STAT_FILE_EXTENSION = 'stat'

LOD_MODE_DEFAULT = 'minibatch'
LOD_VALUE_DEFAULT = 50

VIEW_DATA_MODE_DEFAULT = 'datavisualization'

CONTEXT_DATA_DEFAULT = {
    'data_uploaded': False,
    'data_is_ready': False,
    'type': VIEW_DATA_MODE_DEFAULT,  # values: datavisualization, site2site

    # dataset description
    'dsID': None,
    'num_records': None,
    'index_name': None,
    'features': [],

    # LoD parameters
    'lod_activated': False,
    'lod_mode': LOD_MODE_DEFAULT,
    'lod_value': LOD_VALUE_DEFAULT,
    'lod_data': None,

    # clustering
    'algorithm': None,
    'parameters': {},
    'clusters': [],
    'count_of_clusters': None,  # TODO: Check that this parameter is in use.
    'cluster_ready': False,

    # visualization
    'index': None,
    'real_dataset': None,
    'norm_dataset': None,
    'aux_dataset': None,
    'dim_names': [],
    'aux_names': [],
    'real_metrics': [],
    'corr_matrix': [],
    'visualparameters': None,

    'filename': None,  # selected file from server
    'dataset_files': None,  # list of files from server
    'PREVIEW_URL': None,
    'NEXT_GROUP_URL': None,
    'PAGE_TITLE': 'InVEx',

    'built': None,  # TODO: Check when and where this parameter is used.
    'group_vis': False  # TODO: Parameter might be obsoleted (to be removed).
}
CONTEXT_DATA_BY_MODES = {
    VIEW_DATA_MODE_DEFAULT: {},
    'site2site': {
        'saveid': None,
        'xarray': [],
        'yarray': [],
        'dim_names_short': [],
        'startedat': None  # "Server started working"
    }
}
# TODO: Check the consistency of the context_data key-value pairs.
# TODO: Re-work context_data parameter names.
logger = logging.getLogger(__name__)


def list_csv_data_files(dir_path=None):
    """
    Get the list of local CSV data files.

    :param dir_path: [Full] directory name/path.
    :type dir_path: str/None
    :return: List with descriptions of local files.
    :rtype: list
    """
    output = None

    file_path = os.path.join(dir_path or DATASET_FILES_PATH, FILES_LIST_NAME)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            output = json.loads(f.read())

    return output


class ViewDataHandler(BaseDataHandler):

    def __init__(self, dataset_handler=None, mode=None):
        """
        Initialization.

        :param dataset_handler: DatasetHandler object.
        :type dataset_handler: handlers.dataset.DatasetHandler/None
        :param mode: Mode of the visualization process.
        :type mode: str/None
        """
        super().__init__(did='0' if dataset_handler is None
                         else dataset_handler._did)

        self._dataset_handler = dataset_handler
        self._mode = mode or VIEW_DATA_MODE_DEFAULT

        self._data = dict(CONTEXT_DATA_DEFAULT)
        self._data.update(CONTEXT_DATA_BY_MODES[self._mode])
        self._data.update({'type': self._mode,
                           'built': datetime.utcnow()})

        try:
            self._data['dataset_files'] = list_csv_data_files()
        except Exception as e:
            logger.error('[ViewDataHandler.__init__] Failed to read the list '
                         'of files with dataset samples: {}'.format(e))

    @property
    def context_data(self):
        return self._data

    @staticmethod
    def _get_scaled_dataset(df):
        df_numeric = df._get_numeric_data()
        df_imputer = pd.DataFrame(
            data=SimpleImputer(
                missing_values=np.nan,
                strategy='mean').fit_transform(df_numeric),
            columns=df_numeric.columns)
        scaled_df = pd.DataFrame(
            data=preprocessing.MinMaxScaler().fit_transform(df_imputer),
            columns=df_imputer.columns)
        return scaled_df

    def set_dataset_description(self, with_full_set=False):
        """
        Set corresponding parameters that describe the dataset.

        :param with_full_set: Flag to get full set of context parameters.
        :type with_full_set: bool
        """
        err_msg_subj = '[ViewDataHandler.set_dataset_description]'

        if self._dataset_handler is None:
            err_msg = ('{} DatasetHandler is not defined'.format(err_msg_subj))
            logger.error(err_msg)
            raise Exception(err_msg)

        _origin = self._dataset_handler._origin
        _normalized = self._dataset_handler._normalized
        _auxiliary = self._dataset_handler._auxiliary

        df = _origin.copy()
        if _auxiliary is not None:
            df = df.join(_auxiliary)
        # TODO: Check - is it necessary to apply "dropNA"?
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(axis=0, how='all', inplace=True)

        self._data.update({
            'dsID': self._did,
            'index_name': df.index.name,
            'num_records': len(df.index),
            'features': self._dataset_handler.features_description,
            'data_uploaded': True})

        if with_full_set:
            try:
                self._data.update({
                    'index': [df.index.name or 'id'],
                    'real_dataset':
                        data_converters.pandas_to_js_list(_origin),
                    'norm_dataset':
                        data_converters.pandas_to_js_list(_normalized),
                    'aux_dataset':
                        data_converters.pandas_to_js_list(_auxiliary),
                    'dim_names': _normalized.columns.tolist(),
                    'aux_names': _auxiliary.columns.tolist()})

                ds_origin_stats = BasicStatistics().process_data(_origin)
                ds_stats_values = []
                for i in range(len(ds_origin_stats)):
                    ds_stats_values.append(ds_origin_stats[i].tolist())
                self._data['real_metrics'] = [STAT_DESCRIPTION, ds_stats_values]
                # TODO: Re-work this.
                # TODO: Data should be taken from "features_description"

                corr_matrix = _origin.corr()
                corr_matrix.dropna(axis=0, how='all', inplace=True)
                corr_matrix.dropna(axis=1, how='all', inplace=True)
                self._data['corr_matrix'] = corr_matrix.values.tolist()

            except Exception as e:
                logger.error(f'{err_msg_subj} Failed to prepare basics of '''
                             f'the view data: {e}')
                raise

            # prepare LoD information
            lod_data = self._dataset_handler._property_set.get('lod') or {}
            if lod_data.get('value'):
                self._data.update({
                    'lod_activated': True,
                    'lod_mode': lod_data['mode'],
                    'lod_value': lod_data['value'],
                    'lod_data': lod_data.get('groups', [])})

            # prepare information about checked features
            features = self._dataset_handler._property_set.get('features', [])
            lod_features = lod_data.get('features', [])
            for feature in self._data['features']:
                if feature['feature_name'] in features:
                    feature['enabled'] = 'true'
                else:
                    feature['enabled'] = 'false'
                if feature['feature_name'] in lod_features:
                    feature['lod_enabled'] = 'true'

    def set_clustering_data(self, operation, camera_params):
        """
        Set parameters related to the clustering process.

        :param operation: Applied operation of clustering (with result labels).
        :type operation: baseoperationclass.BaseOperationClass
        :param camera_params: Camera parameters.
        :type camera_params: dict
        """
        cluster_labels = operation.results.tolist()  # TODO: change to labels
        self._data.update({
            'algorithm': operation._operation_code_name,
            'parameters': operation.print_parameters(),  # TODO: to be changed
            'clusters': cluster_labels,
            'count_of_clusters': len(set(cluster_labels)),
            'cluster_ready': True,
            'visualparameters': camera_params})

    def set_preview_url(self, value):
        """
        Set preview url for the corresponding button (at the HTML page).

        :param value: Url.
        :type value: str
        """
        self._data.update({'PREVIEW_URL': value,
                           'NEXT_GROUP_URL': value})

    def set_data_readiness(self):
        """
        Set flag that data is ready (preprocessed for further analysis).
        """
        self._data['data_is_ready'] = True
