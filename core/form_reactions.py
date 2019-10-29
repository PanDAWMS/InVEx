"""
Basic methods to process requests for data visualization.
"""

import io
import json
import logging
import os.path

import pandas as pd

from datetime import datetime
from urllib.parse import urlparse

from django.conf import settings

from core import calc
from core.settings.base import BASE_DIR
from core.calc import clustering

from .calc.handlers import DatasetHandler, ViewDataHandler
from .calc.handlers.viewdata import list_csv_data_files, DATASET_FILES_PATH
from .providers import LocalReader

SITE_SITE_DATASET_FILES_PATH = BASE_DIR + '/site_site_datasets/'

logger = logging.getLogger(__name__)
local_reader = LocalReader()


def create_dataset_storage(dataset_id):
    """
    Create directory for service files related to analyzed dataset sample.

    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :return: Full path for dataset storage.
    :rtype: str
    """
    output = os.path.join(settings.MEDIA_ROOT, str(dataset_id))

    try:
        os.mkdir(output)
    except OSError as e:
        logger.error('[form_reactions.create_dataset_storage] '
                     'Failed to create dataset storage: {}'.format(e))

    return output


def _process_input_data(source_type, source_data, **kwargs):
    """
    Get and process data to prepare data sample (i.e., store at the server).

    :param source_type: Type of the source: file, dataframe, json.
    :type source_type: str
    :param source_data: Source data.
    :type source_data: dict/pandas.DataFrame/json

    :keyword index_name: Column name that would be used as an index.

    :return: Dataset sample id.
    :rtype: str
    """
    err_msg_subj = '[form_reactions._process_input_data]'

    output = str(datetime.now().timestamp())
    dataset_path = os.path.join(create_dataset_storage(output),
                                '{}.csv'.format(output))
    try:
        if source_type == 'file':
            with open(dataset_path, 'wb+') as f:
                for chunk in source_data.chunks():
                    f.write(chunk)

        elif source_type == 'dataframe':
            source_data.to_csv(dataset_path)

        elif source_type == 'json' and 'index_name' in kwargs:
            df = pd.read_json(json.dumps(source_data))
            df.set_index(kwargs['index_name'], inplace=True)
            df.to_csv(dataset_path)
    except Exception as e:
        logger.error('{} Failed to prepare dataset sample: {}'.
                     format(err_msg_subj, e))

    return output


def set_csv_file_from_server(request):
    """
    Prepare dataset sample from the server file (test dataset samples).

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :return: Dataset sample id.
    :rtype: int/str
    """
    err_msg_subj = '[form_reactions.set_csv_file_from_server]'

    output = None
    list_of_files = list_csv_data_files()
    if 'filename' in request.POST and list_of_files is not None:
        for f in list_of_files:
            if f['value'] == request.POST['filename']:
                full_file_name = os.path.join(DATASET_FILES_PATH, f['filename'])
                if os.path.isfile(full_file_name):
                    output = _process_input_data(
                        source_type='dataframe',
                        source_data=local_reader.read_df(
                            file_path=full_file_name,
                            file_format='csv',
                            **{'index_col': 0,
                               'header': 0}))
                else:
                    logger.error('{} Failed to read data from server ({})'.
                                 format(err_msg_subj, full_file_name))
    else:
        logger.error('{} Request parameters are incorrect: {}'.
                     format(err_msg_subj, json.dumps(request.POST)))

    return output


def set_new_csv_file(request):
    """
    Upload new CSV data file.

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :return: Dataset sample id.
    :rtype: int/str
    """
    return _process_input_data(source_type='file',
                               source_data=request.FILES.get('customFile'))


