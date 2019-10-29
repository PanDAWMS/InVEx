from . import baseoperationclass
import numpy as np


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
        return True

    def get_parameters(self):
        return {'feature_name_GroupData': self.feature_name}

    def get_labels(self, data, reprocess=False):
        res = []
        grouped_data = data.groupby(self.feature_name)
        idx = data.index.tolist()
        for name, group in grouped_data:
            for i in group.index.tolist():
                try:
                    res.append([idx.index(i), name])
                except:
                    pass
        from operator import itemgetter
        res = np.array(sorted(res, key=itemgetter(0)))
        self.labels = res[:, 1]

        return self.labels

    # Legacy methods

    def print_parameters(self):
        return self.get_parameters()

    def save_parameters(self):
        return self.get_parameters()

    def load_parameters(self, parameters):
        self.set_parameters(feature_name=parameters.get('feature_name_GroupData') or None)
        return True

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
