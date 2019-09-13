from . import baseoperationclass
from sklearn.cluster import MiniBatchKMeans
import numpy as np
import pickle

CLUST_NUM = 5
BATCH_SIZE = 200


class MiniBatchKMeansClustering(baseoperationclass.BaseOperationClass):

    _operation_name = 'MiniBatch K-Means Clustering'
    _operation_code_name = 'MiniBatchKMeans'
    _type_of_operation = 'cluster'

    def __init__(self):
        super().__init__()
        self.clust_numbers = CLUST_NUM
        self.batch_size = BATCH_SIZE
        self.model = None
        self.results = None
        self.cent = None

    def set_parameters(self, clust_numbers, batch_size):
        if clust_numbers is not None:
            self.clust_numbers = clust_numbers
        if batch_size is not None:
            self.batch_size = batch_size
        return True

    def save_parameters(self):
        return {'cluster_number': self.clust_numbers, 'batch_size': self.batch_size}

    def load_parameters(self, parameters):
        if parameters.get("cluster_number") is not None:
            self.clust_numbers = parameters["cluster_number"]
        else:
            self.clust_numbers = CLUST_NUM
        if parameters.get("batch_size") is not None:
            self.batch_size = parameters["batch_size"]
        else:
            self.batch_size = BATCH_SIZE
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
        result = {'cluster_number': self.clust_numbers, 'batch_size': self.batch_size}
        return result

    def process_data(self, dataset):
        # I'm using normalised center change instead of mini batches not yielding improvement
        # as an early stopping heuristics for the results to be closer to original K-Means.
        # It includes a slight overhead though, so it should be reverted if perfomance is a priority.
        self.model = MiniBatchKMeans(n_clusters=self.clust_numbers, batch_size=self.batch_size, tol=1e-5, max_no_improvement=None)
        self.model.fit(dataset)
        self.results = self.model.predict(dataset)
        self.cent = self.model.cluster_centers_
        return self.results

    def predict(self, dataset):
        return self.model.predict(dataset)


try:
    baseoperationclass.register(MiniBatchKMeansClustering)
except ValueError as error:
    print(repr(error))