def set_jobs_data_from_panda(request):
    """
    Get jobs data from PanDA system (by using providers.panda reader-client).

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :return: Dataset sample id.
    :rtype: int/str
    """
    err_msg_subj = '[form_reactions.set_jobs_data_from_panda]'

    output = None
    if request.GET['remotesrc'] == 'pandajobs':
        try:
            from .providers import PandaReader
        except ImportError as e:
            logger.error('{} {}'.format(err_msg_subj, e))
            raise

        source_data = None

        if 'taskid' in request.GET:
            filter_params = {}
            if 'days' in request.GET:
                filter_params['days'] = request.GET['days']
            else:
                filter_params['fulllist'] = 'true'

            source_data = PandaReader().get_jobs_data_by_task(
                task_id=request.GET['taskid'],
                filter_params=filter_params)

        elif 'bigpandaUrl' in request.GET:
            try:
                parsed_url = urlparse(request.GET['bigpandaUrl'])
            except ValueError as e:
                logger.error('{} No URL provided or provided str is not URL: '
                             '{}'.format(err_msg_subj, e))
                raise

            if parsed_url.path != '/jobs/':
                logger.error('{} Provided BigPanDA URL is incorrect: {}'.
                             format(err_msg_subj, json.dumps(request.GET)))
                raise

            filter_params = {'fulllist': 'true'}
            if len(parsed_url.query) > 0 and '=' in parsed_url.query:
                filter_params.update(dict(query_param.split('=') for query_param
                                          in parsed_url.query.split('&')))
                bigpanda_params_to_delete = ['display_limit']
                [filter_params.pop(i, None) for i in bigpanda_params_to_delete]

            source_data = PandaReader().get_jobs_data_by_url(
                filter_params=filter_params)

        if source_data:
            output = _process_input_data(
                source_type='json',
                source_data=source_data,
                **{'index_name': 'pandaid'})
        else:
            logger.error('{} Data from BigPanDA was not collected: {}'.
                         format(err_msg_subj, json.dumps(request.GET)))
            raise

    else:
        logger.error('{} Request parameters are incorrect: {}'.
                     format(err_msg_subj, json.dumps(request.GET)))

    return output


def get_empty_view_data(mode=None):
    """
    Get view data for UI representation (with default values).

    :param mode: Mode of the visualization process.
    :type mode: str/None
    :return: Key-value pairs for UI representation.
    :rtype: dict
    """
    return ViewDataHandler(mode=mode).context_data


def get_initial_view_data(dataset_id, group_ids=None, **kwargs):
    """
    Get view data for loaded dataset sample (with corresponding initial values).

    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :return: Key-value pairs for UI representation.
    :rtype: dict
    """
    viewdata_hdlr = ViewDataHandler(dataset_handler=DatasetHandler(
        did=dataset_id, group_ids=group_ids, load_initial_dataset=True))
    viewdata_hdlr.set_dataset_description(with_full_set=False)
    if 'preview_url' in kwargs:
        viewdata_hdlr.set_preview_url(kwargs['preview_url'])
    return viewdata_hdlr.context_data


def _get_dataset_handler_by_request_data(request, dataset_id, group_ids=None):
    """
    Create DatasetHandler by input parameters from the request.

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :return: DatasetHandler object.
    :rtype: handlers.dataset.DatasetHandler
    """
    features, lod_features = [], []
    for feature in json.loads(request.POST['features']):
        if feature['enabled'] == 'true':
            features.append(feature['feature_name'])
        if feature.get('lod_enabled') == 'true':
            lod_features.append(feature['feature_name'])

    lod_data = None
    if request.POST['lod_activated'] == 'true':
        lod_data = {'mode': request.POST['lod_mode'],
                    'value': int(request.POST['lod_value']),
                    'features': lod_features}

    return DatasetHandler(did=dataset_id, group_ids=group_ids,
                          features=features, lod_data=lod_data,
                          process_initial_dataset=True)


def get_processed_view_data(request, dataset_id, group_ids=None, **kwargs):
    """
    Process provided dataset sample and get view data for UI representation.

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :return: Key-value pairs for UI representation.
    :rtype: dict
    """
    viewdata_hdlr = ViewDataHandler(
        dataset_handler=_get_dataset_handler_by_request_data(
            request=request, dataset_id=dataset_id, group_ids=group_ids))
    viewdata_hdlr.set_dataset_description(with_full_set=True)
    if 'preview_url' in kwargs:
        viewdata_hdlr.set_preview_url(kwargs['preview_url'])
    return viewdata_hdlr.context_data


def set_processed_view_data(request, dataset_id, group_ids=None, **kwargs):
    """
    Save processed data and get view data for UI representation.

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :return: Key-value pairs for UI representation.
    :rtype: dict
    """
    dataset_hdlr = _get_dataset_handler_by_request_data(
        request=request, dataset_id=dataset_id, group_ids=group_ids)
    dataset_hdlr.save()

    viewdata_hdlr = ViewDataHandler(dataset_handler=dataset_hdlr)
    viewdata_hdlr.set_dataset_description(with_full_set=True)
    if 'preview_url' in kwargs:
        viewdata_hdlr.set_preview_url(kwargs['preview_url'])
    viewdata_hdlr.set_data_readiness()
    return viewdata_hdlr.context_data


