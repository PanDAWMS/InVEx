from . import baseoperationclass
from sklearn.cluster import KMeans
import numpy as np
import pickle

CLUST_NUM = 3
CLUST_ARRAY = None

class KMeansClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'K-Means Clustering'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.clust_numbers = CLUST_NUM
        self.clust_array = CLUST_ARRAY
        self.model = None
        self.results = None
        self.cent = None

    def set_parameters(self, clust_numbers, clust_array):
        if clust_numbers is not None:
            self.clust_numbers = clust_numbers
        if clust_array is not None:
            self.clust_array = clust_array
        return True

    def save_parameters(self):
        result = {'numberofcl': self.clust_numbers, 'clust_array': self.clust_array}
        return result

    def load_parameters(self, parameters):
        if "numberofcl" in parameters and parameters["numberofcl"] is not None:
            self.clust_numbers = parameters["numberofcl"]
        else:
            self.clust_numbers = CLUST_NUM

        if "clust_array" in parameters and parameters["clust_array"] is not None:
            self.clust_array = parameters["clust_array"]
        else:
            self.clust_array = CLUST_ARRAY
        return True

    def save_results(self):
        return {'results': self.results.tolist(), 'cent': self.cent.tolist(), 'dump': pickle.dumps(self.model).hex()}

    def load_results(self, results_dict):
        if 'results' in results_dict and results_dict['results'] is not None:
            self.results = np.array(results_dict['results'])
        if 'cent' in results_dict and results_dict['cent'] is not None:
            self.cent = np.array(results_dict['cent'])
        if 'dump' in results_dict and results_dict['dump'] is not None:
            self.model = pickle.loads(bytes.fromhex(results_dict['dump']))
        return True

    def print_parameters(self):
        result = {'numberofcl': self.clust_numbers, 'clust_array': self.clust_array}
        return result

    def process_data(self, dataset):
        dataset_cut = (dataset.loc[:, self.clust_array], dataset)[self.clust_array is None]

        self.model = KMeans(self.clust_numbers)
        self.model.fit(dataset_cut)
        self.results = self.model.predict(dataset_cut)
        self.cent = self.model.cluster_centers_
        return self.results

    def predict(self, dataset):
        return self.model.predict(dataset.loc[:, self.clust_array])

try:
    baseoperationclass.register(KMeansClustering)
except ValueError as error:
    print(repr(error))
