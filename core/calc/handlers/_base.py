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

    def _get_full_dir_name(self):
        """
        Form full directory name with dataset sample related data.

        :return: Full file name/path.
        :rtype: str
        """
        return os.path.join(settings.MEDIA_ROOT, '{}'.format(self._did))

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