def get_operational_view_data(dataset_id, group_ids, op_number, **kwargs):
    """
    Prepare view data for UI [initial page load and with applied operations].

    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :param op_number: [Current] operation number.
    :type op_number: int
    :return: Key-value pairs for UI representation.
    :rtype: dict
    """
    dataset_hdlr = DatasetHandler(did=dataset_id, group_ids=group_ids,
                                  load_history_data=True)

    op_history = dataset_hdlr.operation_history
    if op_number >= op_history.length():
        op_number = op_history.length() - 1

    operation, _, camera_params = op_history.get_step(op_number)
    if operation._type_of_operation != 'cluster':
        logger.error('[form_reactions.get_operational_view_data] '
                     'The type of the operation is not "cluster": type={}'.
                     format(operation._type_of_operation))

    viewdata_hdlr = ViewDataHandler(dataset_handler=dataset_hdlr)
    viewdata_hdlr.set_dataset_description(with_full_set=True)
    viewdata_hdlr.set_clustering_data(operation=operation,
                                      camera_params=camera_params)
    if 'preview_url' in kwargs:
        viewdata_hdlr.set_preview_url(kwargs['preview_url'])
    viewdata_hdlr.set_data_readiness()
    return viewdata_hdlr.context_data


def clusterize(request, dataset_id, group_ids=None):
    """
    Clustering of data objects/records from the provided dataset sample.

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :return: Number/id of the current operation.
    :rtype: int
    """
    err_msg_subj = '[form_reactions.clusterize]'

    operation = None
    mode = None
    if 'algorithm' in request.POST:

        logger.debug(request.POST)

        clusters_list = [] if request.POST['clustering_list_json'] == '' \
                else json.loads(request.POST['clustering_list_json'])

        if (request.POST['algorithm'] == 'KMeans' and
                'numberofcl_KMeans' in request.POST):

            operation = clustering.KMeansClustering.KMeansClustering()
            operation.set_parameters(int(request.POST['numberofcl_KMeans']),
                                     clusters_list)
            mode = 'numeric'

        elif (request.POST['algorithm'] == 'MiniBatchKMeans' and
                'numclusters_MiniBatchKMeans' in request.POST and
                'batchsize_MiniBatchKMeans' in request.POST):

            operation = clustering.MiniBatchKMeansClustering.\
                MiniBatchKMeansClustering()
            operation.set_parameters(num_clusters=int(request.POST['numclusters_MiniBatchKMeans']),
                                     features=clusters_list,
                                     batch_size=int(request.POST['batchsize_MiniBatchKMeans']))
            mode = 'numeric'

        elif (request.POST['algorithm'] == 'DAALKMeans' and
                'numclusters_DAALKMeans' in request.POST):

            operation = clustering.DAALKMeansClustering.DAALKMeansClustering()
            operation.set_parameters(int(request.POST['numclusters_DAALKMeans']),
                                     clusters_list)
            mode = 'numeric'

        elif (request.POST['algorithm'] == 'KPrototypes' and
                'cluster_number_KPrototypes' in request.POST and
                'categorical_data_weight_KPrototypes' in request.POST):

            operation = clustering.KPrototypesClustering.KPrototypesClustering()
            operation.set_parameters(int(request.POST['cluster_number_KPrototypes']),
                                     int(request.POST['categorical_data_weight_KPrototypes']),
                                     clusters_list)
            mode = 'all'

        elif (request.POST['algorithm'] == 'Hierarchical' and
                'cluster_number_Hierarchical' in request.POST and
                'categorical_data_weight_Hierarchical' in request.POST):

            operation = clustering.HierarchicalClustering.HierarchicalClustering()
            operation.set_parameters(int(request.POST['cluster_number_Hierarchical']),
                                     int(request.POST['categorical_data_weight_Hierarchical']),
                                     clusters_list)
            mode = 'all'

        elif (request.POST['algorithm'] == 'DBSCAN' and
                'min_samples_DBSCAN' in request.POST and 'eps_DBSCAN' in request.POST):

            operation = clustering.DBScanClustering.DBScanClustering()
            operation.set_parameters(int(request.POST['min_samples_DBSCAN']),
                                     float(request.POST['eps_DBSCAN']),
                                     clusters_list)

            mode = 'numeric'

        elif (request.POST['algorithm'] == 'GroupData' and
                'feature_name_GroupData' in request.POST):

            operation = clustering.GroupData.GroupData()
            operation.set_parameters(request.POST['feature_name_GroupData'])

            mode = 'all'

        else:
            logger.error('{} Requested algorithm is not found: {}'.
                         format(err_msg_subj, json.dumps(request.POST)))
    else:
        logger.error('{} Request is incorrect: {}'.
                     format(err_msg_subj, json.dumps(request.POST)))

    dataset_hdlr = DatasetHandler(did=dataset_id,
                                  group_ids=group_ids,
                                  load_history_data=True,
                                  use_normalized_dataset='use_normalized_dataset' in request.POST and
                                                         request.POST['use_normalized_dataset'] == "on")

    dataset_hdlr._mode = mode
    clustering_dataset = dataset_hdlr.clustering_dataset

    output_op_number = None
    if operation is not None:
        try:
            clusters = operation.process_data(clustering_dataset)
        except Exception as e:
            logger.error('{} Failed to perform data clustering: {} - {}'.
                         format(err_msg_subj, json.dumps(request.POST), e))
        else:
            if clusters is not None:
                op_history = dataset_hdlr.operation_history
                op_history.append(clustering_dataset,
                                  operation,
                                  request.POST['visualparameters'])
                dataset_hdlr.operation_history = op_history
                dataset_hdlr.save()

                output_op_number = op_history.length() - 1
            else:
                logger.error('{} No clusters were created: {}'.format(
                    err_msg_subj, json.dumps(operation.save_parameters())))

    return output_op_number


