from numpy import zeros
from numpy import float64, int32
from numpy cimport ndarray
cimport numpy as np
cimport cython
from libc.math cimport sqrt

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def euclidean(ndarray[np.float64_t, ndim=2] a, ndarray[np.float64_t, ndim=1] b):
    cdef Py_ssize_t i, j
    cdef Py_ssize_t n = a.shape[0]
    cdef Py_ssize_t m = a.shape[1]
    cdef np.ndarray[np.float64_t, ndim=1] result = zeros(a.shape[0], dtype=float64)
    for i in range(n):
        for j in range(m):
            result[i] += (a[i,j] - b[j]) * (a[i,j] - b[j])
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def mixed_metric(ndarray[np.float64_t, ndim=1] a, ndarray[np.float64_t, ndim=1] b, ndarray[np.int32_t, ndim=1] categorical_indices, np.float64_t categorical_weight):
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef Py_ssize_t m = categorical_indices.shape[0]
    cdef double result = 0, cat_result = 0
    cdef np.ndarray[np.int32_t, ndim=1] categorical = zeros(a.shape[0], dtype=int32)

    for i in range(m):
        categorical[i] = 1
    for i in range(n):
        if categorical[i] and a[i] == b[i]:
            cat_result += categorical_weight
        else:
            result += (a[i] - b[i]) * (a[i] - b[i])
    return cat_result + sqrt(result)
