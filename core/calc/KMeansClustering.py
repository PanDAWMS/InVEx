from . import baseoperationclass
from sklearn.cluster import KMeans
import numpy as np
import pickle

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
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)
        return True

    def get_parameters(self):
        return {'numberofcl_KMeans': self.clust_numbers,
                'features_KMeans': self.selected_features}

    def get_labels(self, data, reprocess=False):
        data = self._preprocessed_data(data)

        if self.model is None or reprocess:
            self.model = KMeans(self.clust_numbers)
            self.model.fit(data)
            self.labels = self.model.predict(data)
            self.centers = self.model.cluster_centers_
        else:
            self.labels = self.model.predict(data)

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
        return True

    def save_results(self):
        return {'results': self.labels.tolist(),
                'centers': self.centers.tolist(),
                'dump': pickle.dumps(self.model).hex()}

    def load_results(self, results_dict):
        if results_dict.get('results'):
            self.labels = np.array(results_dict['results'])
        if results_dict.get('centers'):
            self.centers = np.array(results_dict['centers'])
        if results_dict.get('dump'):
            self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
        return True

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(KMeansClustering)
except ValueError as error:
    print(repr(error))
