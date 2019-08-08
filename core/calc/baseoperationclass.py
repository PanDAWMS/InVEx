class BaseOperationClass:

    _operations_dictionary = {}
    _operation_name = 'Operation basis'
    _operation_code_name = 'OpBasic'
    # "operation_code_name" should correspond to html parameter "algorithm"

    def _get_name(self):
        return self._operation_name

    operation_name = property(_get_name)

    def __init__(self):
        self.results = None

    def save_to_queue(self, operation_queue, dataset):
        operation_queue.append(dataset, self)
        return True

    # All next functions are overloaded in classes
    def process_data(self, dataset):
        return None

    def save_parameters(self):
        return {}

    # Parameters is a collection of parameters
    def load_parameters(self, parameters):
        return True

    def save_results(self):
        return {'results': self.results}

    # results_dict is a collection of all the results got from previous
    def load_results(self, results_dict):
        if 'results' in results_dict and results_dict['results'] is not None:
            self.results = results_dict['results']
        return True

    def set_parameters(self, **kwargs):
        return True


def register(class_to_register):
    if class_to_register._operation_name in BaseOperationClass._operations_dictionary:
        raise ValueError('This class already registered', class_to_register, class_to_register._operation_name)
    BaseOperationClass._operations_dictionary[class_to_register._operation_name] = class_to_register
    return True


def get_operation_class(operation_name):
    if operation_name in BaseOperationClass._operations_dictionary:
        return BaseOperationClass._operations_dictionary[operation_name]
    else:
        return None


try:
    register(BaseOperationClass)
except ValueError as error:
    print(repr(error))
