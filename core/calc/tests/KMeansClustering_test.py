import pandas as pd
import numpy as np
from calc import KMeansClustering
from calc import operationshistory

DATASETS_STRING = 'dataset'
RESULTS_STRING = 'results'


def isclose(a, b, rel_tol=1e-04, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def check_two_d_arrays(results, info, clusters, order):
    for i in range(len(results)):
        for j in range(len(results)):
            if not isclose(results[clusters[order[i]]][j], info[i][j]):
                return False
    return True


def check_cluster_arrays(clusters, results):
    for i in range(len(results)):
        for j in range(len(results[i])):
            if clusters[results[i][j]] != clusters[results[i][0]]:
                return False
    return True


def run_test(data, parameters, results):
    print('Testing KMeans process data')
    oper1 = KMeansClustering.KMeansClustering()
    oper1.set_parameters(parameters)
    res = oper1.process_data(data)
    assert check_cluster_arrays(res, results['results'])
    assert check_two_d_arrays(oper1.cent, results['cent'], oper1.results, results['order'])
    print('Testing KMeans save/load')
    history = operationshistory.OperationHistory()
    history.append(data, oper1)
    text = history.save_to_json()
    history2 = operationshistory.OperationHistory()
    history2.load_from_json(text)
    oper2 = history2.get_previous_step()[0]
    assert check_cluster_arrays(oper2.results, results['results'])
    assert check_two_d_arrays(oper2.cent, results['cent'], oper2.results, results['order'])
    print('Testing loaded KMeans process data')
    oper2.process_data(data)
    assert check_cluster_arrays(oper2.results, results['results'])
    assert check_two_d_arrays(oper2.cent, results['cent'], oper2.results, results['order'])


def run():
    testset = {DATASETS_STRING: [[pd.DataFrame(
        [[7, 1, 3, 3], [6, 4, 8, 9], [1, 1, 0, 8], [6, 2, 0, 4], [2, 4, 2, 2], [7, 9, 2, 3], [9, 7, 7, 2],
         [5, 9, 8, 10]]), 3],
        [pd.DataFrame([[1, 2, 3, 4], [4, 3, 2, 1], [-1, -2, -3, -4], [0, 0, 0, 0], [0, 0, 0, 0]]), 2]],
        RESULTS_STRING: [{'results': [[0, 2, 3, 4], [1, 7], [5, 6]],
                          'cent': np.array([[4., 2., 1.25, 4.25], [5.5, 6.5, 8., 9.5], [8., 8., 4.5, 2.5]]),
                          'order':[0, 1, 5]},
                         {'results': [[0, 1], [2, 3, 4]],
                          'cent': np.array([[2.5, 2.5, 2.5, 2.5], [-0.33333333, -0.66666667, -1., -1.33333333]]),
                          'order': [0, 2]}]}

    print("Performing test of KMeansClustering")
    for i in range(len(testset)):
        print(f"Testing on testset number {i}:")
        run_test(testset[DATASETS_STRING][i][0], testset[DATASETS_STRING][i][1], testset[RESULTS_STRING][i])
    print("Passed")
