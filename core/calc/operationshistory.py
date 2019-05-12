from . import baseoperationclass
import json

OPERATION_NAME_STRING = "operationname"
OPERATION_PARAMETERS_STRING = "parameters"
OPERATION_RESULTS_STRING = "operationresults"
OPERATION_CAMERA_STRING = "caneraatm"


class OperationHistory:

    def __init__(self):
        self.stack = []
        pass

    def get_camera_parameters(self, number):
        try:
            return json.dumps(self.stack[number][2])
        except:
            return ''
    
    def length(self):
        return len(self.stack)

    def append(self, dataset, operation, camera=None):
        self.stack.append([operation, dataset, camera])
        return True

    def get_previous_step(self, step_number=1):
        if len(self.stack) < step_number:
            raise ValueError('Step number is larger than the number of operations saved', step_number, len(self.stack))
        if step_number < 1:
            raise ValueError('Step number must be greater or equal than 1')

    def get_step(self, step_number=None):
        if step_number is None:
            return self.stack[len(self.stack)-1]
        if len(self.stack) < step_number:
            raise ValueError('Step number is larger than the number of operations saved', step_number, len(self.stack))
        if step_number < 0:
            raise ValueError('Step number must be greater or equal than 0')

        return self.stack[step_number]

    def save_to_json(self):
        list_of_operations = []

        for i in range(len(self.stack)):
            list_of_operations.append({OPERATION_NAME_STRING: self.stack[i][0].operation_name,
                                       OPERATION_PARAMETERS_STRING: json.dumps(self.stack[i][0].save_parameters()),
                                       OPERATION_RESULTS_STRING: json.dumps(self.stack[i][0].save_results()),
                                       OPERATION_CAMERA_STRING: self.get_camera_parameters(i) })

        return json.dumps(list_of_operations)

    def load_from_json(self, json_string):
        list_of_operations = json.loads(json_string)

        for i in range(len(list_of_operations)):
            operation_class = baseoperationclass.get_operation_class(list_of_operations[i][OPERATION_NAME_STRING])
            if (OPERATION_CAMERA_STRING in list_of_operations[i]):
                camera = json.loads(list_of_operations[i][OPERATION_CAMERA_STRING])
            else:
                camera = ''
            if operation_class is None:
                print("Operation " + list_of_operations[i][OPERATION_NAME_STRING] +
                      " is not available. Please, check if all the operations were imported correctly")
            else:
                operation = operation_class()
                if operation.load_parameters(json.loads(list_of_operations[i][OPERATION_PARAMETERS_STRING])):
                    if operation.load_results(json.loads(list_of_operations[i][OPERATION_RESULTS_STRING])):
                        self.stack.append([operation, None, camera])
                    else:
                        print("Failed to load parameters", list_of_operations[i][OPERATION_RESULTS_STRING])
                else:
                    print("Failed to load parameters", list_of_operations[i][OPERATION_PARAMETERS_STRING])

        return True
