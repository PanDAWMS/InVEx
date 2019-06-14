"""
Basic methods to process requests for data visualization.
"""

import io
import json
import logging
import os.path

import pandas as pd

from datetime import datetime

from django.conf import settings

from core.settings.base import BASE_DIR
from core import calc

from .calc.handlers import DatasetHandler
from .providers import LocalReader

DATASET_FILES_PATH = BASE_DIR + '/datasets/'
SITE_SITE_DATASET_FILES_PATH = BASE_DIR + '/site_site_datasets/'
FILES_LIST_NAME = 'files_list.json'

logger = logging.getLogger(__name__)
local_reader = LocalReader()


def list_csv_data_files(dir_name):
    """
    Get the list of local CSV data files.

    :param dir_name: [Full] directory name.
    :type dir_name: str
    :return: List with descriptions of local files.
    :rtype: list
    """
    output = None

    full_file_name = os.path.join(dir_name, FILES_LIST_NAME)
    if os.path.isfile(full_file_name):
        with open(full_file_name, 'r') as f:
            output = json.loads(f.read())

    return output


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
    list_of_files = list_csv_data_files(DATASET_FILES_PATH)
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
    if request.GET['remotesrc'] == 'pandajobs' and 'taskid' in request.GET:
        try:
            from .providers import PandaReader
        except ImportError as e:
            logger.error('{0} {1}'.format(err_msg_subj, e))
            raise
        else:
            filter_params = {}
            if 'days' in request.GET:
                filter_params['days'] = request.GET['days']
            else:
                filter_params['fulllist'] = 'true'

            output = _process_input_data(
                source_type='json',
                source_data=PandaReader().get_jobs_data_by_task(
                    task_id=request.GET['taskid'],
                    filter_params=filter_params),
                **{'index_name': 'pandaid'})
    else:
        logger.error('{} Request parameters are incorrect: {}'.
                     format(err_msg_subj, json.dumps(request.GET)))

    return output


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
    :rtype: dataset.DatasetHandler
    """
    features, lod_features = [], []
    for feature in json.loads(request.POST['features']):
        if feature['enabled'] == 'true':
            features.append(feature['feature_name'])
        if feature.get('lod_enabled') == 'true':
            lod_features.append(feature['feature_name'])

    lod_data = None
    if request.POST.get('lod_activated') == 'true':
        lod_data = {'mode': request.POST['lod_mode'],
                    'value': int(request.POST['lod_value']),
                    'features': lod_features}

    return DatasetHandler(did=dataset_id, group_ids=group_ids,
                          features=features, lod_data=lod_data,
                          process_initial_dataset=True)


def get_processed_view_data(request, dataset_id, group_ids=None):
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
    ds_handler = _get_dataset_handler_by_request_data(
        request, dataset_id, group_ids)

    view_data = ds_handler.get_view_data(with_full_set=True)
    view_data.update({'request': request})
    return view_data


def set_processed_view_data(request, dataset_id, group_ids=None):
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
    ds_handler = _get_dataset_handler_by_request_data(
        request, dataset_id, group_ids)
    ds_handler.save()

    view_data = ds_handler.get_view_data(with_full_set=True)
    view_data.update({'data_is_ready': True,
                      'request': request})
    return view_data


def prepare_view_data(dataset_id, group_ids=None, op_number=None):
    """
    Prepare view data for UI [initial page load and with applied operations].

    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :param op_number: [Current] operation number.
    :type op_number: int/str/None
    :return: Key-value pairs for UI representation.
    :rtype: dict
    """
    err_msg_subj = '[form_reactions.prepare_view_data]'

    try:
        op_number = int(op_number)
    except (TypeError, ValueError):
        op_number = None

    if op_number is not None:
        ds_handler = DatasetHandler(did=dataset_id, group_ids=group_ids,
                                    load_history_data=True)

        op_history = ds_handler.operation_history
        if op_number >= op_history.length():
            op_number = op_history.length() - 1

        operation = op_history.get_step(op_number)
        if operation[0]._type_of_operation != 'cluster':
            logger.error('{} The type of the operation is not "cluster": {}'.
                         format(err_msg_subj, operation[0]._type_of_operation))
        clusters = operation[0].predict(ds_handler.clustering_dataset).tolist()

        view_data = ds_handler.get_view_data(with_full_set=True)
        view_data.update({
            'data_is_ready': True,
            'clusters': clusters,
            'count_of_clusters': len(set(clusters)),
            'cluster_ready': True,
            'parameters': operation[0].print_parameters()})

        if len(operation) >= 3:
            view_data['visualparameters'] = operation[2]
    else:
        ds_handler = DatasetHandler(did=dataset_id, group_ids=group_ids,
                                    load_initial_dataset=True)
        view_data = ds_handler.get_view_data(with_full_set=False)

    return view_data


def clusterize(request, dataset_id, group_ids=None):
    """
    Clustering of data objects/records from the provided dataset sample.

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :param dataset_id: Dataset sample id.
    :type dataset_id: int/str
    :param group_ids: Group ids (if dataset groups were created).
    :type group_ids: list/None
    :return: Key-value pairs for UI representation.
    :rtype: dict
    """
    err_msg_subj = '[form_reactions.clusterize]'

    operation, view_data_extras = None, {}
    if 'algorithm' in request.POST:
        if (request.POST['algorithm'] == 'KMeans' and
                'numberofcl' in request.POST):

            operation = calc.KMeansClustering.KMeansClustering()
            operation.set_parameters(int(request.POST['numberofcl']))

        elif (request.POST['algorithm'] == 'MiniBatchKMeans' and
                'numberofcl' in request.POST and 'batch_size' in request.POST):

            operation = calc.MiniBatchKMeansClustering.\
                MiniBatchKMeansClustering()
            operation.set_parameters(int(request.POST['numberofcl']),
                                     int(request.POST['batch_size']))
            view_data_extras['batch_size'] = int(request.POST['batch_size'])

        elif (request.POST['algorithm'] == 'DBSCAN' and
                'min_samples' in request.POST and 'eps' in request.POST):

            operation = calc.DBScanClustering.DBScanClustering()
            operation.set_parameters(int(request.POST['min_samples']),
                                     float(request.POST['eps']))
            view_data_extras.update({
                'min_samples': int(request.POST['min_samples']),
                'eps': float(request.POST['eps'])})

        else:
            logger.error('{} Requested algorithm is not found: {}'.
                         format(err_msg_subj, json.dumps(request.POST)))
    else:
        logger.error('{} Request is incorrect: {}'.
                     format(err_msg_subj, json.dumps(request.POST)))

    output_op_number = None
    ds_handler = DatasetHandler(did=dataset_id, group_ids=group_ids,
                                load_history_data=True)

    if operation is not None:
        view_data_extras['parameters'] = operation.print_parameters()
        try:
            clusters = operation.process_data(ds_handler.clustering_dataset)
        except Exception as e:
            logger.error('{} Failed to perform clustering: {} - {}'.
                         format(err_msg_subj, json.dumps(request.POST), e))
            raise
        else:
            if clusters is not None:
                op_history = ds_handler.operation_history
                op_history.append(ds_handler.clustering_dataset,
                                  operation,
                                  request.POST['visualparameters'])
                view_data_extras.update({
                    'clusters': clusters.tolist(),
                    'count_of_clusters': int(request.POST['numberofcl']),
                    'cluster_ready': True})
                output_op_number = op_history.length() - 1
                ds_handler.operation_history = op_history
                ds_handler.save()
            else:
                logger.error('{} No clusters were created: {}'.format(
                    err_msg_subj, json.dumps(operation.save_parameters())))

    view_data = ds_handler.get_view_data(with_full_set=True)
    view_data.update(view_data_extras)
    view_data.update({
        'algorithm': request.POST['algorithm'],
        'visualparameters': request.POST['visualparameters'],
        'request': request})

    return view_data, output_op_number


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
            columns.append('p'+str(i))
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
                        logger.error('!form_reactions.load_json_site_to_site!: Failed to read file.\nFilename: ' +
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
