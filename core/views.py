"""
Core Django views for VAR project
"""
import json
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.cache import patch_response_headers
import os
import pandas as pd
from django.shortcuts import render
from django.conf import settings


def initRequest(request):
    """
    A function to check and verify request
    :param request:
    :return:
    """

    url = request.get_full_path()
    u = urlparse(url)
    query = parse_qs(u.query)
    query.pop('timestamp', None)
    try:
        u = u._replace(query=urlencode(query, True))
    except UnicodeEncodeError:
        data = {
            'errormessage': 'Error appeared while encoding URL!'
        }
        return False, render_to_response(json.dumps(data), content_type='text/html')

    ## Set default page lifetime in the http header, for the use of the front end cache
    request.session['max_age_minutes'] = 10

    ## Create a dict in session for storing request params
    requestParams = {}
    request.session['requestParams'] = requestParams

    if request.method == 'POST':
        for p in request.POST:
            pval = request.POST[p]
            pval = pval.replace('+', ' ')
            request.session['requestParams'][p.lower()] = pval
    else:
        for p in request.GET:
            pval = request.GET[p]
            pval = pval.replace('+', ' ')

            ## Here check if int or date type params can be placed

            request.session['requestParams'][p.lower()] = pval

    return True, None


def main(request):
    valid, response = initRequest(request)

    if not valid: return response

    if request.method == 'POST':

        fpath = request.POST.get("customFile")
        file_path = settings.BASE_DIR + '/datasets/' + fpath
        dataset = load_csv(file_path, index='pandaid', column_names=True)

        # get index from DataFRame
        idx = [dataset.index.name]

        # get slice of data from the initial DataFrame
        slice = dataset.head(100)

        # create the copy of current data slice
        slice_copy = slice.copy()

        # clean data slice
        clean_dataset(slice)
        dropNA(slice)

        # get all columns, that left after cleaning
        columns = slice.columns.tolist()

        # normalization of the data slice
        norm_slice = normalization(slice, columns)

        # cleaning data after normalization
        dropNA(norm_slice)

        # get all columns, left after the second cleaning
        columns = norm_slice.columns.tolist()

        # reduce the initial data slice with columns, which were left after cleaning and normalization
        slice_copy = slice_copy.loc[:,columns]

        # get names of all dimensiona
        dim_names = idx + columns

        # get initial dataset statistics
        stats = slice_copy.describe()

        norm_slice = pandas_to_js_list(norm_slice)
        real_data_slice = pandas_to_js_list(slice_copy)
        stats_to_js = pandas_to_js_list(stats)

        data = {
            'built': datetime.now().strftime("%H:%M:%S"),
            'request': request.POST,
            'fpath': fpath,
            'new_file': True,
            'dim_names': dim_names,
            'norm_slice': norm_slice,
            'idx': idx,
            'real_data_slice': real_data_slice,
            'stats': stats_to_js
            }
    else:
        data = {
                'built': datetime.now().strftime("%H:%M:%S"),
                'dataset': [],
                'dim_names': [],
                'new_file': False,
                'norm_slice': [],
                'real_data_slice': [],
                'stats': []
                }
    return render(request, 'main.html', data, content_type='text/html')

def load_csv(path_to_file, index=False, column_names=False):
    if not os.path.exists(path_to_file):
        return None

    if column_names:
        column_names = 0
    else:
        column_names = None
    return pd.read_csv(path_to_file, index_col=index, header=column_names)

def pandas_to_js_list(dataset):
    results = []
    for i in range(len(dataset.index)):
        results.append([[dataset.index[i]], [dataset.values[i].tolist()]])
    return results

def normalization(df, cols_to_norm):
    return (df[cols_to_norm] - df[cols_to_norm].mean()) / (df[cols_to_norm].max() - df[cols_to_norm].min()) * 100

def clean_dataset(df):
    to_drop = []
    for item in df:
        if df[item].dtypes == 'object':
            to_drop.append(item)
    df.drop(to_drop, 1, inplace=True)
    df.drop('Unnamed: 0', 1, inplace=True)

def dropNA(df):
    df.dropna(axis=1, how='any', inplace=True)
    df.dropna(axis=0, how='any', inplace=True)