from . import baseoperationclass
import numpy as np

GROUP_ARRAY = []


class GroupData(baseoperationclass.BaseOperationClass):

    _operation_name = 'Group Data'
    _operation_code_name = 'GroupData'
    _type_of_operation = 'grouping'

    def __init__(self):
        super().__init__()
        self.group_array = GROUP_ARRAY
        self.results = None

    def set_parameters(self, feature_name):
        if feature_name is not None:
            self.feature_name = feature_name
        return True

    def save_parameters(self):
        result = {'feature_name_GroupData': self.feature_name, 'group_array_GroupData': self.group_array}
        return result

    def load_parameters(self, parameters):
        if "feature_name_GroupData" in parameters and parameters["feature_name_GroupData"] is not None:
            self.feature_name = parameters["feature_name_GroupData"]

        if "group_array_GroupData" in parameters and parameters["group_array_GroupData"] is not None:
            self.group_array = parameters["group_array_GroupData"]
        else:
            self.group_array = GROUP_ARRAY
        return True

    def save_results(self):
        return {'results': self.results.tolist()}

    def load_results(self, results_dict):
        if 'results' in results_dict and results_dict['results'] is not None:
            self.results = np.array(results_dict['results'])
        return True

    def print_parameters(self):
        result = {'feature_name_GroupData': self.feature_name, 'group_array_GroupData': self.group_array}
        return result

    def process_data(self, dataset):
        res = []
        grouped_dataset = dataset.groupby(self.feature_name)
        idx = dataset.index.tolist()
        for name, group in grouped_dataset:
            for i in group.index.tolist():
                try:
                    res.append([idx.index(i), name])
                except:
                    pass
        from operator import itemgetter
        res = np.array(sorted(res, key=itemgetter(0)))
        self.results = res[:, 1]
        return self.results

try:
    baseoperationclass.register(GroupData)
except ValueError as error:
    print(repr(error))