"""
Clustering class to support Intel® Data Analytics Acceleration Library.
"""

import numpy as np

from core.calc.logger import ServiceLogger

_logger = ServiceLogger('DBSCAN').logger

try:
    import daal4py as d4p
except ImportError as e:
    _logger.error(e)
    print(e)
    d4p = None

from . import baseoperationclass

NUM_CLUSTERS_DEFAULT = 5
NUM_ITERATIONS_DEFAULT = 5

class DAALKMeansClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'Intel DAAL K-Means Clustering'
    _operation_code_name = 'DAALKMeans'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.num_clusters = NUM_CLUSTERS_DEFAULT
        self.selected_features = []
        self.model = None
        self.centers = None
        self.labels = None

    def _preprocessed_data(self, data):
        return data if not self.selected_features \
            else data.loc[:, self.selected_features]

    def set_parameters(self, num_clusters, features=None):
        if num_clusters is not None:
            self.num_clusters = num_clusters
        else:
            _logger.error('num cluster is None')
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)
        _logger.debug("Parametrs have been set. Num clusters: {0}, selected features: {1}"
                      .format(self.num_clusters, self.selected_features))
        return True  # TODO: "return"-statement should be removed

    def get_parameters(self):
        data = {'numclusters_DAALKMeans': self.num_clusters,
                'features_DAALKMeans': self.selected_features}
        _logger.debug("Parametrs have been got: {0}".format(data))
        return data

    def get_labels(self, data, reprocess=False):
        data = self._preprocessed_data(data)

        if self.model is None or reprocess:
            self.model = d4p.\
                kmeans(nClusters=self.num_clusters,
                       maxIterations=NUM_ITERATIONS_DEFAULT,
                       assignFlag=True)

        if self.centers is None or reprocess:
            self.centers = d4p.\
                kmeans_init(nClusters=self.num_clusters, method='randomDense').\
                compute(data).\
                centroids

        _labels = self.model.compute(data, self.centers).assignments
        self.labels = np.reshape(_labels, len(_labels))
        _logger.debug("Labels have been got: {0}".format(data))
        return self.labels

    # methods that should be re-worked or removed
    # (for now keep these methods for consistency with others clustering modules)

    def print_parameters(self):
        return self.get_parameters()

    def save_parameters(self):
        return self.get_parameters()

    def load_parameters(self, parameters):
        self.set_parameters(
            num_clusters=parameters.get('numclusters_DAALKMeans') or NUM_CLUSTERS_DEFAULT,
            features=parameters.get('features_DAALKMeans') or [])
        _logger.debug("Parametrs have been loaded: {0}".format(parameters))
        return True

    def save_results(self):
        data = {'results': self.labels.tolist(),
                'cent': self.centers.tolist(),
                'dump': None}
        _logger.debug("Results have been saved. {0}".format(data))
        return data

    def load_results(self, results_dict):
        if results_dict.get('results'):
            self.labels = np.array(results_dict['results'])
        if results_dict.get('cent'):
            self.centers = np.array(results_dict['cent'])
        _logger.debug("Results have been loaded")
        return True

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(DAALKMeansClustering)
except ValueError as e:
    _logger.error(e)
    print(repr(e))