# TODO: Re-check/re-work this method (!), it might work incorrectly.
def predict_cluster(request, dataset_id=None, group_ids=None, op_number=None):
    """
    Predict cluster for the data object.
    """
    err_msg_subj = '[form_reactions.predict_cluster]'

    output = {}
    if 'data' not in request.POST:
        logger.error('{} No corresponding data in request: {}'.
                     format(err_msg_subj, json.dumps(request.POST)))

    try:
        op_number = int(op_number)
    except (TypeError, ValueError):
        op_number = None

    if op_number:

        ds_handler = DatasetHandler(did=dataset_id, group_ids=group_ids,
                                    load_history_data=True)
        op_history = ds_handler.operation_history
        if op_number >= op_history.length():
            op_number = op_history.length() - 1

        operation = op_history.get_step(op_number)[0]
        if operation[0]._type_of_operation != 'cluster':
            logger.error('{} The type of the operation is not "cluster": {}'.
                         format(err_msg_subj, operation[0]._type_of_operation))
        try:
            output.update({
                'results': operation[0].predict(
                    [json.loads(request.POST['data'])]).tolist(),
                'clustertype': operation[0]._operation_name})
        except Exception as e:
            logger.error('{} Failed to perform clusters re-build (): {}'.format(
                err_msg_subj, json.dumps(operation.save_parameters()), e))
            raise

    return output

# ------------------------------


# SITE TO SITE VISUALIZATION FUNCTIONS
def read_site_to_site_json(filename, is_file=False):
    if is_file:
        file = filename
    else:
        file = open(filename)
    data = json.load(file)
    if 'columns' in data['transfers']:
        columns = data['transfers']['columns']
    else:
        columns = ['source', 'destination']
        for i in range(2, len(data['transfers']['rows'][0])):
            columns.append('p' + str(i))
    dataset = pd.DataFrame.from_records(data['transfers']['rows'], columns=columns,
                                        coerce_float=True)
    file.close()
    return dataset


def prepare_axes(dataset):
    source_col = dataset.groupby(dataset.columns[0]).max()
    source_col.sort_values(dataset.columns[2], inplace=True, ascending=False)
    xaxis = source_col.index
    destination_col = dataset.groupby(dataset.columns[1]).max()
    destination_col.sort_values(dataset.columns[2], inplace=True, ascending=False)
    yaxis = destination_col.index
    return [xaxis, yaxis]


