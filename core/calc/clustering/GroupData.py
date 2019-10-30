
import numpy as np

from . import baseoperationclass


class GroupData(baseoperationclass.BaseOperationClass):

    _operation_name = 'Group Data'
    _operation_code_name = 'GroupData'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.feature_name = None
        self.labels = None

    def set_parameters(self, feature_name):
        if feature_name is not None:
            self.feature_name = feature_name

    def load_parameters(self, **kwargs):
        self.set_parameters(
            feature_name=kwargs.get('feature_name_GroupData'))

    def get_parameters(self):
        return {'feature_name_GroupData': self.feature_name}

    def get_labels(self, data, reprocess=False):
        self.labels = data[self.feature_name].values
        return self.labels

    # Legacy methods

    def print_parameters(self):
        return self.get_parameters()

    def save_parameters(self):
        return self.get_parameters()

    def save_results(self):
        return {'results': self.labels.tolist()}

    def load_results(self, results_dict):
        if 'results' in results_dict and results_dict['results'] is not None:
            self.labels = np.array(results_dict['results'])
        return True

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(GroupData)
except ValueError as error:
    print(repr(error))
