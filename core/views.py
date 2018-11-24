"""
Core Django views for VAR project
"""
import json
import logging

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



# Get an instance of a logger
logger = logging.getLogger(__name__)


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

    if request.method == 'POST' and 'formt' in request.POST:
        if request.POST['formt'] == 'newfile':
            data = form_reactions.new_csv_file_upload(request)
        if request.POST['formt'] == 'cluster':
            data = form_reactions.clusterize(request)
        if request.POST['formt'] == 'rebuild':
            data = form_reactions.predict_cluster(request)
            return JsonResponse(data)

    else:
        data = {
                'dataset': [],
                'dim_names': [],
                'index': '',
                'new_file': False,
                'norm_dataset': [],
                'real_dataset': [],
                'stats': [],
                'corr_matrix': []
                }
    data['built'] = datetime.now().strftime("%H:%M:%S")
    return render(request, 'main.html', data, content_type='text/html')