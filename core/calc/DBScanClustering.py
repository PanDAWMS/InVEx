import pickle

import numpy as np
from sklearn.cluster import DBSCAN

from . import baseoperationclass

MIN_SAMPLES = 5
EPS = 0.5
CLUST_ARRAY = []


class DBScanClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'DBSCAN Clustering'
    _operation_code_name = 'DBSCAN'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.min_samples = MIN_SAMPLES
        self.eps = EPS
        self.clust_array = CLUST_ARRAY
        self.model = None
        self.results = None
        self.number_of_clusters = None
        self.noise = None

    def set_parameters(self, min_samples, eps, clust_array):
        if min_samples is not None:
            self.min_samples = min_samples
        if eps is not None:
            self.eps = eps
        if clust_array is not None:
            self.clust_array = clust_array
        return True

    def save_parameters(self):
        return {'min_samples': self.min_samples,
                'eps': self.eps, 
                'clust_array': self.clust_array}

    def load_parameters(self, parameters):
        if "min_samples" in parameters and parameters["min_samples"] is not None:
            self.min_samples = parameters["min_samples"]
        else:
            self.min_samples = MIN_SAMPLES

        if "eps" in parameters and parameters["eps"] is not None:
            self.eps = parameters["eps"]
        else:
            self.eps = EPS

        if "clust_array" in parameters and parameters["clust_array"] is not None:
            self.clust_array = parameters["clust_array"]
        else:
            self.clust_array = CLUST_ARRAY
        return True

    def print_parameters(self):
        result = {'eps': self.eps, 'min_samples': self.min_samples, 'clust_array': self.clust_array}
        return result

    def save_results(self):
        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(self.results)) - (1 if -1 in self.results else 0)
        n_noise_ = list(self.results).count(-1)
        return {'results': self.results.tolist(), 'dump': pickle.dumps(self.model).hex(),
                'number_of_clusters': n_clusters_, 'noise': n_noise_}

    def load_results(self, results_dict):
        if 'results' in results_dict and results_dict['results'] is not None:
            self.results = np.array(results_dict['results'])
        if 'dump' in results_dict and results_dict['dump'] is not None:
            self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
        if 'number_of_clusters' in results_dict and results_dict['number_of_clusters'] is not None:
            self.number_of_clusters = results_dict['number_of_clusters']
        if 'noise' in results_dict and results_dict['noise'] is not None:
            self.noise = results_dict['noise']
        return True

    def process_data(self, dataset):
        dataset_cut = dataset if self.clust_array == [] else dataset.loc[:, self.clust_array]
        self.model = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(dataset_cut)
        self.results = self.model.labels_
        return self.results

    def predict(self, dataset):
        dataset_cut = dataset if self.clust_array == [] else dataset.loc[:, self.clust_array]
        return self.model.fit_predict(dataset_cut)


try:
    baseoperationclass.register(DBScanClustering)
except ValueError as error:
    print(repr(error))
