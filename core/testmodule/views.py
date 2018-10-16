"""
Django views for testmodule as an example of Django project structure
"""

from datetime import datetime
from django.shortcuts import render_to_response
from django.utils.cache import patch_response_headers
from core.views import initRequest

def testmodule(request):
    valid, response = initRequest(request)
    if not valid: return response

    data = {
            'request': request,
            'built': datetime.now().strftime("%H:%M:%S"),
            }

    response = render_to_response('testmodule.html', data, content_type='text/html')
    patch_response_headers(response, cache_timeout=request.session['max_age_minutes'] * 60)
    return response