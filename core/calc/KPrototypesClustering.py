import numpy as np
import pickle

from random import randint

from kmodes.kprototypes import KPrototypes
from kmodes.util.dissim import matching_dissim
from . import baseoperationclass
from .util import dissimilarity_python
from .util import get_categorical_indices, encode_nominal_parameters, normalized_dataset


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

    def _get_initial_centers(self, dataset, categorical_indices):
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
        return initial_centroids

    # Used if there's no categorical properties in the dataset
    def _fallback_algorithm(self, dataset):
        from . import KMeansClustering
        self.model = KMeansClustering.KMeansClustering()
        self.model.clust_numbers, self.model.clust_array = self.cluster_number, []
        self.results = self.model.process_data(dataset)
        self.cent = self.model.model.cluster_centers_
        return self.results

    # By default, K-Prototypes uses euclidean distance for numerical data and Hamming distance for categorical data
    # n_init is the number of time the k-modes algorithm will be run with different centroid seeds
    # gamma is the weight to balance numerical data against categorical. If None, it defaults to half of standard deviation for numerical data
    def process_data(self, dataset):
        categorical_indices = get_categorical_indices(dataset)
        if not categorical_indices:
            return self._fallback_algorithm(dataset)
        dataset = encode_nominal_parameters(dataset)
        dataset = normalized_dataset(dataset, categorical_indices)

        initial_centers = self._get_initial_centers(dataset, categorical_indices)
        self.model = KPrototypes(n_clusters=self.cluster_number, max_iter=1000, init=initial_centers, n_init=10, gamma=self.categorical_weight, num_dissim=dissimilarity_python.euclidean, n_jobs=1)
        dataset = dataset.values
        self.model.fit(dataset, categorical=categorical_indices)
        self.results = self.model.predict(dataset, categorical=categorical_indices)
        self.cent = self.model.cluster_centroids_
        centers = self.cent[0]
        for index, cat_index in enumerate(categorical_indices):
            centers = np.insert(centers, cat_index, values=self.cent[1].transpose()[index], axis=1)
        self.cent = centers
        return self.results

    def predict(self, dataset):
        categorical_indices = get_categorical_indices(dataset)
        dataset = dataset.values
        return self.model.predict(dataset, categorical=categorical_indices)


try:
    baseoperationclass.register(KPrototypesClustering)
except ValueError as error:
    print(repr(error))
