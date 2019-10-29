import numpy as np
from functools import partial

from core.calc.logger import ServiceLogger
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage

from . import baseoperationclass
from ..util import get_categorical_indices, encode_nominal_parameters, normalized_dataset

_logger = ServiceLogger('Hierarchical').logger

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
        self.selected_features = []
        self.linkage = None
        self.labels = None
        self.centers = None

    def _preprocessed_data(self, data):
        return data if not self.selected_features \
            else data.loc[:, self.selected_features]

    def set_parameters(self, cluster_number, categorical_weight, features=None):
        if cluster_number is not None:
            self.cluster_number = cluster_number
        else:
            _logger.error("cluster number is None")
        if categorical_weight is not None:
            self.categorical_weight = categorical_weight
        else:
            _logger.error("categorical weight is None")
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)
        _logger.debug("Parametrs have been set. Cluster number: {0}, categorical weight: {1}, selected features: {2}"
                      .format(self.cluster_number, self.categorical_weight, self.selected_features))
        return True

    def get_parameters(self):
        data = {"cluster_number_Hierarchical": self.cluster_number,
                "categorical_data_weight_Hierarchical": self.categorical_weight,
                'features_Hierarchical': self.selected_features}
        _logger.debug("Parametrs have been got: {0}".format(data))
        return data

    def _find_linkage(self, dataset):
        try:
            distance_metric = 'euclidean'
            categorical_indices = get_categorical_indices(dataset)
            numerical_indices = [x for x in range(dataset.shape[1]) if x not in categorical_indices]
            if categorical_indices:
                dataset = normalized_dataset(dataset, categorical_indices)
                dataset = encode_nominal_parameters(dataset, categorical_indices)
                if self.categorical_weight is None or self.categorical_weight < 0:
                    self.categorical_weight = 0.5 * dataset.take(numerical_indices, axis=1).values.std()
                from ..util.dissimilarity_python import mixed_metric
                distance_metric = partial(mixed_metric,
                                          categorical_indices=np.array(categorical_indices, dtype=np.int32),
                                          categorical_weight=self.categorical_weight)
            dataset = dataset.values
            self.linkage = linkage(dataset, method='single', metric=distance_metric, optimal_ordering=False)
        except Exception as error:
            _logger.error(error)
            print(error)
        _logger.debug("Linkage has been found {0}".format(self.linkage))
        return True

    def _dendrogram(self):
        from matplotlib import pyplot
        pyplot.figure()
        dendrogram(self.linkage)
        pyplot.show()

    def get_labels(self, data, reprocess=False):
        data = self._preprocessed_data(data)

        if self.labels is None or reprocess:
            self._find_linkage(data)
            self.labels = fcluster(self.linkage, self.cluster_number, criterion='maxclust')
        _logger.debug("Labels have been got: {0}".format(data))
        return self.labels

    # Legacy methods

    def print_parameters(self):
        return self.get_parameters()

    def save_parameters(self):
        return self.get_parameters()

    def load_parameters(self, parameters):
        self.set_parameters(
            cluster_number=parameters.get('cluster_number_Hierarchical') or CLUSTER_NUMBER,
            categorical_weight=parameters.get('categorical_data_weight_Hierarchical') or CATEGORICAL_WEIGHT,
            features=parameters.get('features_Hierarchical') or []
        )
        _logger.debug("Parametrs have been loaded {0}".format(parameters))
        return True

    def save_results(self):
        data = {'results': self.labels.tolist(),
                'linkage': self.linkage.tolist()}
        _logger.debug("Save results: {0}".format(data))
        return data

    def load_results(self, results_dict):
        if results_dict.get("results") is not None:
            self.labels = np.array(results_dict['results'])
        if results_dict.get("linkage") is not None:
            self.linkage = np.array(results_dict['linkage'])
        _logger.debug("Results have been loaded")
        return True

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(HierarchicalClustering)
except ValueError as error:
    _logger.error(error)
    print(repr(error))
