"""
Basic methods to react to different forms
"""
from core import calc
import io
import os.path
from datetime import datetime
import pandas as pd
import json
from core.settings.base import BASE_DIR
from .providers import LocalReader, PandaReader
import logging
from django.conf import settings
from django.http import HttpResponse, Http404

SAVED_FILES_PATH = BASE_DIR + '/datafiles/'
DATASET_FILES_PATH = BASE_DIR + '/datasets/'
SITE_SITE_DATASET_FILES_PATH = BASE_DIR + '/site_site_datasets/'
TEST_DATASET_FILES_PATH = BASE_DIR + '/test_datasets/'
FILES_LIST_NAME = 'files_list.json'
BACKUP_FILE = '_backup'

# Get an instance of a logger
logger = logging.getLogger(__name__)


def list_csv_data_files(directory):
    """
    Get the list of CSV data files.
    :param directory: 
    :return: 
    """
    if not os.path.isfile(directory + FILES_LIST_NAME):
        return None
    file = open(directory + FILES_LIST_NAME, 'r')
    csv_data_files = json.loads(file.read())
    return csv_data_files

def save_data(original_dataset, norm_dataset, auxiliary_dataset, op_history, lod, lod_metadata, filename=None):
    """
    Saving data to the operations history file.
    1st line - original dataset
    2nd line - normalized datasample
    3rd line - operations history (list of clusterizations)
    4th line - auxiliary data (not numeric values)
    5th line - value of Level-of-Detail Generator
    6th line - groups metadata
    :param lod_metadata: 
    :param original_dataset: 
    :param norm_dataset: 
    :param auxiliary_dataset: 
    :param op_history: 
    :param lod:
    :param filename: 
    :return: 
    """
    if filename is None:
        filename = str(datetime.now().timestamp())
        while os.path.isfile(SAVED_FILES_PATH + filename):
            filename = filename + 't'
    else:
        if os.path.isfile(SAVED_FILES_PATH + filename + BACKUP_FILE):
            try:
                os.remove(SAVED_FILES_PATH + filename + BACKUP_FILE)
            except Exception as exc:
                logger.error('!form_reactions.save_data!: Failed to remove the backup file. \nFilename:'
                             + SAVED_FILES_PATH + filename + '\n' + str(exc))
                raise
        if os.path.isfile(SAVED_FILES_PATH + filename):
            try:
                os.rename(SAVED_FILES_PATH + filename, SAVED_FILES_PATH + filename + BACKUP_FILE)
            except Exception as exc:
                logger.error('!form_reactions.save_data!: Failed to rename the backup file. \nFilename:'
                             + SAVED_FILES_PATH + filename + '\n' + str(exc))
                raise
        if os.path.isfile(SAVED_FILES_PATH + filename):
            try:
                os.remove(SAVED_FILES_PATH + filename)
            except Exception as exc:
                logger.error('!form_reactions.save_data!: Failed to remove the original file. \nFilename:'
                             + SAVED_FILES_PATH + filename + '\n' + str(exc))
                raise
    try:
        file = open(SAVED_FILES_PATH + filename, "w")
        file.write(original_dataset.to_json(orient='table'))
        file.write('\n')
        file.write(norm_dataset.to_json(orient='table'))
        file.write('\n')
        file.write(op_history.save_to_json())
        file.write('\n')
        file.write(auxiliary_dataset.to_json(orient='table'))
        file.write('\n')
        file.write(lod)
        file.write('\n')
        file.write(str(lod_metadata))
        file.close()
        return filename
    except Exception as exc:
        logger.error('!form_reactions.save_data!: Failed to save the data. \nFilename:'
                     + SAVED_FILES_PATH + filename + '\n' + str(exc))
        raise


