"""
Class BaseDataHandler is a base class for data handling.
"""

import errno
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseDataHandler:

    def __init__(self, did):
        """
        Initialization.

        :param did: Dataset sample id.
        :type did: int/str
        """
        self._did = str(did) or ''

    @staticmethod
    def _get_storage_dir_name():
        """
        Form full directory name with dataset samples.

        :return: Full directory name.
        :rtype: str
        """
        return settings.MEDIA_ROOT

    @staticmethod
    def _remove_file(file_name):
        """
        Remove file with provided full name/path.

        :param file_name: Full file name/path.
        :type file_name: str
        """
        try:
            os.remove(file_name)
        except OSError as e:
            # errno.ENOENT - no such file or directory
            if e.errno != errno.ENOENT:
                logger.error(
                    '[BaseDataHandler._remove_file] Failed to remove file '
                    '({}): {}'.format(file_name, e))
                # re-raise exception if a different error occurred
                raise
