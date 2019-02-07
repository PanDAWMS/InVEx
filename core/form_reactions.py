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
import logging

SAVED_FILES_PATH = BASE_DIR + '/datafiles/'
DATASET_FILES_PATH = BASE_DIR + '/datasets/'
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

def save_data(original_dataset, norm_dataset, auxiliary_dataset, op_history, filename=None):
    """
    Saving data to the operations history file.
    1st line - original dataset
    2nd line - normalized datasample
    3rd line - operations history (list of clusterizations)
    4th line - auxiliary data (not numeric values)
    :param original_dataset: 
    :param norm_dataset: 
    :param auxiliary_dataset: 
    :param op_history: 
    :param filename: 
    :return: 
    """
    if (filename is None):
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
        file.close()
        return [original_dataset, norm_dataset, op_history, aux_dataset]
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
        idx = [norm_dataset.index.name]
        columns = norm_dataset.columns.tolist()

        metrics = calc.basicstatistics.BasicStatistics()
        real_dataset_stats_or = metrics.process_data(real_dataset)
        real_dataset_stats = []
        for i in range(len(real_dataset_stats_or)):
            real_dataset_stats.append(real_dataset_stats_or[i].tolist())

        corr_matrix = real_dataset.corr()

        aux_columns = auxiliary_dataset.columns.tolist()

        data = {
            'norm_dataset': calc.data_converters.pandas_to_js_list(norm_dataset),
            'real_dataset': calc.data_converters.pandas_to_js_list(real_dataset),
            'aux_dataset': calc.data_converters.pandas_to_js_list(auxiliary_dataset),
            'data_is_ready':True,
            'dim_names': columns,
            'aux_names': aux_columns,
            'index': idx,
            'real_metrics': [calc.basicstatistics.DESCRIPTION, real_dataset_stats],
            'operation_history': op_history,
            'corr_matrix': corr_matrix.values.tolist()
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
    calc.importcsv.dropNA(dataset)
    numeric_columns = calc.importcsv.numeric_columns(dataset)
    numeric_dataset = dataset[numeric_columns]
    norm_dataset = calc.importcsv.normalization(numeric_dataset, numeric_columns)
    calc.importcsv.dropNA(norm_dataset)
    columns = norm_dataset.columns.tolist()
    numeric_dataset = numeric_dataset[columns]
    auxiliary_dataset = dataset.drop(numeric_columns, 1)
    if ('lod_value' in request.POST and request.POST['lod_value'] != ''):
        lod = int(request.POST['lod_value'])
        lod_data = calc.lod_generator.LoDGenerator(numeric_dataset, lod)
        norm_lod_dataset = calc.importcsv.normalization(lod_data.grouped_dataset, columns)
        aux_lod_dataset = lod_data.grouped_dataset.drop(columns, 1)
        op_history = calc.operationshistory.OperationHistory()
        metrics = calc.basicstatistics.BasicStatistics()
        metrics.process_data(norm_lod_dataset)
        op_history.append(norm_lod_dataset, metrics)
        data = prepare_data_object(norm_lod_dataset, lod_data.grouped_dataset, aux_lod_dataset, op_history)
        data['lod_data'] = lod_data.groups_metadata
        groupedData = calc.grouped.GroupedData(dataset, lod_data.groups_metadata)
        data['saveid'] = save_data(lod_data.grouped_dataset, norm_lod_dataset, aux_lod_dataset, op_history)
        groupedData.set_fname(SAVED_FILES_PATH + data['saveid'] + '_group')
        groupedData.save_to_file()
    else:
        op_history = calc.operationshistory.OperationHistory()
        metrics = calc.basicstatistics.BasicStatistics()
        metrics.process_data(norm_dataset)
        op_history.append(norm_dataset, metrics)
        data = prepare_data_object(norm_dataset, numeric_dataset, auxiliary_dataset, op_history)
        data['saveid'] = save_data(numeric_dataset, norm_dataset, auxiliary_dataset, op_history)
    data['request'] = request
    return data

def new_csv_file_upload(request):
    """
    Donwload CSV file from the remote location.
    :param request: 
    :return: 
    """
    if 'customFile' in request.FILES:
        try:
            dataset = calc.importcsv.import_csv_file(io.StringIO(request.FILES['customFile'].read().decode('utf-8')),
                                                     True, True)
        except Exception as exc:
            logger.error(
                '!form_reactions.new_csv_file_upload!: Failed to load data from the uploaded csv file. \n' + str(exc))
            raise
    else:
        logger.error('!form_reactions.new_csv_file_upload!: Failed to load data. There is no file to read.\nRequest: '
                     + json.dumps(request.POST))
        return {}
    try:
        data = data_preparation(dataset, request)
        data['filename'] = request.FILES['customFile']
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.new_csv_file_upload!: Failed to prepare data after uploading from file. \n' + str(exc))
        raise


def csv_file_from_server(request):
    """
    Download CSV file from server.
    :param request: 
    :return: 
    """
    list_of_files = list_csv_data_files(DATASET_FILES_PATH)
    dataset = None
    if ('filename' in request.POST) and (list_of_files is not None):
        for file in list_of_files:
            if request.POST['filename'] == file['value']:
                if os.path.isfile(DATASET_FILES_PATH + file['filename']):
                    dataset = calc.importcsv.import_csv_file(DATASET_FILES_PATH + file['filename'], True, True)
                else:
                    logger.error('!form_reactions.csv_file_from_server!: Failed to read file.\nFilename: ' +
                                 DATASET_FILES_PATH + file['filename'])
                    return {}
    else:
        logger.error('!form_reactions.csv_file_from_server!: Wrong request.\nRequest parameters: ' + json.dumps(request.POST))
        return {}
    if dataset is None:
        logger.error('!form_reactions.csv_file_from_server!: Failed to get the dataset. \nRequest parameters: ' + json.dumps(
            request.POST))
        return {}
    try:
        data = data_preparation(dataset, request)
        data['filename'] = request.POST['filename']
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.csv_file_from_server!: Failed to prepare data after parsing the file. \nRequest.POST filename: '
            + json.dumps(request.POST['filename']) + '\n' + str(exc))
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
                    dataset = calc.importcsv.import_csv_file(TEST_DATASET_FILES_PATH + file['filename'], True, True)
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
    original, dataset, op_history, aux_dataset = load_data(request.POST['fdid'])
    if dataset is None:
        return {}
    data = prepare_data_object(dataset, original, aux_dataset, op_history)
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
    data['saveid'] = save_data(original, dataset, aux_dataset, op_history, request.POST['fdid'])
    data['visualparameters'] = request.POST['visualparameters']
    data['algorithm'] = request.POST['algorithm']
    data['parameters'] = operation.print_parameters()
    data['filename'] = request.POST['fname']
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
    if (operation._type_of_operation != 'cluster'):
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