def load_data(filename):
    """
    Loading data from the operations history file.
    The file is reading line by line:
    1st line - original dataset
    2nd line - normalized datasample
    3rd line - operations history (list of clusterizations)
    4th line - auxiliary data (not numeric values)
    5th line - value of Level-of-Detail Generator
    6th line - groups metadata
    :param filename: 
    :return: 
    """
    if not os.path.isfile(SAVED_FILES_PATH + filename):
        logger.error('!form_reactions.load_data!: File is missing. Couldn\'t load the file. \nFilename:'
                     + SAVED_FILES_PATH + filename)
        return [None, None, None, None]
    try:
        file = open(SAVED_FILES_PATH + filename, "r")
        data = file.readline()
        original_dataset = calc.data_converters.table_to_df(data)
        data = file.readline()
        norm_dataset = calc.data_converters.table_to_df(data)
        data = file.readline()
        op_history = calc.operationshistory.OperationHistory()
        op_history.load_from_json(data)
        data = file.readline()
        aux_dataset = calc.data_converters.table_to_df(data)
        lod_value = int(file.readline())
        groups_metadata = file.readline()
        file.close()
        return [original_dataset, norm_dataset, op_history, aux_dataset, lod_value, groups_metadata]
    except Exception as exc:
        logger.error('!form_reactions.load_data!: Failed to load the data. \nFilename:'
                     + SAVED_FILES_PATH + filename + '\n' + str(exc))
        raise

def prepare_data_object(norm_dataset, real_dataset, auxiliary_dataset, op_history):
    """
    Preparing data object for the client. 
    This object includes all information about data sample:
    - initial data sample (numerical) 
    - normalized data sample
    - auxiliary data sample
    - names of numerical features (columns)
    - names of auxiliary features (columns)
    - data sample index
    - statistics for the initial data sample
    - operations history data file
    - array for the correlation matrix
    :param norm_dataset: 
    :param real_dataset: 
    :param auxiliary_dataset: 
    :param op_history: 
    :return: 
    """
    try:
        if norm_dataset.index.name is None:
            idx = ['id']
        else:
            idx = [norm_dataset.index.name]
        columns = norm_dataset.columns.tolist()

        metrics = calc.basicstatistics.BasicStatistics()
        real_dataset_stats_or = metrics.process_data(real_dataset)
        real_dataset_stats = []
        for i in range(len(real_dataset_stats_or)):
            real_dataset_stats.append(real_dataset_stats_or[i].tolist())

        corr_matrix = real_dataset.corr()
        corr_matrix.dropna(axis=0, how='all', inplace=True)
        corr_matrix.dropna(axis=1, how='all', inplace=True)

        aux_columns = auxiliary_dataset.columns.tolist()

        data = {
            'norm_dataset': calc.data_converters.pandas_to_js_list(norm_dataset),
            'real_dataset': calc.data_converters.pandas_to_js_list(real_dataset),
            'aux_dataset': calc.data_converters.pandas_to_js_list(auxiliary_dataset),
            'data_is_ready': True,
            'cluster_ready': False,
            'lod_activated': False,
            'visualparameters': False,
            'lod_data': False,
            'algorithm': False,
            'dim_names': columns,
            'aux_names': aux_columns,
            'index': idx,
            'filename': False,
            'real_metrics': [calc.basicstatistics.DESCRIPTION, real_dataset_stats],
            'operation_history': op_history,
            'corr_matrix': corr_matrix.values.tolist(),
            'type': 'datavisualization',
            'group_vis': False
        }
        return data
    except Exception as exc:
        logger.error('!form_reactions.prepare_data_object!: Failed to prepare basics of the data. \n' + str(exc))
        raise

