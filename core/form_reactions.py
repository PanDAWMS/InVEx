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

SAVED_FILES_PATH = BASE_DIR + '/datafiles/'
BACKUP_FILE = '_backup'


def pandas_to_js_list(dataset):
    if dataset is None:
        return []
    else:
        results = []
        for i in range(len(dataset.index)):
            results.append([[dataset.index[i]], [dataset.values[i].tolist()]])
        return results


def save_data(original_dataset, norm_dataset, auxiliary_dataset, op_history, filename=None):
    if (filename is None):
        filename = str(datetime.now().timestamp())
        while os.path.isfile(SAVED_FILES_PATH + filename):
            filename = filename + 't'
    else:
        if os.path.isfile(SAVED_FILES_PATH + filename + BACKUP_FILE):
            os.remove(SAVED_FILES_PATH + filename + BACKUP_FILE)
        if os.path.isfile(SAVED_FILES_PATH + filename):
            os.rename(SAVED_FILES_PATH + filename, SAVED_FILES_PATH + filename + BACKUP_FILE)
        if os.path.isfile(SAVED_FILES_PATH + filename):
            os.remove(SAVED_FILES_PATH + filename)

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


def table_to_df(data):
    json_obj = json.loads(data)
    df = pd.DataFrame(json_obj['data'],
                      columns=[t['name'] for t in json_obj['schema']['fields']])
    for t in json_obj['schema']['fields']:
        if t['type'] == "datetime":
            df[t['name']] = pd.to_datetime(df[t['name']], infer_datetime_format=True)
    df.set_index(json_obj['schema']['primaryKey'], inplace=True)
    return df


def load_data(filename):
    if not os.path.isfile(SAVED_FILES_PATH + filename):
        return [None, None]
    file = open(SAVED_FILES_PATH + filename, "r")
    data = file.readline()
    original_dataset = table_to_df(data)
    # original_dataset = pd.read_json(data, orient='table')
    data = file.readline()
    norm_dataset = table_to_df(data)
    # norm_dataset = pd.read_json(data, orient='table')
    data = file.readline()
    op_history = calc.operationshistory.OperationHistory()
    op_history.load_from_json(data)
    data = file.readline()
    aux_dataset = table_to_df(data)
    file.close()
    return [original_dataset, norm_dataset, op_history, aux_dataset]


def prepare_basic(norm_dataset, real_dataset, auxiliary_dataset, op_history):
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
        'norm_dataset': pandas_to_js_list(norm_dataset),
        'real_dataset': pandas_to_js_list(real_dataset),
        'aux_dataset': pandas_to_js_list(auxiliary_dataset),
        'dim_names': columns,
        'aux_names': aux_columns,
        'index': idx,
        'real_metrics': [calc.basicstatistics.DESCRIPTION, real_dataset_stats],
        'operation_history': op_history,
        'corr_matrix': corr_matrix.values.tolist()
    }
    return data


def new_csv_file_upload(request):
    if 'customFile' in request.FILES:
        dataset = calc.importcsv.import_csv_file(io.StringIO(request.FILES['customFile'].read().decode('utf-8')),
                                                 True,
                                                 True)
    else:
        return {}
    # drop all columns and rows with NaN values
    calc.importcsv.dropNA(dataset)
    numeric_columns = calc.importcsv.numeric_columns(dataset)
    numeric_dataset = dataset[numeric_columns]
    norm_dataset = calc.importcsv.normalization(numeric_dataset, numeric_columns)
    calc.importcsv.dropNA(norm_dataset)
    columns = norm_dataset.columns.tolist()
    numeric_dataset = numeric_dataset[columns]
    auxiliary_dataset = dataset.drop(numeric_columns, 1)
    op_history = calc.operationshistory.OperationHistory()
    metrics = calc.basicstatistics.BasicStatistics()
    metrics.process_data(norm_dataset)
    op_history.append(norm_dataset, metrics)
    data = prepare_basic(norm_dataset, numeric_dataset, auxiliary_dataset, op_history)
    data['request'] = request
    data['saveid'] = save_data(numeric_dataset, norm_dataset, auxiliary_dataset, op_history)
    return data


def clusterize(request):
    if 'fdid' not in request.POST:
        return {}
    original, dataset, op_history, aux_dataset = load_data(request.POST['fdid'])
    if dataset is None:
        return {}

    data = prepare_basic(dataset, original, aux_dataset, op_history)
    data['request'] = request
    if 'algorithm' in request.POST:
        if request.POST['algorithm'] == 'KMeans' and 'numberofcl' in request.POST:
            operation = calc.KMeansClustering.KMeansClustering()
            operation.set_parameters(int(request.POST['numberofcl']))
            result = operation.process_data(dataset)
            if result is not None:
                op_history.append(dataset, operation)
                data['clusters'] = result.tolist()
                data['count_of_clusters'] = int(request.POST['numberofcl'])
                data['cluster_ready'] = True
            else:
                print('couldn\'t clusterize')
        elif request.POST['algorithm'] == 'DBSCAN' and 'min_samples' in request.POST and 'eps' in request.POST:
            operation = calc.DBScanClustering.DBScanClustering()
            operation.set_parameters(int(request.POST['min_samples']), float(request.POST['eps']))
            result = operation.process_data(dataset)
            if result is not None:
                op_history.append(dataset, operation)
                data['clusters'] = result.tolist()
                data['count_of_clusters'] = len(set(result.tolist()))
                data['min_samples'] = int(request.POST['min_samples'])
                data['eps'] = float(request.POST['eps'])
                data['cluster_ready'] = True
            else:
                print('couldn\'t clusterize')
        else:
            print('unknown methond')
    else:
        print('No method')
    data['saveid'] = save_data(original, dataset, aux_dataset, op_history, request.POST['fdid'])
    data['visualparameters'] = request.POST['visualparameters']
    return data


# Here we have to implement prediction for point with updated coordinates
def predict_cluster(request):
    if ('fdid' not in request.POST) or ('data' not in request.POST):
        return {}
    original, dataset, op_history, aux_dataset = load_data(request.POST['fdid'])
    if op_history is None:
        return {}
    data = {}
    operation = op_history.get_previous_step()[0]
    if (operation._type_of_operation != 'cluster'):
        return {}
    result = operation.predict([json.loads(request.POST['data'])]).tolist()
    data['results'] = result
    data['clustertype'] = operation._operation_name
    return data
