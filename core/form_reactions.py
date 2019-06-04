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

DATASET_FILES_PATH = BASE_DIR + '/datasets/'
SITE_SITE_DATASET_FILES_PATH = BASE_DIR + '/site_site_datasets/'
TEST_DATASET_FILES_PATH = BASE_DIR + '/test_datasets/'
FILES_LIST_NAME = 'files_list.json'
BACKUP_FILE = '_backup'

LOD_VALUE_DEFAULT = 50
LOD_MODE_DEFAULT = 'minibatch'

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


def save_data(original_dataset, norm_dataset, auxiliary_dataset, op_history,
              selected_features, lod_metadata, datasetid, groups):
    """
    Saving data to the operations history file.
    1st line - original dataset
    2nd line - normalized dataset
    3rd line - auxiliary data (not numeric values)
    4th line - operations history (list of clusterizations)
    5th line - selected features
    6th line - Level-of-Detail Generator metadata
    """
    filename = datasetid
    if not groups is None:
        for i in groups:
            filename += '.group' + i
    dataset_storage = os.path.join(settings.MEDIA_ROOT, datasetid)
    history_file = os.path.join(dataset_storage, filename+'.history')
    if os.path.isdir(dataset_storage):
        if os.path.isfile(history_file):
            try:
                os.remove(history_file)
            except Exception as exc:
                logger.error('!form_reactions.save_data!: Failed to remove the history file. \nFilename:'
                             + history_file + '\n' + str(exc))
                raise
    try:
        file = open(history_file, "w")
        file.write(original_dataset.to_json(orient='table'))
        file.write('\n')
        file.write(norm_dataset.to_json(orient='table'))
        file.write('\n')
        file.write(auxiliary_dataset.to_json(orient='table'))
        file.write('\n')
        file.write(op_history.save_to_json())
        file.write('\n')
        file.write(json.dumps(selected_features or list(original_dataset.columns.values)))
        file.write('\n')
        file.write(json.dumps(lod_metadata))
        file.close()
    except Exception as exc:
        logger.error('!form_reactions.save_data!: Failed to save the data. \nFilename:'
                     + history_file + '\n' + str(exc))
        raise


def load_data(datasetid, groups=None, operation=None):
    """
    Loading data from the operations history file.
    The file is reading line by line:
    1st line - original dataset
    2nd line - normalized dataset
    3rd line - auxiliary data (not numeric values)
    4th line - operations history (list of clusterizations)
    5th line - selected features
    6th line - Level-of-Detail Generator metadata
    """
    filename = datasetid
    if groups is not None:
        for i in groups:
            filename += '.group' + i
    # history_file = get_history_file(dsID)
    dataset_storage = os.path.join(settings.MEDIA_ROOT, datasetid)
    history_file = os.path.join(dataset_storage, filename+'.history')
    if not os.path.isfile(history_file):
        logger.error('!form_reactions.load_data!: File is missing. Couldn\'t load the file. \nFilename:'
                     + history_file)
        return [None, None, None, None, None, None]
    try:
        file = open(history_file, "r")
        original_dataset = calc.data_converters.table_to_df(file.readline())
        norm_dataset = calc.data_converters.table_to_df(file.readline())
        aux_dataset = calc.data_converters.table_to_df(file.readline())
        op_history = calc.operationshistory.OperationHistory()
        op_history.load_from_json(file.readline())
        selected_features = json.loads(file.readline())
        lod_metadata = json.loads(file.readline())
        file.close()
        return [original_dataset, norm_dataset, aux_dataset, op_history,
                selected_features, lod_metadata]
    except Exception as exc:
        logger.error('!form_reactions.load_data!: Failed to load the data. \nFilename:'
                     + history_file + '\n' + str(exc))
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