def data_preparation(dataset, request):
    """
    Data Preparation includes:
    - cleaning data sample from NaNs
    - data sample normalization
    - splitting data sample into 2 parts: numeric and auxiliary.
    Numeric part contains only numerical data and is used for clustering.
    Auxiliary part contains objects, strings, datetime etc. and can be used for data grouping
    - calculating statistics for the normalized data sample
    - saving information about normalized data sample and statistics in the operations history file with the unique ID
    :param dataset: 
    :param request: 
    :return: 
    """
    LocalReader().drop_na(dataset)
    numeric_dataset = LocalReader().get_numeric_data(dataset)
    norm_dataset = LocalReader().scaler(numeric_dataset)
    auxiliary_dataset = dataset.drop(numeric_dataset.columns.tolist(), 1)
    if 'lod_activated' in request.POST and request.POST['lod_activated'] == 'true':
        lod = int(request.POST['lod_value'])
        lod_data = calc.lod_generator.LoDGenerator(numeric_dataset, lod)
        norm_lod_dataset = LocalReader().scaler(lod_data.grouped_dataset)
        aux_lod_dataset = lod_data.grouped_dataset.drop(lod_data.grouped_dataset.columns.tolist(), 1)
        op_history = calc.operationshistory.OperationHistory()
        metrics = calc.basicstatistics.BasicStatistics()
        metrics.process_data(norm_lod_dataset)
        op_history.append(norm_lod_dataset, metrics)
        data = prepare_data_object(norm_lod_dataset, lod_data.grouped_dataset, aux_lod_dataset, op_history)
        data['lod_data'] = lod_data.groups_metadata
        data['lod_value'] = request.POST['lod_value']
        data['lod_activated'] = True
        groupedData = calc.grouped.GroupedData()
        groupedData.get_groups(dataset, lod_data.groups_metadata)
        if 'fdid' in request.GET:
            fname = request.GET['fdid']
            groups = request.GET.getlist('group_id')
            for i in groups:
                fname += '_' + i
            fname += '_group'
            data['saveid'] = save_data(lod_data.grouped_dataset, norm_lod_dataset, aux_lod_dataset, op_history,
                                       str(lod), lod_data.groups_metadata, fname)
        else:
            data['saveid'] = save_data(lod_data.grouped_dataset, norm_lod_dataset, aux_lod_dataset, op_history,
                                       str(lod), lod_data.groups_metadata)
            fname = data['saveid'] + '_group'
        groupedData.set_fname(fname)
        groupedData.save_to_file()
    else:
        op_history = calc.operationshistory.OperationHistory()
        metrics = calc.basicstatistics.BasicStatistics()
        metrics.process_data(norm_dataset)
        op_history.append(norm_dataset, metrics)
        data = prepare_data_object(norm_dataset, numeric_dataset, auxiliary_dataset, op_history)
        if 'fdid' in request.GET:
            fname = request.GET['fdid']
            groups = request.GET.getlist('group_id')
            for i in groups:
                fname += '_' + i
            fname += '_group'
            data['saveid'] = save_data(numeric_dataset, norm_dataset, auxiliary_dataset, op_history, '0', '0', fname)
        else:
            data['saveid'] = save_data(numeric_dataset, norm_dataset, auxiliary_dataset, op_history, '0', '0')
    data['request'] = request
    return data

def file_upload(request, source, source_file=False, remote_data=False):
    """
    Upload file to server
    :param request:
    :param source: file | remote
    :return:
    """
    if source == 'file' and source_file:
        dest_path = os.path.join(settings.MEDIA_ROOT, source_file.name)
        with open(dest_path, 'wb+') as destination:
            for chunk in source_file.chunks():
                destination.write(chunk)
            destination.close()
        return source_file.name
    elif source == 'remote' and remote_data:
        if request.GET['remotesrc'] == 'pandajobs':
            fname = request.GET['remotesrc'] + '_' + request.GET['taskid'] + '.csv'
            dest_path = os.path.join(settings.MEDIA_ROOT, fname)
            df = pd.read_json(json.dumps(remote_data))
            df.set_index('pandaid', inplace=True)
            df.to_csv(dest_path)
            # with open(dest_path, 'w') as destination:
            #     json.dump(remote_data, destination)
            #     destination.close()
            return fname


def new_csv_file_upload(request):
    """
    Donwload CSV file from the remote location.
    :param request: 
    :return: 
    """
    if 'customFile' in request.FILES:
        try:
            return csv_file_from_server(request, file_upload(request=request,
                                                             source='file',
                                                             source_file=request.FILES['customFile'],
                                                             remote_data=False))
        except Exception as exc:
            logger.error('File upload error')
            raise

