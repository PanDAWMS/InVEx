import numpy as np
import pickle

from random import randint

from kmodes.kprototypes import KPrototypes
from kmodes.util.dissim import matching_dissim

from core.calc.logger import ServiceLogger

from . import baseoperationclass
from ..util import dissimilarity_python
from ..util import get_categorical_indices, encode_nominal_parameters, normalized_dataset

_logger = ServiceLogger('KPrototypes').logger

CLUSTER_NUMBER = 5
CATEGORICAL_WEIGHT = -1


class KPrototypesClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'K-Prototypes Clustering'
    _operation_code_name = 'KPrototypes'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.cluster_number = CLUSTER_NUMBER
        self.categorical_weight = CATEGORICAL_WEIGHT
        self.selected_features = []
        self.model = None
        self.labels = None
        self.centers = None

    def _preprocessed_data(self, data):
        return data if not self.selected_features \
            else data.loc[:, self.selected_features]

    def set_parameters(self, cluster_number, categorical_weight=None, features=None):
        if cluster_number is not None:
            self.cluster_number = cluster_number
        else:
            _logger.error('cluster number is None')
        if categorical_weight is not None:
            self.categorical_weight = categorical_weight
        if features is not None and isinstance(features, (list, tuple)):
            self.selected_features = list(features)
        _logger.debug("Parametrs have been set. Cluster number: {0}, categorical weight: {1}, selected features: {2}"
                      .format(self.cluster_number, self.categorical_weight, self.selected_features))
        return True

    def get_parameters(self):
        data = {'cluster_number_KPrototypes': self.cluster_number,
                'categorical_data_weight_KPrototypes': self.categorical_weight,
                'features_KPrototypes': self.selected_features}
        _logger.debug("Parametrs have been got: {0}".format(data))
        return data

    def _get_initial_centers(self, dataset, categorical_indices):
        try:
            dataset_cat = dataset.take(categorical_indices, axis=1).values
            categorical_labels = [column for index, column in enumerate(dataset.columns) if index in categorical_indices]
            dataset_num = dataset.drop(categorical_labels, axis=1).values

            categorical_weight = self.categorical_weight
            if categorical_weight is None or categorical_weight < 0:
                categorical_weight = 0.5 * dataset_num.std()
            initial_centroids_num = np.zeros((self.cluster_number, dataset_num.shape[1]))
            initial_centroids_cat = np.zeros((self.cluster_number, dataset_cat.shape[1]))
            rand_index = randint(0, dataset.shape[0] - 1)
            initial_centroids_num[0], initial_centroids_cat[0] = dataset_num[rand_index], dataset_cat[rand_index]

            for i in range(1, self.cluster_number):
                distances_num_cat = [np.zeros((i, dataset.shape[0]), dtype=np.float64), np.zeros((i, dataset.shape[0]))]
                for j in range(0, i):
                    distances_num_cat[0][j] = dissimilarity_python.euclidean(dataset_num, initial_centroids_num[j])
                    distances_num_cat[1][j] = matching_dissim(dataset_cat, initial_centroids_cat[j])
                distances = np.amin(distances_num_cat[0] + categorical_weight * distances_num_cat[1], axis=0)
                probabilities = distances / np.sum(distances)
                chosen_point = np.random.choice(range(0, dataset.shape[0]), p=probabilities)
                initial_centroids_num[i] = dataset_num[chosen_point]
                initial_centroids_cat[i] = dataset_cat[chosen_point]

            initial_centroids = [initial_centroids_num, initial_centroids_cat]
        except Exception as error:
            _logger.error(error)
            print(error)
        _logger.debug("Initial centroids: {0}".format(initial_centroids))
        return initial_centroids

    # Used if there's no categorical properties in the dataset
    def _fallback_algorithm(self, dataset):
        from . import KMeansClustering
        self.model = KMeansClustering.KMeansClustering()
        self.model.set_parameters(self.cluster_number, self.selected_features)
        self.labels = self.model.get_labels(dataset)
        self.centers = self.model.centers
        return self.labels

    # By default, K-Prototypes uses euclidean distance for numerical data and Hamming distance for categorical data
    # n_init is the number of time the k-modes algorithm will be run with different centroid seeds
    # gamma is the weight to balance numerical data against categorical.
    # If None, it defaults to half of standard deviation for numerical data
    def get_labels(self, data, reprocess=False):
        data_original = data
        data = self._preprocessed_data(data)

        categorical_indices = get_categorical_indices(data)
        if not categorical_indices:
            return self._fallback_algorithm(data_original)

        if self.model is None or reprocess:
            data = encode_nominal_parameters(data)
            data = normalized_dataset(data, categorical_indices)

            initial_centers = self._get_initial_centers(data, categorical_indices)
            self.model = KPrototypes(n_clusters=self.cluster_number, max_iter=1000, init=initial_centers, n_init=10,
                                     gamma=self.categorical_weight, num_dissim=dissimilarity_python.euclidean, n_jobs=1)
            data = data.values
            self.model.fit(data, categorical=categorical_indices)
            self.labels = self.model.predict(data, categorical=categorical_indices)
            self.centers = self.model.cluster_centroids_
            centers = self.centers[0]
            for index, cat_index in enumerate(categorical_indices):
                centers = np.insert(centers, cat_index, values=self.centers[1].transpose()[index], axis=1)
            self.centers = centers
        else:
            self.labels = self.model.predict(data)
        _logger.debug("Labels have been got: {0}".format(data))
        return self.labels

    # Legacy methods

    def print_parameters(self):
        return self.get_parameters()

    def save_parameters(self):
        return self.get_parameters()

    def load_parameters(self, parameters):
        self.set_parameters(
            cluster_number=parameters.get('cluster_number_KPrototypes') or CLUSTER_NUMBER,
            categorical_weight=parameters.get('categorical_data_weight_KPrototypes') or CATEGORICAL_WEIGHT,
            features=parameters.get('features_KPrototypes') or []
        )
        _logger.debug("Parametrs have been loaded: {0}".format(parameters))
        return True

    def save_results(self):
        data = {'results': self.labels.tolist(),
                'centers': self.centers.tolist(),
                'dump': pickle.dumps(self.model).hex()}
        _logger.debug("Results have been saved: {0}".format(data))
        return data

    def load_results(self, results_dict):
        if results_dict.get("results") is not None:
            self.labels = np.array(results_dict['results'])
        if results_dict.get("centers") is not None:
            self.centers = np.array(results_dict['centers'])
        if results_dict.get("dump") is not None:
            self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
        _logger.debug("Results have been loaded")
        return True

    def process_data(self, data):
        return self.get_labels(data)

    def predict(self, data):
        return self.get_labels(data)


try:
    baseoperationclass.register(KPrototypesClustering)
except ValueError as error:
    _logger.error(error)
    print(repr(error))
