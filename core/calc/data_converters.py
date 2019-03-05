import pandas as pd
import json


def pandas_to_js_list(dataset):
    """
    Convert pandas DataFrame to JavaScript-like array.
    :param dataset:
    :return:
    """
    if dataset is None:
        return []
    else:
        temp = dataset.values.tolist()
        results = []
        for i in range(len(dataset.index)):
            results.append([[str(dataset.index[i])], [temp[i]]])
        return results


def table_to_df(data):
    """
    Convert JSON data to pandas DataFrame.
    :param data:
    :return:
    """
    json_obj = json.loads(data)
    df = pd.DataFrame(json_obj['data'],
                      columns=[t['name'] for t in json_obj['schema']['fields']])
    for t in json_obj['schema']['fields']:
        if t['type'] == "datetime":
            df[t['name']] = pd.to_datetime(df[t['name']], infer_datetime_format=True)
    df.set_index(json_obj['schema']['primaryKey'], inplace=True)
    return df
