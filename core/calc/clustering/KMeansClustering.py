from . import baseoperationclass
from sklearn.cluster import KMeans

from core.calc.logger import ServiceLogger

import numpy as np
import pickle

_logger = ServiceLogger('KMeans').logger

CLUST_NUM = 3


class KMeansClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'K-Means Clustering'
    _operation_code_name = 'KMeans'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.clust_numbers = CLUST_NUM
        self.selected_features = []
        self.model = None
        self.labels = None
        self.centers = None

    def _preprocessed_data(self, data):
        return data if not self.selected_features \
            else data.loc[:, self.selected_features]

    def set_parameters(self, clust_numbers, features=None):
        if clust_numbers is not None:
            self.clust_numbers = clust_numbers
        else:
            _logger.error('cluster numbers is None')
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)
        _logger.debug("Parametrs have been set. Cluster numbers: {0}, selected features: {1}"
                      .format(self.clust_numbers, self.selected_features))
        return True

    def get_parameters(self):
        data = {'numberofcl_KMeans': self.clust_numbers,
                'features_KMeans': self.selected_features}
        _logger.debug('Get parametrs: {0}'.format(data))
        return data

    def get_labels(self, data, reprocess=False):
        data = self._preprocessed_data(data)

        if self.model is None or reprocess:
            self.model = KMeans(self.clust_numbers)
            self.model.fit(data)
            self.labels = self.model.predict(data)
            self.centers = self.model.cluster_centers_
        else:
            self.labels = self.model.predict(data)
        _logger.debug('Labels have been got')
        return self.labels

    # Legacy methods

    def print_parameters(self):
        return self.get_parameters()

    def save_parameters(self):
        return self.get_parameters()

    def load_parameters(self, parameters):
        self.set_parameters(
            clust_numbers=parameters.get('numberofcl_KMeans') or CLUST_NUM,
            features=parameters.get('features_KMeans') or []
        )
        _logger.debug("Parameters have been loaded: {0}".format(parameters))
        return True

    def save_results(self):
        data = {'results': self.labels.tolist(),
                'centers': self.centers.tolist(),
                'dump': pickle.dumps(self.model).hex()}
        _logger.debug("Save results: {0}".format(data))
        return data

    def load_results(self, results_dict):
        try:
            if results_dict.get('results'):
                self.labels = np.array(results_dict['results'])
            if results_dict.get('centers'):
                self.centers = np.array(results_dict['centers'])
            if results_dict.get('dump'):
                self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
            return True
        except Exception as error:
            _logger.error(error)
            print(repr(error))

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(KMeansClustering)
except ValueError as error:
    _logger.error(error)
    print(repr(error))