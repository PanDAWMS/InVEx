import numpy as np
from functools import partial

from scipy.cluster.hierarchy import dendrogram, fcluster, linkage

from . import baseoperationclass
from .util import get_categorical_indices, encode_nominal_parameters, normalized_dataset


CLUSTER_NUMBER = 5
CATEGORICAL_WEIGHT = -1


class HierarchicalClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'Hierarchical Clustering'
    _operation_code_name = 'Hierarchical'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.cluster_number = CLUSTER_NUMBER
        self.categorical_weight = CATEGORICAL_WEIGHT
        self.linkage = None
        self.results = None

    def set_parameters(self, cluster_number, categorical_weight):
        if cluster_number is not None:
            self.cluster_number = cluster_number
        if categorical_weight is not None:
            self.categorical_weight = categorical_weight
        return True

    def save_parameters(self):
        return {"cluster_number": self.cluster_number, "categorical_weight": self.categorical_weight}

    def load_parameters(self, parameters):
        if parameters.get("cluster_number") is not None:
            self.cluster_number = parameters["cluster_number"]
        else:
            self.cluster_number = CLUSTER_NUMBER
        if parameters.get("categorical_weight") is not None:
            self.categorical_weight = parameters["categorical_weight"]
        else:
            self.categorical_weight = CATEGORICAL_WEIGHT
        return True

    def save_results(self):
        return {'results': self.results.tolist(), 'linkage': self.linkage.tolist()}

    def load_results(self, results_dict):
        if results_dict.get("results") is not None:
            self.results = np.array(results_dict['results'])
        if results_dict.get("linkage") is not None:
            self.linkage = np.array(results_dict['linkage'])
        return True

    def print_parameters(self):
        result = {"cluster_number": self.cluster_number, "categorical_weight": self.categorical_weight}
        return result

    def find_linkage(self, dataset):
        distance_metric = 'euclidean'
        categorical_indices = get_categorical_indices(dataset)
        numerical_indices = [x for x in range(dataset.shape[1]) if x not in categorical_indices]
        if categorical_indices:
            dataset = normalized_dataset(dataset, categorical_indices)
            dataset = encode_nominal_parameters(dataset, categorical_indices)
            if self.categorical_weight is None or self.categorical_weight < 0:
                self.categorical_weight = 0.5 * dataset.take(numerical_indices, axis=1).values.std()
            from .util.dissimilarity_python import mixed_metric
            distance_metric = partial(mixed_metric, categorical_indices=np.array(categorical_indices, dtype=np.int32), categorical_weight=self.categorical_weight)
        dataset = dataset.values
        self.linkage = linkage(dataset, method='single', metric=distance_metric, optimal_ordering=False)
        return True

    def dendrogram(self):
        from matplotlib import pyplot
        pyplot.figure()
        dendrogram(self.linkage)
        pyplot.show()

    def process_data(self, dataset):
        self.find_linkage(dataset)
        self.results = fcluster(self.linkage, self.cluster_number, criterion='maxclust')
        return self.results

    def predict(self, dataset):
        return self.model.predict(dataset)


try:
    baseoperationclass.register(HierarchicalClustering)
except ValueError as error:
    print(repr(error))
