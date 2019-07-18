from . import baseoperationclass

DEFAULT_PARAMETER1 = 5
DEFAULT_PARAMETER2 = 10


class OperationExample(baseoperationclass.BaseOperationClass):
    _operation_name = "OperationExample"

    def __init__(self):
        super().__init__()
        self.parameter1 = DEFAULT_PARAMETER1
        self.parameter2 = DEFAULT_PARAMETER2
        self.parameter3 = None
        self.results = None

    def set_parameters(self, parameter1, parameter2, parameter3):
        if parameter1 is not None:
            self.parameter1 = parameter1
        if parameter2 is not None:
            self.parameter2 = parameter2
        if parameter3 is not None:
            self.parameter3 = parameter3
        return True

    def load_parameters(self, parameters):
        if "parameter1" in parameters and parameters["parameter1"] is not None:
            self.parameter1 = parameters["parameter1"]
        else:
            self.parameter1 = DEFAULT_PARAMETER1

        if "parameter2" in parameters and parameters["parameter2"] is not None:
            self.parameter2 = parameters["parameter2"]
        else:
            self.parameter2 = DEFAULT_PARAMETER2

        # If parameter3 has to be defined, return False to fail the load_parameters function
        if "parameter3" in parameters and parameters["parameter3"] is not None:
            self.parameter3 = parameters["parameter3"]
        else:
            return False

        return True

    def process_data(self, dataset):
        # your code here, dataset is pandas.DataFrame
        # return True if the data analysis process went well.
        return True

    def save_parameters(self):
        return {'parameter1': self.parameter1, 'parameter2': self.parameter2, 'parameter3': self.parameter3}


try:
    baseoperationclass.register(OperationExample)  # Your class name here
except ValueError as error:
    print(repr(error))
