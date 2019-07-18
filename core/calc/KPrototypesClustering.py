import numpy as np
import pickle

from kmodes.kprototypes import KPrototypes
from . import baseoperationclass

CLUSTER_NUMBER = 5
CATEGORICAL_WEIGHT = None


class KPrototypesClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'K-Prototypes Clustering'
    _operation_code_name = 'KPrototypes'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.cluster_number = CLUSTER_NUMBER
        self.categorical_weight = CATEGORICAL_WEIGHT
        self.model = None
        self.results = None
        self.cent = None

    def set_parameters(self, cluster_number, categorical_weight):
        if cluster_number is not None:
            self.cluster_number = cluster_number
        if categorical_weight is not None:
            self.categorical_weight = categorical_weight
        return True

    def save_parameters(self):
        return {'cluster_number': self.cluster_number, 'categorical_data_weight': self.categorical_weight}

    def load_parameters(self, parameters):
        if parameters.get("cluster_number") is not None:
            self.cluster_number = parameters["cluster_number"]
        else:
            self.cluster_number = CLUSTER_NUMBER
        if parameters.get("categorical_data_weight") is not None:
            self.categorical_weight = parameters["categorical_data_weight"]
        else:
            self.categorical_weight = CATEGORICAL_WEIGHT
        return True

    def save_results(self):
        return {'results': self.results.tolist(), 'cent': self.cent.tolist(), 'dump': pickle.dumps(self.model).hex()}

    def load_results(self, results_dict):
        if results_dict.get("results") is not None:
            self.results = np.array(results_dict['results'])
        if results_dict.get("cent") is not None:
            self.cent = np.array(results_dict['cent'])
        if results_dict.get("dump") is not None:
            self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
        return True

    def print_parameters(self):
        result = {'cluster_number': self.cluster_number, 'categorical_data_weight': self.categorical_weight}
        return result

    def get_categorical_indices(self, dataset):
        categorical_indices = []
        for index, column in enumerate(dataset.columns):
            if dataset[column].dtype.name in ('category', 'object'):
                categorical_indices.append(index)
                print(f"categorical index = {index}")
        return tuple(categorical_indices)

    # By default, K-Prototypes uses euclidean distance for numerical data and Hamming distance for categorical data
    # n_init is the number of time the k-modes algorithm will be run with different centroid seeds
    # gamma is the weight to balance numerical data against categorical. If None, it defaults to half of standard deviation for numerical data
    def process_data(self, dataset):
        self.model = KPrototypes(n_clusters=self.cluster_number, max_iter=1000, init='Cao', n_init=10, gamma=self.categorical_weight, n_jobs=1)
        categorical_indices = self.get_categorical_indices(dataset)
        dataset = dataset.to_numpy()
        self.model.fit(dataset, categorical=categorical_indices)
        self.results = self.model.predict(dataset, categorical=categorical_indices)
        self.cent = self.model.cluster_centroids_
        return self.results

    def predict(self, dataset):
        categorical_indices = self.get_categorical_indices(dataset)
        dataset = dataset.to_numpy()
        return self.model.predict(dataset, categorical=categorical_indices)


try:
    baseoperationclass.register(KPrototypesClustering)
except ValueError as error:
    print(repr(error))