def prepare_basic_s2s(norm_dataset, real_dataset, auxiliary_dataset, numcols, op_history):
    try:
        if norm_dataset.index.name is None:
            idx = ['id']
        else:
            idx = [norm_dataset.index.name]
        columns = norm_dataset.columns.tolist()

        metrics = calc.basicstatistics.BasicStatistics()
        numbers_dataset = real_dataset[numcols]
        real_dataset_stats_or = metrics.process_data(numbers_dataset)
        real_dataset_stats = []
        for i in range(len(real_dataset_stats_or)):
            real_dataset_stats.append(real_dataset_stats_or[i].tolist())

        corr_matrix = real_dataset.corr()
        xarray, yarray = prepare_axes(norm_dataset)
        xarray_list = xarray.tolist()
        yarray_list = yarray.tolist()
        aux_columns = auxiliary_dataset.columns.tolist()

        data = {
            'norm_dataset': calc.data_converters.pandas_to_js_list(norm_dataset),
            'real_dataset': calc.data_converters.pandas_to_js_list(real_dataset),
            'aux_dataset': calc.data_converters.pandas_to_js_list(auxiliary_dataset),
            'data_is_ready': True,
            'cluster_ready': False,
            'lod_activated': False,
            'filename': False,
            'visualparameters': False,
            'lod_data': False,
            'saveid': False,
            'algorithm': False,
            'dim_names_short': numcols,
            'dim_names': columns,
            'aux_names': aux_columns,
            'xarray': xarray_list,
            'yarray': yarray_list,
            'index': idx,
            'real_metrics': [calc.basicstatistics.DESCRIPTION, real_dataset_stats],
            'operation_history': op_history,
            'corr_matrix': corr_matrix.values.tolist(),
            'type': 'site2site'
        }
        return data
    except Exception as exc:
        logger.error('!form_reactions.prepare_basic!: Failed to prepare basics of the data. \n' + str(exc))
        raise


def load_json_site_to_site(request):
    if 'customFile' in request.FILES:
        try:
            dataset = read_site_to_site_json(io.StringIO(request.FILES['customFile'].read().decode('utf-8')), True)
        except Exception as exc:
            logger.error(
                '!form_reactions.load_json_site_to_site!: Failed to load data from the uploaded csv file. \n' + str(
                    exc))
            raise
    else:
        list_of_files = list_csv_data_files(SITE_SITE_DATASET_FILES_PATH)
        dataset = None
        if ('filename' in request.POST) and (list_of_files is not None):
            for file in list_of_files:
                if request.POST['filename'] == file['value']:
                    if os.path.isfile(SITE_SITE_DATASET_FILES_PATH + file['filename']):
                        dataset = read_site_to_site_json(SITE_SITE_DATASET_FILES_PATH + file['filename'])
                    else:
                        logger.error('!form_reactions.load_json_site_to_site!: Failed to read file.\nFilename: ' + \
                                     SITE_SITE_DATASET_FILES_PATH + file['filename'])
                        return {}
        else:
            logger.error('!form_reactions.load_json_site_to_site!: Wrong request.\nRequest parameters: ' + json.dumps(
                request.POST))
            return {}
        if dataset is None:
            logger.error(
                '!form_reactions.load_json_site_to_site!: Failed to get the dataset. \nRequest parameters: ' + json.dumps(
                    request.POST))
            return {}
    # drop all columns and rows with NaN values
    try:
        calc.importcsv.dropNA(dataset)

        mesh_coordinates = dataset.iloc[:, :2]
        numeric_columns = calc.importcsv.numeric_columns(dataset)
        numeric_dataset = dataset
        norm_dataset = mesh_coordinates.join(calc.importcsv.normalization(numeric_dataset, numeric_columns), how='left')
        calc.importcsv.dropNA(norm_dataset)
        columns = norm_dataset.columns.tolist()
        numeric_dataset = dataset[columns]
        auxiliary_dataset = dataset.drop(numeric_columns, 1)
        op_history = calc.operationshistory.OperationHistory()
        data = prepare_basic_s2s(norm_dataset, numeric_dataset, auxiliary_dataset, numeric_columns, op_history)
        data['request'] = request
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.load_json_site_to_site!: Failed to prepare data after uploading from file. \n' + str(exc))
        raise
