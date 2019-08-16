from math import log1p

from sklearn.cluster import MiniBatchKMeans
import pandas as pd

from .KPrototypesClustering import KPrototypesClustering


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
            self.group_features = '_cluster_number'
            self.dataset[self.group_features] = group_labels
            self.dataset.set_index(self.group_features)
            self.grouped_dataset = self._get_groups_mean()
            self._update_groups_metadata()
        elif mode == 'kprototypes':
            group_labels = self._get_labels_kprototypes_clustering(
                n_clusters=num_groups,
                categorical_weight=None,
                features=features)
            self.group_features = '_cluster_number'
            self.dataset[self.group_features] = group_labels
            self.grouped_dataset = self._get_groups_mean()
            self._update_groups_metadata()
        elif mode == 'param_categorical':
            self.group_features = features
            self.grouped_dataset = self._get_groups_mean()
            self._update_groups_metadata()
        elif mode == 'param_num_continuous':
            curr_variable = self.dataset[features[0]].max()
            intervals = self.set_intervals(curr_variable)
            group_number = -1
            self.group_features = str(features[0]) + '_intervals'

            if self._groups_metadata:
                del self._groups_metadata[:]

            self.grouped_dataset = pd.DataFrame()

            for i in intervals:
                group_number += 1
                group = self.dataset[((self.dataset[features[0]] >= i[0]) & (self.dataset[features[0]] < i[1]))]
                group_meta = {}
                group_meta['group_name'] = str(round(i[0], 2)) + '-' + str(round(i[1], 2))
                group_meta['group_number'] = group_number
                group_meta['group_indexes'] = group.index.tolist()
                group_meta['group_length'] = len(group)
                group_meta['group_koeff'] = log1p(len(group) * 100 / self.num_initial_elements)
                self._groups_metadata.append(group_meta)
                group_mean = self.f(group)
                group_mean[self.group_features] = group_meta['group_name']
                self.grouped_dataset = self.grouped_dataset.append(group_mean, ignore_index=True)
            self.grouped_dataset.set_index(self.group_features, inplace=True)
        else:
            raise NotImplementedError

    def set_intervals(self, number):
        part = number / self._init_metadata['value']
        return [(i * part, (i + 1) * part) for i in range(self._init_metadata['value'])]

    def _get_labels_kmeans_clustering(self, n_clusters, features=None):
        data = self.dataset if not features else self.dataset.loc[:, features]
        return MiniBatchKMeans(n_clusters=n_clusters,
                               **MINIBATCH_PARAMS_DEFAULT).fit_predict(data)

    def _get_labels_kprototypes_clustering(self, n_clusters, categorical_weight=None, features=None):
        data = self.dataset if not features else self.dataset.filter(items=features)
        algorithm = KPrototypesClustering()
        algorithm.set_parameters(n_clusters, categorical_weight)
        return algorithm.process_data(data)

    def f(self, data):
        columns_dict = {}
        for i in data.columns:
            if (data[i].dtype.name in ['int64', 'float64', 'int32', 'float32', 'int', 'float']):
                columns_dict[i] = data[i].mean()
            else:
                unique_values = data[i].unique()
                columns_dict[i] = "%s" % ', '.join(unique_values)
        return pd.Series(dict(columns_dict))

    def _get_groups_mean(self):
        result = self.dataset.groupby(self.group_features).apply(self.f)
        # We cannot drop self.group_features if we group by it, cause in that case it serves as an index
        try:
            result = result.drop(self.group_features, axis=1)
        except KeyError:
            pass
        return result
        # return self.dataset.groupby(self.group_features).mean()

    def _update_groups_metadata(self):
        """
        Groups metadata is set in a form of list of dictionaries:
        for each groups:
        - group_name
        - group_number
        - group_indexes
        - group_length
        - group_koeff
        :return:
        """
        if self.grouped_dataset is not None:

            if self._groups_metadata:
                del self._groups_metadata[:]

            grouped = self.dataset.groupby(self.group_features)

            # assotiate groups with ordinal numbers
            group_number = -1
            # store in groups metadata original groups with its numbers
            for name, group in grouped:
                group_number += 1
                group_meta = {}
                group_meta['group_name'] = str(name)
                group_meta['group_number'] = group_number
                group_meta['group_indexes'] = group.index.tolist()
                group_meta['group_length'] = len(group)
                group_meta['group_koeff'] = log1p(len(group) * 100 / self.num_initial_elements)
                self._groups_metadata.append(group_meta)

    def get_full_metadata(self):
        output = dict(self._init_metadata)
        output['groups'] = self._groups_metadata
        return output

    def get_groups_metadata(self):
        return self._groups_metadata
