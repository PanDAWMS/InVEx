"""
Core Django views for VAR project
"""
import json
import logging
from core import calc
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render_to_response
from django.utils.cache import patch_response_headers
import os
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from core import form_reactions
from django.template.context_processors import csrf

# Get an instance of a logger
logger = logging.getLogger(__name__)
EMPTY_DATA = data = {
            'dataset': [],
            'dim_names': [],
            'index': '',
            'new_file': False,
            'norm_dataset': [],
            'real_dataset': [],
            'filename': False,
            'visualparameters': False,
            'lod_data': False,
            'algorithm': False,
            'type': False,
            'xarray': False,
            'stats': [],
            'corr_matrix': [],
            'aux_dataset': [],
            'aux_names': []
        }

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
    if not valid:
        return response
    data = {}
    if request.method == 'POST' and 'formt' in request.POST:
        if request.POST['formt'] == 'newfile':
            try:
                data = form_reactions.new_csv_file_upload(request)
            except Exception as exc:
                logger.error(
                    '!views.performance_test_frame!: Couldn\'t perform an upload of a new CSV file. \n' + str(exc))
        elif request.POST['formt'] == 'filefromserver':
            try:
                data = form_reactions.csv_file_from_server(request)
            except Exception as exc:
                logger.error(
                    '!views.performance_test_frame!: Couldn\'t load the a CSV file from the server. \n' + str(exc))
        elif request.POST['formt'] == 'cluster':
            try:
                data = form_reactions.clusterize(request)
            except Exception as exc:
                logger.error('!views.performance_test_frame!: Couldn\'t perform a clusterization. \n' + str(exc))
        elif request.POST['formt'] == 'rebuild':
            try:
                data = form_reactions.predict_cluster(request)
                return JsonResponse(data)
            except Exception as exc:
                logger.error('!views.performance_test_frame!: Couldn\'t calculate a prediction. \n' + str(exc))
                return JsonResponse({})
        elif request.POST['formt'] == 'group_data':
            try:
                data = form_reactions.get_group_data(request)
                return JsonResponse(data)
            except Exception as exc:
                logger.error('!views.performance_test_frame!: Couldn\'t get the group. \n' + str(exc))
                return JsonResponse({})

    elif request.method == 'GET' and 'remotesrc' in request.GET:
        err_msg_subj = '[views/remotesrc=pandajobs]'

        if request.GET['remotesrc'] == 'pandajobs':
            try:
                data = form_reactions.get_jobs_from_panda(request)
            except Exception as exc:
                logger.error('{0} Remote data are not accessible: {1}'.
                             format(err_msg_subj, exc))

    else:
        data = EMPTY_DATA
        data['type'] = 'datavisualization'
    data['built'] = datetime.now().strftime("%H:%M:%S")
    data['PAGE_TITLE'] = "InVEx"
    try:
        data['dataset_files'] = form_reactions.list_csv_data_files(form_reactions.DATASET_FILES_PATH)
    except:
        data['dataset_files'] = False
        logger.error('Could not read the list of datasets file')
    return render(request, 'main.html', data, content_type='text/html')







def site_to_site(request):
    valid, response = initRequest(request)
    if not valid:
        return response
    data = {}
    if request.method == 'POST' and 'formt' in request.POST:
        if request.POST['formt'] == 'newfile':
            try:
                data = form_reactions.load_json_site_to_site(request)
            except Exception as exc:
                logger.error(
                    '!views.site_to_site!: Couldn\'t perform an upload of a new CSV file. \n' + str(exc))
        elif request.POST['formt'] == 'filefromserver':
            try:
                data = form_reactions.load_json_site_to_site(request)
            except Exception as exc:
                logger.error(
                    '!views.site_to_site!: Couldn\'t load the a CSV file from the server. \n' + str(exc))

    else:
        data = EMPTY_DATA
        data['type'] = 'site2site'
    data['built'] = datetime.now().strftime("%H:%M:%S")
    data['type'] = 'datavisualization'
    data['PAGE_TITLE'] = "InVEx"
    try:
        data['dataset_files'] = form_reactions.list_csv_data_files(form_reactions.SITE_SITE_DATASET_FILES_PATH)
    except:
        data['dataset_files'] = False
        logger.error('Could not read the list of datasets file')
    return render(request, 'mesh.html', data, content_type='text/html')





def performance_test(request):
    data = {}
    try:
        data['dataset_files'] = form_reactions.list_csv_data_files(form_reactions.TEST_DATASET_FILES_PATH)
    except:
        logger.error('Could not read the list of datasets file')
    return render(request, 'test.html', data, content_type='text/html')


def performance_test_frame(request):
    start_time = datetime.now()
    valid, response = initRequest(request)
    if not valid:
        return response

    if request.method == 'POST' and 'formt' in request.POST:
        if request.POST['formt'] == 'newfile':
            try:
                data = form_reactions.new_csv_file_upload(request)
            except Exception as exc:
                logger.error(
                    '!views.performance_test_frame!: Couldn\'t perform an upload of a new CSV file. ' + str(exc))
        if request.POST['formt'] == 'filefromserver':
            try:
                data = form_reactions.csv_test_file_from_server(request)
            except Exception as exc:
                logger.error(
                    '!views.performance_test_frame!: Couldn\'t load the a CSV file from the server. ' + str(exc))
        if request.POST['formt'] == 'cluster':
            try:
                data = form_reactions.clusterize(request)
            except Exception as exc:
                logger.error('!views.performance_test_frame!: Couldn\'t perform a clusterization. ' + str(exc))
        if request.POST['formt'] == 'rebuild':
            try:
                data = json.loads(form_reactions.predict_cluster(request))
                return JsonResponse(data)
            except Exception as exc:
                logger.error('!views.performance_test_frame!: Couldn\'t calculate a prediction. ' + str(exc))
                return JsonResponse({})

    else:
        data = {
            'dataset': [],
            'dim_names': [],
            'index': '',
            'new_file': False,
            'norm_dataset': [],
            'real_dataset': [],
            'stats': [],
            'corr_matrix': [],
            'aux_dataset': [],
            'aux_names': []
        }
    data['built'] = datetime.now().strftime("%H:%M:%S")
    try:
        data['dataset_files'] = form_reactions.list_csv_data_files(form_reactions.TEST_DATASET_FILES_PATH)
    except:
        logger.error('Could not read the list of datasets file')
    end_time = datetime.now()
    data['servertime'] = round((end_time - start_time).total_seconds() * 1000)
    return render(request, 'testframe.html', data, content_type='text/html')

def visualize_group(request):
    if request.method == 'GET' and 'group_id' in request.GET:
        group = form_reactions.get_group_data(request)
        data = form_reactions.data_preparation(calc.data_converters.table_to_df(group['group_data_df']), request)
        data['group_vis'] = True
        data['built'] = datetime.now().strftime("%H:%M:%S")
    return render(request, 'main.html', data, content_type="text/html")