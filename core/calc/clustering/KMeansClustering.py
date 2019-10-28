
import numpy as np
import pickle

from sklearn.cluster import KMeans

from . import baseoperationclass

NUM_CLUSTERS_DEFAULT = 3


class KMeansClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'K-Means Clustering'
    _operation_code_name = 'KMeans'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.num_clusters = NUM_CLUSTERS_DEFAULT
        self.selected_features = []
        self.model = None
        self.labels = None
        self.centers = None

    def _preprocessed_data(self, data):
        return data if not self.selected_features \
            else data.loc[:, self.selected_features]

    def set_parameters(self, num_clusters, features=None):
        if num_clusters is not None:
            self.num_clusters = num_clusters
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)

    def load_parameters(self, **kwargs):
        self.set_parameters(
            num_clusters=kwargs.get('numberofcl_KMeans') or
            NUM_CLUSTERS_DEFAULT,
            features=kwargs.get('features_KMeans') or [])

    def get_parameters(self):
        return {'numberofcl_KMeans': self.num_clusters,
                'features_KMeans': self.selected_features}

    def get_labels(self, data, reprocess=False):
        data = self._preprocessed_data(data)

        if self.model is None or reprocess:
            self.model = KMeans(self.num_clusters)
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