# def json_file_from_server(request, filename=False, index=False):
#     filepath = os.path.join(settings.MEDIA_ROOT, filename)
#     dataset = LocalReader().read_df(file_path=filepath, file_format='json')
#     if index:
#         dataset.set_index(index, inplace=True)
#     try:
#         fname = filename
#         data = {}
#         data['data_uploaded'] = True
#         data['features'] = []
#         dataset_stat = calc.dataset.DatasetInfo()
#         dataset_stat.get_info_from_dataset(dataset, ds_id=1,
#                                            ds_name=fname,
#                                            filepath=filepath)
#         for i in range(len(dataset_stat.features)):
#             data['features'].append(dataset_stat.features[i].__dict__)
#         data['ds_id'] = dataset_stat.ds_id
#         data['ds_name'] = dataset_stat.ds_name
#         data['filepath'] = dataset_stat.filepath
#         data['num_records'] = dataset_stat.num_records
#         data['index_name'] = dataset_stat.index_name
#         data['filename'] = fname
#         data['lod'] = False
#         data['lod_value'] = 50
#         return data
#     except Exception as exc:
#         logger.error(
#             '!form_reactions.csv_file_from_server!: Failed to prepare data after parsing the file. \nRequest.POST filename: '
#             + json.dumps(fname) + '\n' + str(exc))
#         raise


def csv_file_from_server(request, filename=False):
    """
    Download CSV file from server.
    :param request: 
    :return: 
    """
    list_of_files = list_csv_data_files(DATASET_FILES_PATH)
    dataset = None
    filepath = ''
    if ('filename' in request.POST) and (list_of_files is not None):
        for file in list_of_files:
            if request.POST['filename'] == file['value']:
                if os.path.isfile(DATASET_FILES_PATH + file['filename']):
                    filepath = DATASET_FILES_PATH + file['filename']
                    dataset = LocalReader().read_df(file_path=filepath, file_format='csv',index_col=0, header=0)
                    # dataset = calc.importcsv.import_csv_file(DATASET_FILES_PATH + file['filename'], True, True, False)
                else:
                    logger.error('!form_reactions.csv_file_from_server!: Failed to read file.\nFilename: ' +
                                 DATASET_FILES_PATH + file['filename'])
                    return {}
    elif filename:
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        dataset = LocalReader().read_df(file_path=filepath, file_format='csv',index_col=0, header=0)
        # dataset = calc.importcsv.import_csv_file(filepath, True, True, False)
    else:
        logger.error(
            '!form_reactions.csv_file_from_server!: Wrong request.\nRequest parameters: ' + json.dumps(request.POST))
        return {}
    if dataset is None:
        logger.error(
            '!form_reactions.csv_file_from_server!: Failed to get the dataset. \nRequest parameters: ' + json.dumps(
                request.POST))
        return {}
    try:
        fname = ''
        if ('filename' in request.POST):
            fname = request.POST['filename']
        else:
            fname = filename
        data = {}
        data['data_uploaded'] = True
        data['features'] = []
        dataset_stat = calc.dataset.DatasetInfo()
        dataset_stat.get_info_from_dataset(dataset, ds_id=1,
                                                ds_name=fname,
                                                filepath=filepath)
        for i in range(len(dataset_stat.features)):
            data['features'].append(dataset_stat.features[i].__dict__)
        data['ds_id'] = dataset_stat.ds_id
        data['ds_name'] = dataset_stat.ds_name
        data['filepath'] = dataset_stat.filepath
        data['num_records'] = dataset_stat.num_records
        data['index_name'] = dataset_stat.index_name
        data['filename'] = fname
        data['lod'] = False
        data['lod_value'] = 50
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.csv_file_from_server!: Failed to prepare data after parsing the file. \nRequest.POST filename: '
            + json.dumps(fname) + '\n' + str(exc))
        raise


