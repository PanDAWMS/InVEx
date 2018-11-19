"""
Basic methods to react to different forms
"""
from core import calc
import io
import os.path
from datetime import datetime
import pandas as pd
import json

SAVED_FILES_PATH = 'core/datafiles/'


def pandas_to_js_list(dataset):
    if dataset is None:
        return []
    else:
        results = []
        for i in range(len(dataset.index)):
            results.append([[dataset.index[i]], [dataset.values[i].tolist()]])
        return results


def save_data(original_dataset, norm_dataset, op_history):
    filename = str(datetime.now().timestamp())
    while os.path.isfile(SAVED_FILES_PATH + filename):
        filename = filename + 't'
    file = open(SAVED_FILES_PATH + filename, "w")
    file.write(original_dataset.to_json(orient='table'))
    file.write('\n')
    file.write(norm_dataset.to_json(orient='table'))
    file.write('\n')
    file.write(op_history.save_to_json())
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
    #original_dataset = pd.read_json(data, orient='table')
    data = file.readline()
    norm_dataset = table_to_df(data)
    # norm_dataset = pd.read_json(data, orient='table')
    data = file.readline()
    op_history = calc.operationshistory.OperationHistory()
    op_history.load_from_json(data)
    file.close()
    return [original_dataset, norm_dataset, op_history]


def prepare_basic(norm_dataset, real_dataset, op_history):
    idx = [norm_dataset.index.name]
    columns = norm_dataset.columns.tolist()
    dim_names = idx + columns

    metrics = calc.basicstatistics.BasicStatistics()
    met_numb_or = metrics.process_data(real_dataset)
    met_numb = []
    for i in range(len(met_numb_or)):
        met_numb.append(met_numb_or[i].tolist())
    data = {
        'norm_dataset': pandas_to_js_list(norm_dataset),
        'real_dataset': pandas_to_js_list(real_dataset),
        'dim_names': dim_names,
        'metrics': [calc.basicstatistics.DESCRIPTION, met_numb],
        'operation_history': op_history,
        'idx': idx,
    }
    return data


def new_csv_file_upload(request):
    if 'customFile' in request.FILES:
        dataset = calc.importcsv.import_csv_file(io.StringIO(request.FILES['customFile'].read().decode('utf-8')),
                                                 True,
                                                 True)
    else:
        return {}

    # get slice of data from the initial DataFrame
    slice = dataset.head(100)

    # create the copy of current data slice
    slice_copy = slice.copy()

    # clean data slice
    calc.importcsv.clean_dataset(slice)
    calc.importcsv.dropNA(slice)

    # get all columns, that left after cleaning
    columns = slice.columns.tolist()

    # normalization of the data slice
    norm_slice = calc.importcsv.normalization(slice, columns)

    # cleaning data after normalization
    calc.importcsv.dropNA(norm_slice)

    # get all columns, left after the second cleaning
    columns = norm_slice.columns.tolist()

    # reduce the initial data slice with columns, which were left after cleaning and normalization
    slice_copy = slice_copy.loc[:, columns]

    op_history = calc.operationshistory.OperationHistory()
    metrics = calc.basicstatistics.BasicStatistics()
    metrics.process_data(norm_slice)
    op_history.append(norm_slice, metrics)
    data = prepare_basic(norm_slice, slice_copy, op_history)
    data['request'] = request
    data['saveid'] = save_data(slice_copy, norm_slice, op_history)
    return data


def clusterize(request):
    if 'fdid' not in request.POST:
        return {}
    original, dataset, op_history = load_data(request.POST['fdid'])
    if dataset is None:
        return {}

    data = prepare_basic(dataset, original, op_history)
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
        else:
            print('unknown methond')
    else:
        print('No method')
    data['saveid'] = save_data(original, dataset, op_history)
    return data
