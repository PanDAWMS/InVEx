
import numpy as np
import pickle

from sklearn.cluster import MiniBatchKMeans
from core.calc.logger import ServiceLogger

from . import baseoperationclass

_logger = ServiceLogger('MiniBatchKMeans').logger

NUM_CLUSTERS_DEFAULT = 5
BATCH_SIZE_DEFAULT = 200
EXTRA_PARAMS_DEFAULT = {
    'random_state': 0,
    'max_iter': 10,
    'init_size': 3000,
    # 'tol': 1e-5,
    # 'max_no_improvement': None
}
CLUST_ARRAY = []


class MiniBatchKMeansClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'MiniBatch K-Means Clustering'
    _operation_code_name = 'MiniBatchKMeans'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.num_clusters = NUM_CLUSTERS_DEFAULT
        self.selected_features = []
        self.batch_size = BATCH_SIZE_DEFAULT
        self.model = None
        self.centers = None
        self.labels = None

    def _preprocessed_data(self, data):
        return data if not self.selected_features \
            else data.loc[:, self.selected_features]

    def set_parameters(self, num_clusters, features=None, batch_size=None):
        if num_clusters is not None:
            self.num_clusters = num_clusters
        else:
            _logger.error('num clusters is None')
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)
        if batch_size is not None:
            self.batch_size = batch_size
        _logger.debug("Parametrs have been set. Num clusters: {0}, selected features: {1}, batch size: {2}"
                      .format(self.num_clusters, self.selected_features, self.batch_size))
        return True  # TODO: "return"-statement should be removed

    def get_parameters(self):
        data = {'numclusters_MiniBatchKMeans': self.num_clusters,
                'features_MiniBatchKMeans': self.selected_features,
                'batchsize_MiniBatchKMeans': self.batch_size}
        _logger.debug("Parametrs have been got: {0}".format(data))
        return data

    def get_labels(self, data, reprocess=False):
        data = self._preprocessed_data(data)

        if self.model is None or reprocess:
            self.model = MiniBatchKMeans(
                n_clusters=self.num_clusters,
                batch_size=self.batch_size,
                **EXTRA_PARAMS_DEFAULT)

            self.labels = self.model.fit_predict(data)
            self.centers = self.model.cluster_centers_
        else:
            self.labels = self.model.predict(data)
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
            num_clusters=parameters.get('numclusters_MiniBatchKMeans') or NUM_CLUSTERS_DEFAULT,
            features=parameters.get('features_MiniBatchKMeans') or [],
            batch_size=parameters.get('batchsize_MiniBatchKMeans' or BATCH_SIZE_DEFAULT))
        _logger.debug("Parametrs have been loaded: {0}".format(parameters))
        return True

    def save_results(self):
        data = {'results': self.labels.tolist(),
                'cent': self.centers.tolist(),
                'dump': pickle.dumps(self.model).hex()}
        _logger.debug("Results have been saved: {0}".format(data))
        return data

    def load_results(self, results_dict):
        if results_dict.get('results'):
            self.labels = np.array(results_dict['results'])
        if results_dict.get('cent'):
            self.centers = np.array(results_dict['cent'])
        if results_dict.get('dump'):
            self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
        _logger.debug("Results have been loaded")
        return True

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(MiniBatchKMeansClustering)
except ValueError as error:
    _logger.error(error)
    print(repr(error))