def csv_test_file_from_server(request):
    """
    Download test CSV file from server.
    :param request: 
    :return: 
    """
    list_of_files = list_csv_data_files(TEST_DATASET_FILES_PATH)
    dataset = None
    if ('filename' in request.POST) and (list_of_files is not None):
        for file in list_of_files:
            if request.POST['filename'] == file['value']:
                if os.path.isfile(TEST_DATASET_FILES_PATH + file['filename']):
                    filename = file['filename']
                    dataset = calc.importcsv.import_csv_file(TEST_DATASET_FILES_PATH + file['filename'], True, True, False)
                else:
                    logger.error('!form_reactions.csv_test_file_from_server!: Could not read file.\n' +
                                 TEST_DATASET_FILES_PATH + file['filename'])
                    return {}
            else:
                logger.error('!form_reactions.csv_test_file_from_server!: File not found.\n' + TEST_DATASET_FILES_PATH
                             + request.POST['filename'] + '\nRequest: ' + json.dumps(request.POST))
                return {}
    else:
        logger.error('!form_reactions.csv_test_file_from_server!: Wrong request')
        return {}
    if dataset is None:
        logger.error('!form_reactions.csv_test_file_from_server!: Could not find file. \n' + json.dumps(request.POST)
                     + '\nFile name: ' + TEST_DATASET_FILES_PATH + filename)
        return {}
    try:
        return data_preparation(dataset, request)
    except Exception as exc:
        logger.error(
            '!form_reactions.csv_test_file_from_server!: Failed to prepare data after parsing the file. \nRequest.POST filename: '
            + json.dumps(request.POST['filename']) + '\n' + str(exc))
        raise


def update_dataset(request):
    dataset_stat = calc.dataset.DatasetInfo()
    dataset_stat.update_dataset_info(ds_id=request.POST['ds_id'],
                                     filepath=request.POST['filepath'],
                                     ds_name=request.POST['ds_name'],
                                     index_name=request.POST['index_name'],
                                     features=json.loads(request.POST['features']),
                                     num_records=request.POST['num_records'])

    use_col = []
    for item in dataset_stat.features:
        if item['enabled'] == 'true':
            use_col.append(item['feature_name'])
    use_col.append(dataset_stat.index_name)
    dataset = pd.DataFrame()
    if 'group_id' in request.GET:
        group = calc.grouped.GroupedData()
        dataset = group.load_from_file(int(request.GET['group_id']), request.POST['filepath'])
    else:
        reader = LocalReader()
        dataset = reader.read_df(dataset_stat.filepath, file_format='csv', index_col=0, header=0,usecols=use_col)
    data = data_preparation(dataset, request)
    data['filename'] = dataset_stat.ds_name
    data['data_uploaded'] = True
    data['features'] = dataset_stat.features
    data['ds_id'] = dataset_stat.ds_id
    data['ds_name'] = dataset_stat.ds_name
    data['filepath'] = dataset_stat.filepath
    data['num_records'] = dataset_stat.num_records
    data['index_name'] = dataset_stat.index_name
    data['lod'] = request.POST['lod_activated']
    data['lod_value'] = request.POST['lod_value']
    return data


def get_jobs_from_panda(request):
    """
    Get jobs data from PanDA system (by using providers.panda reader-client).

    :param request: HTTP [user] request.
    :type request: django.http.HttpRequest
    :return: Data for analysis (pre-processed by the preparation method).
    :rtype: dict
    """
    err_msg_subj = '[get_jobs_from_panda]'

    dataset = None
    if 'taskid' in request.GET:
        try:
            from .providers import PandaReader
        except ImportError as exc:
            logger.error('{0} {1}'.format(err_msg_subj, exc))
        else:
            filter_params = {}
            if 'days' in request.GET:
                filter_params['days'] = request.GET['days']
            else:
                filter_params['fulllist'] = 'true'
            data = PandaReader().get_jobs_data_by_task(task_id=request.GET['taskid'],
                                                       filter_params=filter_params)
    else:
        logger.error('{0} Request parameters are incorrect: {1}'.
                     format(err_msg_subj, json.dumps(request.GET)))

    if data is not None:
        try:
            return csv_file_from_server(request, file_upload(request=request,
                                                             source='remote',
                                                             source_file=False,
                                                             remote_data=data))
        except Exception as exc:
            logger.error('{0} Failed to prepare data: {1}'.
                         format(err_msg_subj, exc))
            # TODO: check that the raise of the Exception is needed.
            raise

    return data


