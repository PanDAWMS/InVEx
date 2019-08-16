from numpy cimport ndarray
from numpy import zeros, sum
from numpy import float32, float64, int32, int64
cimport numpy as np
cimport cython


def euclidean(ndarray a, ndarray b):
    if not (a.dtype == b.dtype):
        if a.dtype in (float32, float64, int32, int64) and b.dtype in (float32, float64, int32, int64):
            a = a.astype(float64)
            b = b.astype(float64)
        else:
            return _euclidean_default(a, b)
    dispatch = {
        "float64": _euclidean_f64,
        "float32": _euclidean_f32,
        "int64": _euclidean_i64,
        "int32": _euclidean_i32,
    }
    algorithm = dispatch.get(a.dtype.name, _euclidean_default)
    return algorithm(a, b)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def _euclidean_f64(ndarray[np.float64_t, ndim=2] a, ndarray[np.float64_t, ndim=1] b):
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
def _euclidean_f32(ndarray[np.float32_t, ndim=2] a, ndarray[np.float32_t, ndim=1] b):
    cdef Py_ssize_t i, j
    cdef Py_ssize_t n = a.shape[0]
    cdef Py_ssize_t m = a.shape[1]
    cdef np.ndarray[np.float32_t, ndim=1] result = zeros(a.shape[0], dtype=float32)
    for i in range(n):
        for j in range(m):
            result[i] += (a[i,j] - b[j]) * (a[i,j] - b[j])
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def _euclidean_i64(ndarray[np.int64_t, ndim=2] a, ndarray[np.int64_t, ndim=1] b):
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef Py_ssize_t m = a.shape[1]
    cdef np.ndarray[np.int64_t, ndim=1] result = zeros(a.shape[0], dtype=int64)
    for i in range(n):
        for j in range(m):
            result[i] += (a[i,j] - b[j]) * (a[i,j] - b[j])
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def _euclidean_i32(ndarray[np.int32_t, ndim=2] a, ndarray[np.int32_t, ndim=1] b):
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef Py_ssize_t m = a.shape[1]
    cdef np.ndarray[np.int32_t, ndim=1] result = zeros(a.shape[0], dtype=int32)
    for i in range(n):
        for j in range(m):
            result[i] += (a[i,j] - b[j]) * (a[i,j] - b[j])
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def _euclidean_default(ndarray a, ndarray b):
    return sum((a - b) ** 2)
