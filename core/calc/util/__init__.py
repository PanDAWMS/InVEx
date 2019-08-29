import numpy as np
from sklearn.preprocessing import scale

import pyximport
pyximport.install(setup_args={"include_dirs": [np.get_include()]})


def get_categorical_indices(dataset):
    categorical_indices = []
    for index, column in enumerate(dataset.columns):
        if dataset[column].dtype.name not in ("float64", "float32", "int64", "int32"):
            categorical_indices.append(index)
        elif float(dataset[column].nunique()) / dataset[column].count() < 0.1:
            categorical_indices.append(index)
    return tuple(categorical_indices)


def _get_encoding_map(values):
    unique_values = np.unique(values)
    encoding_map = {}
    for index, value in enumerate(unique_values):
        encoding_map[value] = index
    return encoding_map


def encode_nominal_parameters(dataset):
    for column, values in dataset.items():
        if dataset[column].dtype.name not in ("float64", "float32", "int64", "int32"):
            encoding_map = _get_encoding_map(values.values)
            dataset[column] = values.apply(encoding_map.get)
    return dataset


def normalized_dataset(dataset, indices_to_ignore):
    dataset = dataset.copy()
    for index, column in enumerate(dataset.columns):
        if index in indices_to_ignore or dataset[column].dtype.name not in ("float64", "float32", "int64", "int32"):
            continue
        values = scale(dataset[column].values.astype(np.float64))
        dataset[column] = values
    return dataset
