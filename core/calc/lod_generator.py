from math import log1p

from sklearn.cluster import MiniBatchKMeans

MINIBATCH_PARAMS_DEFAULT = {
    'random_state': 0,
    'batch_size': 6,
    'max_iter': 10,
    'init_size': 3000
}
MODE_DEFAULT = 'minibatch'
NUM_GROUPS_DEFAULT = 100


class LoDGenerator:

    """
    Level-of-Detail Generator class provides grouping of the initial
    [large] data sample (default grouping mode is k-means clustering).
    """

    def __init__(self, dataset, num_groups=None, features=None, **kwargs):
        self.dataset = dataset.copy()
        self.num_initial_elements = self.dataset.shape[0]
        self.num_groups = num_groups or NUM_GROUPS_DEFAULT

        self.grouped_dataset = None  # init
        self.groups_metadata = None  # init

        self.set_groups(mode=kwargs.get('mode', MODE_DEFAULT),
                        selected_features=features)

    def set_groups(self, mode, selected_features=None):
        """
        Create groups of provided objects (from dataset)

        :param mode: Mode of grouping (default: minibatch).
        :type mode: str
        :param selected_features: List of features used for grouping.
        :type: list/None
        """
        if mode == 'minibatch':
            group_labels = self._get_labels_kmeans_clustering(
                features=selected_features)
        else:
            raise NotImplementedError
        self.dataset['group'] = group_labels
        self.dataset.set_index('group')

        self.grouped_dataset = self.get_groups_mean()
        self.groups_metadata = self.get_groups_metadata()

    def _get_labels_kmeans_clustering(self, features=None):
        data = self.dataset if not features else self.dataset.loc[:, features]
        return MiniBatchKMeans(n_clusters=self.num_groups,
                               **MINIBATCH_PARAMS_DEFAULT).fit_predict(data)

    def get_groups_metadata(self):
        output = []
        grouped = self.dataset.groupby('group')
        for i in sorted(grouped.groups.keys()):
            group = grouped.get_group(i)
            output.append([i, group.index.tolist(), len(group),
                           log1p(len(group) * 100 / self.num_initial_elements)])
        return output

    def get_groups_mean(self):
        return self.dataset.groupby('group').mean()
