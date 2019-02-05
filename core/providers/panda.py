"""
Client for local (inside the CERN network) execution (lightweight client).

Required installation: yum install cern-get-sso-cookie
"""

import json
import os
import urllib.parse

from ..utils import pyCMD

from ._basereader import BaseReader

SSO_COOKIE_DEFAULT = 'sso.cookie.txt'


class CERNSSOClient(object):

    GET_SSO_COOKIE_CMD = 'cern-get-sso-cookie'

    def __init__(self, base_url, cookie_file=None, verbose=False):
        """
        Initialization.

        :param base_url: Remote server base url (host:port/root_path).
        :type base_url: str
        :param cookie_file: File name for sso cookie.
        :type cookie_file: str/None
        :param verbose: Flag to get (show) logs.
        :type verbose: bool
        """
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        self.base_url = base_url
        self.cookie_file = cookie_file or SSO_COOKIE_DEFAULT
        self.verbose = verbose

        self.post_init()

    def post_init(self):
        """
        Post-initialization.
        """
        cmd_options = ['-u', self.base_url,
                       '-o', self.cookie_file]

        run_cmd = pyCMD(self.GET_SSO_COOKIE_CMD)
        run_cmd.set_options(*cmd_options)
        output = run_cmd.execute()

        if self.verbose:
            print('Code: {0} | Output: {1}'.format(output[0], output[1]))
            if output[2]:
                print('Error message: {0}'.format(output[2]))

    def clear(self):
        """
        Clear env and remove unwanted files (that were created by the instance).
        """
        try:
            os.remove(self.cookie_file)
        except OSError:
            pass

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

        cmd_options = ['-b', self.cookie_file,
                       '-H', "'Accept: application/json'",
                       '-H', "'Content-Type: application/json'",
                       '{0}/{1}?{2}'.format(
                           self.base_url, url_path, query_string)]

        run_cmd = pyCMD('curl')
        run_cmd.set_options(*cmd_options)
        _stdcode, _stdout, _stderr = run_cmd.execute()

        if self.verbose:
            print('Code: {0} | Output: {1}'.format(_stdcode, _stdout))
            if _stderr:
                print('Error message: {0}'.format(_stderr))

        if _stdout:
            output = json.loads(_stdout)

        return output


class PandaReader(CERNSSOClient, BaseReader):

    BASE_URL = 'https://bigpanda.cern.ch'
    COOKIE_FILE_NAME = 'bigpanda.cookie.txt'

    def __init__(self, verbose=False):
        """
        Initialization.

        :param verbose: Flag to get (show) logs.
        :type verbose: bool
        """
        super(PandaReader, self).__init__(base_url=self.BASE_URL,
                                          cookie_file=self.COOKIE_FILE_NAME,
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

    def get_jobs_data_by_task(self, task_id, **kwargs):
        """
        Get jobs data for the corresponding production task.

        :param task_id: Task id.
        :type task_id: int

        :keyword days: Number of days during which jobs were created.

        :return: Jobs data.
        :rtype: list
        """
        output = []

        if task_id:
            filter_params = dict(kwargs) or {}
            filter_params.update({'jeditaskid': task_id})
            output = self.get(url_path='jobs/',
                              filter_params=filter_params).get('jobs', [])

        return output

    def read_jobs_df(self, task_id, **kwargs):
        """
        Read data of DataFrame format from the corresponding file.

        :param task_id: Task id.
        :type task_id: int
        :param kwargs: Additional parameters.
        :type kwargs: dict

        :return: Data for analysis.
        :rtype: DataFrame
        """
        data = self.get_jobs_data_by_task(task_id=task_id, **kwargs)
        return self.to_df(data=data, **kwargs)
