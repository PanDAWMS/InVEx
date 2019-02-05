#
# Copyright European Organization for Nuclear Research (CERN),
#           National Research Centre "Kurchatov Institute" (NRC KI)
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Mikhail Titov, <mikhail.titov@cern.ch>, 2017-2018
#

from subprocess import Popen, PIPE


class SimpleCMDWrapper(object):

    _command = None
    _options = None
    _process = None

    def __init__(self, command, options=None, **kwargs):
        """
        Initialization.
        
        @param command: Command name.
        @type command: str
        @param options: List of options/parameters.
        @type options: list
        
        @keyword stdin: Standard input.
        @keyword stdout: Standard output.
        @keyword stderr: Standard error.
        """
        self._command = command
        self._options = []
        if options and isinstance(options, (list, tuple)):
            self._options = list(options)

        self.stdin = kwargs.get('stdin')
        self.stdout = kwargs.get('stdout', PIPE)
        self.stderr = kwargs.get('stderr', PIPE)

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        if self._process is not None:
            self._process.terminate()
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.traceback = traceback

    def __call__(self, stdin=None):
        """
        Call class object.

        @param stdin: Standard input.
        @return: Result from self.execute()
        """
        self.stdin = stdin
        return self.execute()

    @property
    def command(self):
        """
        Get command with options.
        
        @return: List of command with options.
        @rtype: list
        """
        return [self._command] + self._options

    def reset_options(self):
        """
        Remove defined options.
        """
        del self._options[:]

    def set_options(self, *args, **kwargs):
        """
        Set new options.

        @param args: List of keys.
        @type args: list
        @param kwargs: Dict of options.
        @type kwargs: dict
        """
        self.reset_options()
        self.add_options(*args, **kwargs)

    def add_option(self, key, value=None):
        """
        Add command option (e.g., key/value pair).
        
        @param key: Key name.
        @type key: str
        @param value: Key value.
        @type value: str
        """
        self._options.append(key)
        if value:
            self._options.append(value)

    def add_options(self, *args, **kwargs):
        """
        Add command options.

        @param args: List of keys.
        @type args: list
        @param kwargs: Dict of options.
        @type kwargs: dict
        """
        for option in args:
            if isinstance(option, (list, tuple)) and len(option) > 1:
                self.add_option(key=option[0], value=option[1])
            else:
                self.add_option(key=option)
        for (key, value) in kwargs.iteritems():
            self.add_option(key=key, value=value)

    def execute(self):
        """
        Execute CLI command.
        @return: Return code, output data, error message.
        @rtype: tuple
        """
        self._process = Popen([self._command] + self._options,
                              shell=False,
                              stdin=self.stdin,
                              stdout=self.stdout,
                              stderr=self.stderr)
        (stdoutdata, stderrdata) = self._process.communicate(self.stdin)
        returncode = self._process.returncode
        return returncode, stdoutdata, stderrdata
