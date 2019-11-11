"""
Class OperationHandler provides methods to deal with operations applied to
the analysis dataset sample.
"""

import json

import h5py
import numpy as np

from datetime import datetime

from ..clustering import baseoperationclass


class OperationHandler:

    def __init__(self, **kwargs):
        self.operation = None
        self.operations_count = 0
        self.use_normalized_dataset = False

        self.visual_parameters = None

        if 'operation' in kwargs:
            self.set(operation=kwargs['operation'],
                     use_normalized_dataset=kwargs.get(
                         'use_normalized_dataset', False),
                     visual_parameters=kwargs.get('visual_parameters'))

    def set(self, operation, use_normalized_dataset=False,
            visual_parameters=None):
        """
        Set operation for handling.

        :param operation: Analysis operation (clustering/grouping).
        :type operation: calc.clustering.baseoperationclass.BaseOperationClass
        :param use_normalized_dataset: Flag to use normalized dataset.
        :type use_normalized_dataset: bool
        :param visual_parameters: Camera parameters.
        :type visual_parameters: dict
        """
        self.operation = operation
        self.use_normalized_dataset = use_normalized_dataset
        if visual_parameters is not None:
            self.visual_parameters = visual_parameters

    def save_to_hdf5(self, root_group):
        """
        Add operation info to the HDF5 file.

        :param root_group: Group to which new operation will be attached.
        :type root_group: h5py.Group
        """
        if self.operation is not None:

            operation_group = root_group.create_group(
                'operation_{}'.format(root_group.attrs['operations_count']))
            operation_group.attrs['name'] = self.operation.operation_name
            operation_group.attrs['date'] = str(datetime.utcnow())
            operation_group.attrs['number_of_groups'] = len(
                set(self.operation.labels))
            operation_group.attrs['use_normalized_dataset'] = \
                self.use_normalized_dataset

            operation_group.attrs['operation_parameters'] = json.dumps(
                self.operation.get_parameters())
            operation_group.attrs['visual_parameters'] = json.dumps(
                self.visual_parameters)

            operation_group.create_dataset(
                name='operation_results',
                data=np.array(self.operation.labels).
                astype(h5py.special_dtype(vlen=str)))

            root_group.attrs['operations_count'] += 1
            self.operations_count = root_group.attrs['operations_count']

    def load_from_hdf5(self, root_group, operation_id):
        """
        Load operation info from HDF5 file.

        :param root_group: Group to which new operation will be attached.
        :type root_group: h5py.Group
        :param operation_id: Operation id.
        :type operation_id: int
        """
        self.operations_count = root_group.attrs['operations_count']

        if operation_id is None or operation_id >= self.operations_count:
            operation_id = self.operations_count - 1
        operation_group_name = f'operation_{operation_id}'

        operation_group = root_group.get(operation_group_name)
        if operation_group is None:
            raise Exception('[OperationHandler.load_from_hdf5] '
                            f'Operation "{operation_group_name}" is not found')

        self.set(operation=baseoperationclass.get_operation_class(
                 operation_group.attrs['name'])(),
                 use_normalized_dataset=bool(
                 operation_group.attrs['use_normalized_dataset']),
                 visual_parameters=json.loads(
                 operation_group.attrs['visual_parameters']))

        self.operation.load_parameters(**json.loads(
            operation_group.attrs['operation_parameters']))
        self.operation.labels = operation_group['operation_results'][()]