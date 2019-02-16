"""
Module with class to work with PanDA as a remote source for jobs/tasks data
in JSON format.
"""

import json
import urllib.parse


try:
    import requests
    import urllib3
except ImportError:
    pass
else:
    urllib3.disable_warnings()

from ._basereader import BaseReader


class RemoteJSONReader(object):

    def __init__(self, base_url, verbose=False):
        """
        Initialization.

        :param base_url: Remote server base url (host:port/root_path).
        :type base_url: str
        :param verbose: Flag to get (show) logs.
        :type verbose: bool
        """
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        self.base_url = base_url
        self.verbose = verbose

        self.headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json'}

    def get(self, url_path, filter_params=None):
        """
        Get data from the defined url-path.

        :param url_path: Url path.
        :type url_path: str
        :param filter_params: Parameters to filter the request.
        :type filter_params: dict/None
        :return: JSON output from the defined url (base-url + path).
        :rtype: dict
        """
        output = {}

        if url_path.startswith('/'):
            url_path = url_path[1:]

        query_dict = filter_params or {}
        query_string = '&'.join(list(filter(
            lambda x: x,
            [urllib.parse.urlencode(query_dict).replace('%2C', ','), 'json'])))

        response = requests.get(
            url='{0}/{1}?{2}'.format(self.base_url, url_path, query_string),
            headers=self.headers,
            verify=False)
        # note: ignore verifying the SSL certificate (applies to host certs)

        if response.status_code == requests.codes.ok:
            output = json.loads(response.content)

            if self.verbose:
                print('Data is collected successfully | response code: {0}'.
                      format(response.status_code))
        else:
            err_message = ('Invalid HTTP response code: {0}'.
                           format(response.status_code))
            if self.verbose:
                print('[ERROR] {0}'.format(err_message))
            # raise Exception(err_message)

        return output


class PandaReader(RemoteJSONReader, BaseReader):

    BASE_URL = 'https://bigpanda.cern.ch'

    def __init__(self, verbose=False):
        """
        Initialization.

        :param verbose: Flag to get (show) logs.
        :type verbose: bool
        """
        super(PandaReader, self).__init__(base_url=self.BASE_URL,
                                          verbose=verbose)

    def get_task_data(self, task_id):
        """
        Get production task data.

        :param task_id: Task id.
        :type task_id: int
        :return: Task data.
        :rtype: dict
        """
        output = {}

        if task_id:
            output = self.get(url_path='task/{0}/'.format(task_id))

        return output

    def get_jobs_data_by_task(self, task_id, filter_params=None):
        """
        Get jobs data for the corresponding production task.

        :param task_id: Task id.
        :type task_id: int
        :param filter_params: Parameters to filter the request (e.g., days).
        :type filter_params: dict/None

        :return: Jobs data.
        :rtype: list
        """
        output = []

        if task_id:
            filter_params = dict(filter_params) or {}
            filter_params.update({'jeditaskid': task_id})
            output = self.get(url_path='jobs/',
                              filter_params=filter_params).get('jobs', [])

        return output

    def read_jobs_df(self, task_id, filter_params=None, **kwargs):
        """
        Read data of DataFrame format from the corresponding file.

        :param task_id: Task id.
        :type task_id: int
        :param filter_params: Parameters to filter the request (e.g., days).
        :type filter_params: dict/None
        :param kwargs: Additional parameters for DataFrame object.
        :type kwargs: dict

        :return: Data for analysis.
        :rtype: DataFrame
        """
        return self.to_df(
            data=self.get_jobs_data_by_task(
                task_id=task_id,
                filter_params=filter_params),
            **kwargs)
