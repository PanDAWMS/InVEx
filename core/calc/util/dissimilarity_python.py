import numpy as np
import numba

from math import sqrt


@numba.jit(nopython=True)
def euclidean(array_2d, array_1d):
    result = np.zeros(array_2d.shape[0])
    for i in range(array_2d.shape[0]):
        for j in range(array_2d.shape[1]):
            result[i] += (array_2d[i][j] - array_1d[j]) * (array_2d[i][j] - array_1d[j])
    return result


@numba.jit(nopython=True)
def mixed_metric(array_2d, array_1d, categorical_indices, categorical_weight):
    result, cat_result = 0, 0
    categorical = np.zeros(array_2d.shape[0], dtype=np.int32)
    for i in categorical_indices:
        categorical[i] = 1
    for i in range(array_2d.shape[0]):
        if categorical[i] and array_2d[i] == array_1d[i]:
            cat_result += categorical_weight
        else:
            result += (array_2d[i] - array_1d[i]) * (array_2d[i] - array_1d[i])
    return cat_result + sqrt(result)
