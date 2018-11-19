from calc import operationshistory
from calc import basicstatistics
from calc import operationexample
import pandas as pd

DATASETS_STRING = 'datasets'
TESTOP_STRING = 'testoperations'
OPER_STRING = 'operation'
PARAM_STRING = 'parameters'
RES_STRING = 'results'
CHECKF_STRING = 'checkfunction'


def isclose(a, b, rel_tol=1e-04, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def check_arrays(arr1, arr2):
    for i in range(len(arr1)):
        for j in range(len(arr1[i])):
            if not isclose(arr1[i][j], arr2[i][j]):
                return False
    return True


def check_basic_stats(operation, dataset, result):
    calculation_result = operation.process_data(dataset)
    return check_arrays(result, calculation_result)


def check_operation_example(operation, dataset, result):
    return (operation.parameter1 == result[0]) and (operation.parameter2 == result[1]) and (
            operation.parameter3 == result[2]) and operation.process_data(None)


def run():
    testset = {DATASETS_STRING: [pd.DataFrame(
        [[7, 1, 3, 3], [6, 4, 8, 9], [1, 1, 0, 8], [6, 2, 0, 4], [2, 4, 2, 2], [7, 9, 2, 3], [9, 7, 7, 2],
         [5, 9, 8, 10]]), None,
        pd.DataFrame([[1, 2, 3, 4], [4, 3, 2, 1], [-1, -2, -3, -4], [0, 0, 0, 0], [0, 0, 0, 0]]), None],
        TESTOP_STRING: [{OPER_STRING: basicstatistics.BasicStatistics, PARAM_STRING: {},
                         RES_STRING: [[1, 1, 0, 2], [4.25, 1.75, 1.5, 2.75], [6.0, 4.0, 2.5, 3.5],
                                      [7.0, 7.5, 7.25, 8.25], [9, 9, 8, 10], [43, 37, 30, 41],
                                      [2.66927, 3.33542, 3.41216, 3.31393]],
                         CHECKF_STRING: check_basic_stats},
                        {OPER_STRING: operationexample.OperationExample,
                         PARAM_STRING: {"parameter1": 1, "parameter2": 2, "parameter3": 3},
                         RES_STRING: [1, 2, 3],
                         CHECKF_STRING: check_operation_example},
                        {OPER_STRING: basicstatistics.BasicStatistics, PARAM_STRING: {},
                         RES_STRING: [[-1, -2, -3, -4], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0],
                                      [1.0, 2.0, 2.0, 1.0], [4, 3, 3, 4], [4, 3, 2, 1],
                                      [1.92354, 1.94936, 2.30217, 2.86356]],
                         CHECKF_STRING: check_basic_stats},
                        {OPER_STRING: operationexample.OperationExample,
                         PARAM_STRING: {"parameter1": None, "parameter3": 1},
                         RES_STRING: [operationexample.DEFAULT_PARAMETER1, operationexample.DEFAULT_PARAMETER2, 1],
                         CHECKF_STRING: check_operation_example}]}

    print("Performing test of OperationHistory")
    operations = operationshistory.OperationHistory()

    print("Testing appending operations:")
    for i in range(len(testset[DATASETS_STRING])):
        oper = testset[TESTOP_STRING][i][OPER_STRING]()
        oper.load_parameters(testset[TESTOP_STRING][i][PARAM_STRING])
        assert testset[TESTOP_STRING][i][CHECKF_STRING](oper, testset[DATASETS_STRING][i],
                                                        testset[TESTOP_STRING][i][RES_STRING])
        assert oper.save_to_queue(operations, testset[DATASETS_STRING][i])
    print("Passed")

    print("Testing run previous operation:")
    for i in range(len(testset[DATASETS_STRING])):
        assert testset[TESTOP_STRING][i][CHECKF_STRING](
            operations.get_previous_step(len(testset[DATASETS_STRING]) - i)[0],
            testset[DATASETS_STRING][i],
            testset[TESTOP_STRING][i][RES_STRING])
    print("Passed")

    print("Testing save and load to JSON:")
    json_string = operations.save_to_json()
    op_new = operationshistory.OperationHistory()
    assert op_new.load_from_json(json_string)

    print("Testing loaded operations:")
    for i in range(len(testset[DATASETS_STRING])):
        if (testset[TESTOP_STRING][i][RES_STRING] is not None) and \
                (op_new.get_previous_step(len(testset[DATASETS_STRING]) - i)[0].results is not None):
            assert check_arrays(op_new.get_previous_step(len(testset[DATASETS_STRING]) - i)[0].results,
                                testset[TESTOP_STRING][i][RES_STRING])
        assert testset[TESTOP_STRING][i][CHECKF_STRING](op_new.get_previous_step(len(testset[DATASETS_STRING]) - i)[0],
                                                        testset[DATASETS_STRING][i],
                                                        testset[TESTOP_STRING][i][RES_STRING])
    print("Passed")
