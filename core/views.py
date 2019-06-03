"""
Core Django views for VAR project
"""
from datetime import datetime
import os, re, logging, json
from urllib.parse import urlencode, urlparse, parse_qs
from django.utils.cache import patch_response_headers
from django.shortcuts import render, reverse, render_to_response, redirect
from django.http import HttpResponse, JsonResponse
from django.template.context_processors import csrf
from django.conf import settings
import pandas as pd
from core import form_reactions
from core import calc

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


def parse_groups_url_parameter(groups):
    output = None

    if groups not in [None, '']:
        regex = re.compile('g/(?P<groupid>[0-9]+)/')
        output = regex.findall(groups) or None

    return output


def visualization_init(request):
    valid, response = initRequest(request)
    if not valid:
        return response
    data = EMPTY_DATA
    datasetid = None
    if request.method == 'POST' and 'formt' in request.POST:
        if request.POST['formt'] == 'newfile':
            try:
                data, datasetid = form_reactions.new_csv_file_upload(request)
            except Exception as exc:
                logger.error(
                    '!views.visualization_init!: Could not perform an upload of a new CSV file. \n' + str(exc))
        elif request.POST['formt'] == 'filefromserver':
            try:
                data, datasetid = form_reactions.csv_file_from_server(request)
            except Exception as exc:
                logger.error(
                    '!views.visualization_init!: Could not load the a CSV file from the server. \n' + str(exc))
    elif request.method == 'GET' and 'remotesrc' in request.GET:
        err_msg_subj = '[views/remotesrc=pandajobs]'
        if request.GET['remotesrc'] == 'pandajobs':
            try:
                data, datasetid = form_reactions.get_jobs_from_panda(request)
            except Exception as exc:
                logger.error('{0} Remote data are not accessible: {1}'.
                             format(err_msg_subj, exc))
    if not datasetid is None:
        return redirect(reverse('regular_visualization_data', kwargs={'maindatasetuid': datasetid, 'groups': ''}))
    data['type'] = 'datavisualization'
    data['built'] = datetime.now()
    data['PAGE_TITLE'] = "InVEx"
    try:
        data['dataset_files'] = form_reactions.list_csv_data_files(form_reactions.DATASET_FILES_PATH)
    except:
        data['dataset_files'] = False
        logger.error('Could not read the list of datasets file')
    return render(request, 'main.html', data, content_type='text/html')


def visualization_data(request, maindatasetuid,
                       groups=None, operationnumber=None):
    valid, response = initRequest(request)
    if not valid:
        return response

    parsed_groups = parse_groups_url_parameter(groups)
    if parsed_groups is None:
        groups = ''

    data = None
    if request.method == 'POST' and 'formt' in request.POST:
        if request.POST['formt'] == 'preview':
            try:
                data = form_reactions.update_dataset(request, maindatasetuid, parsed_groups)
            except Exception as exc:
                logger.error('!views.visualization_data!: Could not perform an update. \n' + str(exc))
        elif request.POST['formt'] == 'submit_feature_selection':
            err_msg_subj = '[views/formt=submit_feature_selection]'
            try:
                data = form_reactions.get_preprocessed_history_data(
                    maindatasetuid, parsed_groups)
            except Exception as exc:
                logger.error('{0} Error with preprocessed history data: {1}'.
                             format(err_msg_subj, exc))
        elif request.POST['formt'] == 'cluster':
            try:
                data, op_number = form_reactions.clusterize(request, maindatasetuid, parsed_groups)
                return redirect(reverse('regular_visualization_data_operation', kwargs={'maindatasetuid': maindatasetuid, 'groups': groups, 'operationnumber': str(op_number)}))
            except Exception as exc:
                logger.error('!views.visualization_data!: Could not perform a clusterization. \n' + str(exc))
        elif request.POST['formt'] == 'rebuild':
            try:
                data = form_reactions.predict_cluster(request)
                return JsonResponse(data)
            except Exception as exc:
                logger.error('!views.visualization_data!: Could not calculate a prediction. \n' + str(exc))
                return JsonResponse({})
    if data is None:
        data = form_reactions.prepare_dataset_data(request, maindatasetuid, parsed_groups, operationnumber)
    data['PREVIEW_URL'] = reverse('regular_visualization_data_new_group', kwargs={'maindatasetuid': maindatasetuid, 'groups': groups})
    data['NEXT_GROUP_URL'] = reverse('regular_visualization_data_new_group', kwargs={'maindatasetuid': maindatasetuid, "groups": groups})
    data['type'] = 'datavisualization'
    data['built'] = datetime.now()
    data['PAGE_TITLE'] = "InVEx"
    try:
        data['dataset_files'] = form_reactions.list_csv_data_files(form_reactions.DATASET_FILES_PATH)
    except:
        data['dataset_files'] = False
        logger.error('Could not read the list of datasets file')
    return render(request, 'main.html', data, content_type='text/html')


def main(request):
    valid, response = initRequest(request)
    if not valid:
        return response
    return redirect(reverse('regular_visualization_init'))


def site_to_site(request):
    valid, response = initRequest(request)
    if not valid:
        return response
    data = {}
    if ('benchmark' in request.GET and request.GET['benchmark']=='true'):
        startedat = datetime.now()
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
    data['built'] = datetime.now()
    data['PAGE_TITLE'] = "InVEx"
    if ('benchmark' in request.GET and request.GET['benchmark']=='true'):
        data['startedat'] = startedat
    else:
        data['startedat'] = False
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
    data['built'] = datetime.now()
    try:
        data['dataset_files'] = form_reactions.list_csv_data_files(form_reactions.TEST_DATASET_FILES_PATH)
    except:
        logger.error('Could not read the list of datasets file')
    end_time = datetime.now()
    data['servertime'] = round((end_time - start_time).total_seconds() * 1000)
    return render(request, 'testframe.html', data, content_type='text/html')

