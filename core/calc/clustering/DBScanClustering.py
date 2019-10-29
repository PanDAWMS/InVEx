import pickle

import numpy as np
from sklearn.cluster import DBSCAN
from core.calc.logger import ServiceLogger

from . import baseoperationclass

_logger = ServiceLogger('DBSCAN').logger

MIN_SAMPLES = 5
EPS = 0.5


class DBScanClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'DBSCAN Clustering'
    _operation_code_name = 'DBSCAN'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.min_samples = MIN_SAMPLES
        self.eps = EPS
        self.selected_features = []
        self.model = None
        self.labels = None
        self.number_of_clusters = None
        self.noise = None

    def _preprocessed_data(self, data):
        return data if not self.selected_features \
            else data.loc[:, self.selected_features]

    def set_parameters(self, min_samples, eps, features=None):
        if min_samples is not None:
            self.min_samples = min_samples
        else:
            _logger.error('min samples is None')
        if eps is not None:
            self.eps = eps
        else:
            _logger.error('eps is None')
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)
        _logger.debug("Parametrs have been set. Min samples: {0}, eps: {1}, selected features: {2}"
                      .format(self.min_samples, self.eps, self.selected_features))
        return True

    def get_parameters(self):
        data = {'min_samples_DBSCAN': self.min_samples,
                'eps_DBSCAN': self.eps,
                'features_DBSCAN': self.selected_features}
        _logger.debug("Parametrs have been got: {0}".format(data))
        return data

    def get_labels(self, data, reprocess=False):
        data = self._preprocessed_data(data)

        if self.model is None or reprocess:
            self.model = DBSCAN(eps=self.eps, min_samples=self.min_samples)
            self.model.fit(data)

        self.labels = self.model.labels_
        _logger.debug("Labels have been got: {0}".format(data))
        return self.labels

    # Legacy methods

    def print_parameters(self):
        return self.get_parameters()

    def save_parameters(self):
        return self.get_parameters()

    def load_parameters(self, parameters):
        self.set_parameters(
            min_samples=parameters.get('min_samples_DBSCAN') or MIN_SAMPLES,
            eps=parameters.get('eps_DBSCAN') or EPS,
            features=parameters.get('features_DBSCAN') or []
        )
        _logger.debug("Parametrs have been loaded: {0}".format(parameters))
        return True

    def save_results(self):
        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(self.labels)) - (1 if -1 in self.labels else 0)
        n_noise_ = list(self.labels).count(-1)
        data = {'results': self.labels.tolist(),
                'dump': pickle.dumps(self.model).hex(),
                'number_of_clusters': n_clusters_,
                'noise': n_noise_}
        _logger.debug("Results have been saved: {0}".format(data))
        return data

    def load_results(self, results_dict):
        if 'results' in results_dict and results_dict['results'] is not None:
            self.labels = np.array(results_dict['results'])
        if 'dump' in results_dict and results_dict['dump'] is not None:
            self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
        if 'number_of_clusters' in results_dict and results_dict['number_of_clusters'] is not None:
            self.number_of_clusters = results_dict['number_of_clusters']
        if 'noise' in results_dict and results_dict['noise'] is not None:
            self.noise = results_dict['noise']
        _logger.debug("Results have been loaded")
        return True

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(DBScanClustering)
except ValueError as error:
    _logger.error(error)
    print(repr(error))