def clusterize(request):
    """
    Implement clusterization.
    :param request: 
    :return: 
    """
    if 'fdid' not in request.POST:
        logger.error('!form_reactions.clusterize!: There was no file name in the request. \nRequest parameters: '
                     + json.dumps(request.POST))
        return {}
    original, dataset, op_history, aux_dataset, lod_value, lod_metadata = load_data(request.POST['fdid'])
    if dataset is None:
        return {}
    data = prepare_data_object(dataset, original, aux_dataset, op_history)
    if lod_value > 0:
        data['lod_data'] = lod_metadata
    data['request'] = request
    operation = None
    if 'algorithm' in request.POST:
        if request.POST['algorithm'] == 'KMeans' and 'numberofcl' in request.POST:
            try:
                operation = calc.KMeansClustering.KMeansClustering()
                operation.set_parameters(int(request.POST['numberofcl']))
                result = operation.process_data(dataset)
            except Exception as exc:
                logger.error(
                    '!form_reactions.clusterize!: Failed to perform KMean clusterization. \nRequest parameters: '
                    + json.dumps(request.POST) + '\n' + str(exc))
                raise
            if result is not None:
                try:
                    op_history.append(dataset, operation)
                    data['clusters'] = result.tolist()
                    data['count_of_clusters'] = int(request.POST['numberofcl'])
                    data['cluster_ready'] = True
                except Exception as exc:
                    logger.error(
                        '!form_reactions.clusterize!: Failed to perform KMean clusterization. \nOperation parameters:'
                        + json.dumps(operation.save_parameters()) + '\nOperation results: '
                        + json.dumps(operation.save_results()) + '\nRequest parameters: '
                        + json.dumps(request.POST) + '\n' + str(exc))
                    raise
            else:
                logger.error(
                    '!form_reactions.clusterize!: Failed to perform KMean clusterization. \nOperation parameters:'
                    + json.dumps(operation.save_parameters()) + '\nRequest parameters: ' + json.dumps(request.POST))
        elif request.POST['algorithm'] == 'DBSCAN' and 'min_samples' in request.POST and 'eps' in request.POST:
            try:
                operation = calc.DBScanClustering.DBScanClustering()
                operation.set_parameters(int(request.POST['min_samples']), float(request.POST['eps']))
                result = operation.process_data(dataset)
            except Exception as exc:
                logger.error(
                    '!form_reactions.clusterize!: Failed to perform DBScan clusterization. \nRequest parameters: '
                    + json.dumps(request.POST) + '\n' + str(exc))
                raise
            if result is not None:
                try:
                    op_history.append(dataset, operation)
                    data['clusters'] = result.tolist()
                    data['count_of_clusters'] = len(set(result.tolist()))
                    data['min_samples'] = int(request.POST['min_samples'])
                    data['eps'] = float(request.POST['eps'])
                    data['cluster_ready'] = True
                except Exception as exc:
                    logger.error(
                        '!form_reactions.clusterize!: Failed to perform DBScan clusterization. \nOperation parameters:'
                        + json.dumps(operation.save_parameters()) + '\nOperation results: '
                        + json.dumps(operation.save_results()) + '\nRequest parameters: '
                        + json.dumps(request.POST) + '\n' + str(exc))
                    raise
            else:
                logger.error(
                    '!form_reactions.clusterize!: Failed to perform DBScan clusterization. \nOperation parameters:'
                    + json.dumps(operation.save_parameters()) + '\nRequest parameters: ' + json.dumps(request.POST))
        else:
            logger.error('!form_reactions.clusterize!: The requested algorithm was not found. \nRequest parameters: '
                         + json.dumps(request.POST))
    else:
        logger.error('!form_reactions.clusterize!: The request was wrong. \nRequest parameters: ' + json.dumps(request.POST))
    data['saveid'] = save_data(original, dataset, aux_dataset, op_history, str(lod_value), lod_metadata, request.POST['fdid'])
    data['visualparameters'] = request.POST['visualparameters']
    data['algorithm'] = request.POST['algorithm']
    data['parameters'] = operation.print_parameters()
    data['filename'] = request.POST['fname']
    data['data_uploaded'] = True
    dataset_info = json.loads(request.POST['dataset_info'])
    data['ds_id'] = dataset_info['ds_id']
    data['ds_name'] = dataset_info['ds_name']
    data['filepath'] = dataset_info['filepath']
    data['num_records'] = dataset_info['num_records']
    data['index_name'] = dataset_info['index_name']
    data['features'] = dataset_info['features']
    data['lod'] = dataset_info['lod']
    data['lod_value'] = dataset_info['lod_value']

    return data


