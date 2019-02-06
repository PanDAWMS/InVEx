from sklearn.cluster import KMeans
import pandas as pd
import numpy as np

class LoDGenerator:

    def __init__(self, dataset, n = 200):
        self.dataset = dataset.copy()
        self.initialLength = self.dataset.shape[0]
        self.n = n
        self.kmeans_clustering()
        self.groups_mean = self.get_groups_mean()
        self.groups2id = self.groups_to_ids()

    def kmeans_clustering(self):
        self.model = KMeans(self.n)
        self.model.fit(self.dataset)
        self.results = self.model.predict(self.dataset)
        self.dataset['group'] = self.results
        self.dataset.set_index('group')

    def groups_to_ids(self):
        result = []
        clusters = self.dataset.groupby('group')
        for name, group in clusters:
            group_size = len(group)
            percentage = group_size * 100 / self.initialLength
            result.append([name, group.index.tolist(), len(group), percentage])
        return result

    def get_groups_mean(self):
        return self.dataset.groupby('group').mean()

# dataset = pd.DataFrame(np.random.randint(0,500,size=(500, 4)), columns=list('ABCD'))
#
# lod = LoDGenerator(dataset, 5)
# print(lod.initialLength)
# print(lod.groups_mean)
# print(lod.groups2id)
