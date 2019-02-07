from sklearn.cluster import KMeans
import pandas as pd
import numpy as np

class LoDGenerator:
    """
    Level-of-Detail Generator class provides k-means clusterization 
    of the initial data sample into a number of clusters. 
    """

    def __init__(self, dataset, n = 200):
        self.dataset = dataset.copy()
        self.initialLength = self.dataset.shape[0]
        self.n = n
        self.kmeans_clustering()
        self.grouped_dataset = self.get_groups_mean()
        self.groups_metadata = self.get_groups_metadata()

    def kmeans_clustering(self):
        self.model = KMeans(self.n)
        self.model.fit(self.dataset)
        self.results = self.model.predict(self.dataset)
        self.dataset['group'] = self.results
        self.dataset.set_index('group')

    def get_groups_metadata(self):
        result = []
        self.clusters = self.dataset.groupby('group')
        for i in sorted(self.clusters.groups.keys()):
            group = self.clusters.get_group(i)
            group_size = len(group)
            percentage = group_size * 100 / self.initialLength
            result.append([i, group.index.tolist(), len(group), percentage])
        return result

    def get_group(self, group_name):
        return self.clusters.get_group(group_name)

    def get_groups_mean(self):
        return self.dataset.groupby('group').mean()


dataset = pd.DataFrame(np.random.randint(0,100,size=(100, 4)), columns=list('ABCD'))
print(dataset)
lod = LoDGenerator(dataset, 5)
print(lod.initialLength)
print(lod.grouped_dataset)
print(lod.groups_metadata)