def data_preparation(dataset, datasetid, features, lod_params=None, groups=None):
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
    :return:
    """
    LocalReader().drop_na(dataset)
    numeric_dataset = LocalReader().get_numeric_data(dataset)
    if lod_params:
        """
        Important!
        LoD needs all data sample (not only numeric) to process grouping
        by nominal categories. However, all these nominal values will be removed from
        groups and fixed as index names.
        """

        lod = calc.lod_generator.LoDGenerator(
            dataset, lod_params['mode'], lod_params['value'], lod_params['features'])
        norm_lod_dataset = LocalReader().scaler(lod.grouped_dataset)
        aux_lod_dataset = lod.grouped_dataset.drop(lod.grouped_dataset.columns.tolist(), 1)
        op_history = calc.operationshistory.OperationHistory()
        metrics = calc.basicstatistics.BasicStatistics()
        metrics.process_data(norm_lod_dataset)
        op_history.append(norm_lod_dataset, metrics)
        data = prepare_data_object(norm_lod_dataset, lod.grouped_dataset, aux_lod_dataset, op_history)
        data['lod_data'] = lod.get_groups_metadata()
        groupedData = calc.grouped.GroupedData()
        groupedData.get_groups(dataset.loc[:, features], lod.get_groups_metadata())
        filename = datasetid
        if not groups is None:
            for i in groups:
                filename += '.group' + i
        save_data(lod.grouped_dataset, norm_lod_dataset, aux_lod_dataset,
                  op_history, features, lod.get_full_metadata(),
                  datasetid, groups)
        groupedData.set_dsID(datasetid)
        groupedData.set_filename(filename)
        groupedData.save_to_file()
    else:
        numeric_features = list(set(list(numeric_dataset.columns.values)) &
                                set(features))
        numeric_dataset = numeric_dataset.loc[:, numeric_features]
        norm_dataset = LocalReader().scaler(numeric_dataset)
        auxiliary_dataset = dataset.drop(numeric_dataset.columns.tolist(), 1)
        op_history = calc.operationshistory.OperationHistory()
        metrics = calc.basicstatistics.BasicStatistics()
        metrics.process_data(norm_dataset)
        op_history.append(norm_dataset, metrics)
        data = prepare_data_object(norm_dataset, numeric_dataset, auxiliary_dataset, op_history)
        save_data(numeric_dataset, norm_dataset, auxiliary_dataset,
                  op_history, features, {}, datasetid, groups)
    return data

def file_upload(request, source, source_file=False, remote_data=False):
    """
    Upload file to server
    :param request:
    :param source: file | remote | server
    :return:
    """
    try:
        dsID = str(datetime.now().timestamp())
        dataset_storage = create_dataset_storage(dsID)
        dest_path = os.path.join(dataset_storage, dsID+'.csv')
        if source == 'file' and source_file:
            with open(dest_path, 'wb+') as destination:
                for chunk in source_file.chunks():
                    destination.write(chunk)
                destination.close()
        elif source == 'remote' and remote_data:
            if request.GET['remotesrc'] == 'pandajobs':
                df = pd.read_json(json.dumps(remote_data))
                df.set_index('pandaid', inplace=True)
                df.to_csv(dest_path)
        elif source == 'server':
            remote_data.to_csv(dest_path)
        return dsID
    except Exception as exc:
        logger.error('File_upload error: \n' + str(exc))

def create_dataset_storage(dsID):

    path = os.path.join(settings.MEDIA_ROOT, dsID)
    try:
        os.mkdir(path)
        return path
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)


def get_dataset_path(dsID):
    return os.path.join(settings.MEDIA_ROOT, dsID, dsID+'.csv')

def get_history_path(dsID):
    return os.path.join(settings.MEDIA_ROOT, dsID, dsID + '.history')

def get_groups_path(dsID):
    return os.path.join(settings.MEDIA_ROOT, dsID, dsID + '.groups')

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


def csv_file_from_server(request, dsID=False):
    """
    Download CSV file from server as Pandas DataFrame.
    Collect dataset statistics.
    :param request: 
    :return: 
    """
    list_of_files = list_csv_data_files(DATASET_FILES_PATH)
    dataset = pd.DataFrame()
    if ('filename' in request.POST) and (list_of_files is not None):
        for file in list_of_files:
            if request.POST['filename'] == file['value']:
                if os.path.isfile(DATASET_FILES_PATH + file['filename']):
                    filepath = DATASET_FILES_PATH + file['filename']
                    dataset = LocalReader().read_df(file_path=filepath, file_format='csv',index_col=0, header=0)
                    dsID = file_upload(request=request, source='server',source_file=False, remote_data=dataset)
                else:
                    logger.error('!form_reactions.csv_file_from_server!: Failed to read file.\nFilename: ' +
                                 DATASET_FILES_PATH + file['filename'])
                    return {}
    elif dsID:
        filepath = os.path.join(settings.MEDIA_ROOT, dsID, dsID+'.csv')
        dataset = LocalReader().read_df(file_path=filepath, file_format='csv',index_col=0, header=0)
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
        data = {}
        data['data_uploaded'] = True
        data['features'] = []
        dataset_stat = calc.dataset.DatasetInfo()
        dataset_stat.get_info_from_dataset(dataset, dsID)
        dataset_stat.save_to_file()
        for i in range(len(dataset_stat.features)):
            data['features'].append(dataset_stat.features[i].__dict__)
        data['dsID'] = dataset_stat.dsID
        data['num_records'] = dataset_stat.num_records
        data['index_name'] = dataset_stat.index_name
        data['lod_activated'] = False
        data['lod_value'] = LOD_VALUE_DEFAULT
        return data, dsID
    except Exception as exc:
        logger.error(
            '!form_reactions.csv_file_from_server!: Failed to prepare data after parsing the file. \nRequest.POST filename: '
            + json.dumps(dsID) + '\n' + str(exc))
        raise


def load_dataset(datasetid, groups=None, usecols=None):
    if groups is not None:
        filename = datasetid
        for i in groups[:-1]:
            filename += '.group' + i
        filename += '.groups'
        group = calc.grouped.GroupedData()
        group.set_dsID(datasetid)
        group.set_filename(filename)
        dataset = group.load_from_file(int(groups[-1]))
    else:
        dataset = LocalReader().read_df(file_path=get_dataset_path(datasetid),
                                        file_format='csv',
                                        **{'index_col': 0,
                                           'header': 0,
                                           'usecols': usecols})
    return dataset


def prepare_data_for_operation(request, datasetid, groups=None, operationnumber=None):
    original, dataset, aux_dataset, op_history, features, lod_metadata = \
        load_data(datasetid, groups)

    if dataset is None or operationnumber is None:
        return prepare_dataset_data(datasetid, groups, None)
    try:
        operationnumber = int(operationnumber)
    except:
        return prepare_dataset_data(datasetid, groups, None)
    if operationnumber >= op_history.length():
        operationnumber = op_history.length() - 1
    oper = op_history.get_step(operationnumber)
    if oper[0]._type_of_operation != 'cluster':
        return prepare_dataset_data(datasetid, groups, None)
    data = prepare_data_object(dataset, original, aux_dataset, op_history)
    if lod_metadata.get('value', 0) > 0:
        data['lod_activated'] = 'true'
        data['lod_mode'] = lod_metadata['mode']
        data['lod_value'] = lod_metadata['value']
        data['lod_data'] = lod_metadata['groups']
    else:
        data['lod_activated'] = 'false'
        data['lod_value'] = LOD_VALUE_DEFAULT
        data['lod_mode'] = LOD_MODE_DEFAULT
    lod_features = lod_metadata.get('features', [])
    if len(oper) >= 3:
        data['visualparameters'] = oper[2]
    data['parameters'] = oper[0].print_parameters()
    numeric_features = list(set(features) & set(list(dataset.columns.values)))
    result = oper[0].predict(dataset.loc[:, numeric_features])
    data['data_uploaded'] = True
    data['data_is_ready'] = True
    data['clusters'] = result.tolist()
    data['count_of_clusters'] = len(set(data['clusters']))
    data['cluster_ready'] = True
    data['dsID'] = datasetid
    data['features'] = []
    dataset_stat = calc.dataset.DatasetInfo()
    dataset_stat.get_info_from_dataset(original, datasetid)
    for i in range(len(dataset_stat.features)):
        data['features'].append(dataset_stat.features[i].__dict__)
        if data['features'][-1]['feature_name'] in features:
            data['features'][-1]['enabled'] = 'true'
        else:
            data['features'][-1]['enabled'] = 'false'
        if data['features'][-1]['feature_name'] in lod_features:
            data['features'][-1]['lod_enabled'] = 'true'
    data['dsID'] = dataset_stat.dsID
    data['num_records'] = dataset_stat.num_records
    data['index_name'] = dataset_stat.index_name
    return data
    

def prepare_dataset_data(request, datasetid, groups=None, operationnumber=None):
    if operationnumber is not None:
        return prepare_data_for_operation(request, datasetid, groups, operationnumber)
    dataset = load_dataset(datasetid, groups)
    try:
        data = {}
        data['data_uploaded'] = True
        data['features'] = []
        dataset_stat = calc.dataset.DatasetInfo()
        dataset_stat.get_info_from_dataset(dataset, datasetid)
        for i in range(len(dataset_stat.features)):
            data['features'].append(dataset_stat.features[i].__dict__)
        data['dsID'] = dataset_stat.dsID
        data['num_records'] = dataset_stat.num_records
        data['index_name'] = dataset_stat.index_name
        data['lod_activated'] = False
        data['lod_value'] = LOD_VALUE_DEFAULT
        data['lod_mode'] = LOD_MODE_DEFAULT
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.csv_file_from_server!: Failed to prepare data after parsing the file. \nRequest.POST filename: '
            + json.dumps(datasetid) + '\n' + str(exc))
        raise


def update_dataset(request, datasetid, groups=None):
    dataset_info = calc.dataset.DatasetInfo()
    dataset_info.update_dataset_info(dsID=datasetid,
                                     index_name=request.POST['index_name'],
                                     features=json.loads(request.POST['features']),
                                     num_records=request.POST['num_records'])

    features, lod_features = [], []
    for feature in dataset_info.features:
        if feature['enabled'] == 'true':
            features.append(feature['feature_name'])
        if feature.get('lod_enabled') == 'true':
            lod_features.append(feature['feature_name'])
    checked_features = list(set(
        [dataset_info.index_name] + features + lod_features))

    lod_params = None
    if request.POST.get('lod_activated') == 'true':
        lod_params = {'mode': request.POST['lod_mode'],
                      'value': int(request.POST['lod_value']),
                      'features': lod_features}

    dataset = load_dataset(datasetid, groups, checked_features)
    data = data_preparation(dataset, datasetid, features, lod_params, groups)
    data.update({'dsID': datasetid,
                 'data_uploaded': True,
                 'data_is_ready': False,
                 'features': dataset_info.features,
                 'num_records': dataset_info.num_records,
                 'index_name': dataset_info.index_name,
                 'lod_activated': request.POST['lod_activated'],
                 'lod_mode': request.POST['lod_mode'],
                 'lod_value': request.POST['lod_value'],
                 'request': request})

    return data


def get_preprocessed_history_data(dataset_id, groups=None):
    original, dataset, aux_dataset, op_history, features, lod_metadata = \
        load_data(dataset_id, groups)

    data = prepare_data_object(dataset, original, aux_dataset, op_history)
    data.update({'dsID': dataset_id,
                 'data_uploaded': True,
                 'data_is_ready': True,
                 'features': []})

    dataset_info = calc.dataset.DatasetInfo()
    dataset_info.get_info_from_dataset(dataset, dataset_id)
    data.update({'num_records': dataset_info.num_records,
                 'index_name': dataset_info.index_name})
    lod_features = lod_metadata.get('features', [])
    for i in range(len(dataset_info.features)):
        f = dataset_info.features[i].__dict__
        f['enabled'] = 'true' if f['feature_name'] in features else 'false'
        if f['feature_name'] in lod_features:
            f['lod_enabled'] = 'true'
        data['features'].append(f)

    if lod_metadata.get('value', 0) > 0:
        data.update({'lod_activated': 'true',
                     'lod_mode': lod_metadata['mode'],
                     'lod_value': lod_metadata['value'],
                     'lod_data': lod_metadata['groups']})
    else:
        data.update({'lod_activated': 'false',
                     'lod_mode': LOD_MODE_DEFAULT,
                     'lod_value': LOD_VALUE_DEFAULT})

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


def clusterize(request, datasetid, groups):
    """
    Implement clusterization.
    :param request: 
    :return: 
    """
    original, dataset, aux_dataset, op_history, features, lod_metadata = \
        load_data(datasetid, groups)
    numeric_features = list(set(features) & set(list(dataset.columns.values)))

    if dataset is None:
        return {}
    data = prepare_data_object(dataset, original, aux_dataset, op_history)
    if lod_metadata.get('value', 0) > 0:
        data['lod_activated'] = 'true'
        data['lod_value'] = lod_metadata['value']
        data['lod_data'] = lod_metadata['groups']
    else:
        data['lod_activated'] = 'false'
        data['lod_value'] = LOD_VALUE_DEFAULT
    data['request'] = request
    operation = None
    if 'algorithm' in request.POST:
        if request.POST['algorithm'] == 'KMeans' and 'numberofcl' in request.POST:
            try:
                operation = calc.KMeansClustering.KMeansClustering()
                operation.set_parameters(int(request.POST['numberofcl']))
                result = operation.process_data(dataset.loc[:, numeric_features])
            except Exception as exc:
                logger.error(
                    '!form_reactions.clusterize!: Failed to perform KMean clusterization. \nRequest parameters: '
                    + json.dumps(request.POST) + '\nDataset: '+ dataset.to_json(orient='table') + '\n' + str(exc))
                raise
            if result is not None:
                try:
                    op_history.append(dataset.loc[:, numeric_features], operation, request.POST['visualparameters'])
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
                result = operation.process_data(dataset.loc[:, numeric_features])
            except Exception as exc:
                logger.error(
                    '!form_reactions.clusterize!: Failed to perform DBScan clusterization. \nRequest parameters: '
                    + json.dumps(request.POST) + '\n' + str(exc))
                raise
            if result is not None:
                try:
                    op_history.append(dataset.loc[:, numeric_features], operation, request.POST['visualparameters'])
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
    save_data(original, dataset, aux_dataset, op_history,
              features, lod_metadata, datasetid, groups)
    data['visualparameters'] = request.POST['visualparameters']
    data['algorithm'] = request.POST['algorithm']
    data['parameters'] = operation.print_parameters()
    data['data_uploaded'] = True
    dataset_info = json.loads(request.POST['dataset_info'])
    data['dsID'] = datasetid
    data['num_records'] = dataset_info['num_records']
    data['index_name'] = dataset_info['index_name']
    data['features'] = dataset_info['features']

    return data, op_history.length()-1


def predict_cluster(request, datasetid, groups, operationnumber):
    """
    Predict cluster for the data object. 
    :param request: 
    :return: 
    """
    if 'data' not in request.POST:
        logger.error('!form_reactions.predict_cluster!: There was no data in the request. \nRequest parameters: '
                     + json.dumps(request.POST))
        return {}

    original, dataset, aux_dataset, op_history, features, lod_metadata = \
        load_data(datasetid, groups)

    if dataset is None or operationnumber is None or op_history is None:
        logger.error('!form_reactions.predict_cluster!: Could not load the dataset or the operation history. \nDatasetid: '+
            datasetid + '\ngroups:' + groups + '\nRequest parameters: ' + json.dumps(request.POST))
        return {}
    try:
        operationnumber = int(operationnumber)
    except:
        logger.error('!form_reactions.predict_cluster!: Could not convert operation number to int. \nDatasetid: '+
            datasetid + '\ngroups:' + groups + '\nOperation number: ' + operationnumber + '\nRequest parameters: ' + json.dumps(request.POST))
        return {}
    if operationnumber >= op_history.length():
        operationnumber = op_history.length() - 1
    
    data = {}
    operation = op_history.get_step(operationnumber)[0]
    if operation._type_of_operation != 'cluster':
        logger.error(
            '!form_reactions.predict_cluster!: Previous operation was not a clusterization method. \nDatasetid: '+
            datasetid + '\ngroups:' + groups + '\nOperation number: ' + operationnumber + '\nRequest parameters: ' + json.dumps(request.POST))
        return {}
    try:
        result = operation.predict([json.loads(request.POST['data'])]).tolist()
        data['results'] = result
        data['clustertype'] = operation._operation_name
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.predict_cluster!: Failed to perform prediction. \nDatasetid: '+
            datasetid + '\ngroups:' + groups + '\nOperation number: ' + operationnumber +
            '\nOperation parameters:' + json.dumps(operation.save_parameters()) + '\nOperation results: '
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
        return data
    except Exception as exc:
        logger.error(
            '!form_reactions.load_json_site_to_site!: Failed to prepare data after uploading from file. \n' + str(exc))
        raise