def predict_cluster(request):
    """
    Predict cluster for the data object. 
    :param request: 
    :return: 
    """
    if ('fdid' not in request.POST) or ('data' not in request.POST):
        logger.error('!form_reactions.predict_cluster!: There was no file name in the request. \nRequest parameters: '
                     + json.dumps(request.POST))
        return {}
    original, dataset, op_history, aux_dataset = load_data(request.POST['fdid'])
    if op_history is None:
        logger.error('!form_reactions.predict_cluster!: There was no operations in the history. \nRequest parameters: '
                     + json.dumps(request.POST))
        return {}
    data = {}
    operation = op_history.get_previous_step()[0]
    if operation._type_of_operation != 'cluster':
        logger.error(
            '!form_reactions.predict_cluster!: Previous operation was not a clusterization method. \nRequest parameters: '
            + json.dumps(request.POST))
        return {}
    try:
        result = operation.predict([json.loads(request.POST['data'])]).tolist()
        data['results'] = result
        data['clustertype'] = operation._operation_name
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.predict_cluster!: Failed to perform prediction. \nOperation parameters:'
            + json.dumps(operation.save_parameters()) + '\nOperation results: '
            + json.dumps(operation.save_results()) + '\nRequest parameters: '
            + json.dumps(request.POST) + '\n' + str(exc))
        raise

# SITE TO SITE VISUALIZATION FUNCTIONS
def read_site_to_site_json(filename):
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
            dataset = read_site_to_site_json(io.StringIO(request.FILES['customFile'].read().decode('utf-8')),
                                             True, True)
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
        # data['saveid'] = save_data(numeric_dataset, norm_dataset, auxiliary_dataset, op_history)
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.load_json_site_to_site!: Failed to prepare data after uploading from file. \n' + str(exc))
        raise


def read_group_data(request):
    group = calc.grouped.GroupedData()
    if request.method == 'POST':
        request_dict = dict(request.POST.items())
    elif request.method == 'GET':
        request_dict = dict(request.GET.items())
    fname = request_dict['fdid']
    groups = request.GET.getlist('group_id')
    for i in groups[:-1]:
        fname += '_' + i
    fname += '_group'
    dataset = group.load_from_file(int(groups[-1]), fname)
    data = {}
    data['data_uploaded'] = True
    data['features'] = []
    dataset_stat = calc.dataset.DatasetInfo()
    dataset_stat.get_info_from_dataset(dataset, ds_id=1,
                                       ds_name=fname,
                                       filepath=fname)
    for i in range(len(dataset_stat.features)):
        data['features'].append(dataset_stat.features[i].__dict__)
    data['ds_id'] = dataset_stat.ds_id
    data['ds_name'] = dataset_stat.ds_name
    data['filepath'] = dataset_stat.filepath
    data['num_records'] = dataset_stat.num_records
    data['index_name'] = dataset_stat.index_name
    data['filename'] = fname
    data['lod'] = False
    data['lod_value'] = 50
    return data

