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

    def __init__(self, dataset, mode=MODE_DEFAULT, num_groups=None, features=None, **kwargs):
        """
        Initialization.

        :param dataset: Input data sample
        :type dataset: pandas.DataFrame
        :param num_groups: Level of Detail value.
        :type num_groups: int/None
        :param features: List of features used for grouping.
        :type features: list/None

        :keyword mode: Mode of grouping (default: minibatch).
        """
        self.dataset = dataset.copy()
        self.num_initial_elements = self.dataset.shape[0]
        self.grouped_dataset = None

        self._init_metadata = {'mode': mode,
                               'value': num_groups or NUM_GROUPS_DEFAULT,
                               'features': features}
        self._groups_metadata = []
        self.set_groups()

    def set_groups(self, **kwargs):
        """
        Create groups of provided objects (from dataset).

        :keyword mode: Mode of grouping.
        :keyword num_groups: Number of resulting groups.
        :keyword features: List of selected features used for grouping.
        """
        mode = kwargs.get('mode', self._init_metadata['mode'])
        num_groups = kwargs.get('num_groups', self._init_metadata['value'])
        features = kwargs.get('features', self._init_metadata['features'])

        if mode == 'minibatch':
            group_labels = self._get_labels_kmeans_clustering(
                n_clusters=num_groups,
                features=features)
            self.group_name = 'group'
            self.dataset[self.group_name] = group_labels
            self.dataset.set_index(self.group_name)
            self.grouped_dataset = self._get_groups_mean()
            self._update_groups_metadata()
        elif mode == 'param':
            self.group_name = features[0]
            self.grouped_dataset = self._get_groups_mean()
            self._update_groups_metadata()
        else:
            raise NotImplementedError


    def _get_labels_kmeans_clustering(self, n_clusters, features=None):
        data = self.dataset if not features else self.dataset.loc[:, features]
        return MiniBatchKMeans(n_clusters=n_clusters,
                               **MINIBATCH_PARAMS_DEFAULT).fit_predict(data)

    def _parameter_grouping(self, feature):
        self.grouped_dataset = self.dataset.groupby(feature)

    def _get_groups_mean(self):
        return self.dataset.groupby(self.group_name).mean()

    def _update_groups_metadata(self):
        if self.grouped_dataset is not None:

            if self._groups_metadata:
                del self._groups_metadata[:]

            grouped = self.dataset.groupby(self.group_name)
            for i in sorted(grouped.groups.keys()):
                group = grouped.get_group(i)
                self._groups_metadata.append(
                    [i, group.index.tolist(), len(group),
                     log1p(len(group) * 100 / self.num_initial_elements)])

    def get_full_metadata(self):
        output = dict(self._init_metadata)
        output['groups'] = self._groups_metadata
        return output

    def get_groups_metadata(self):
        return self._groups_metadata
