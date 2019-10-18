
from math import log1p

import pandas as pd

from . import (
    DAALKMeansClustering,
    KPrototypesClustering,
    MiniBatchKMeansClustering)

MODE_DEFAULT = 'minibatch'
NUM_GROUPS_DEFAULT = 100
CLUSTERING_BY_MODE = {
    'minibatch': MiniBatchKMeansClustering.MiniBatchKMeansClustering,
    'kprototypes': KPrototypesClustering.KPrototypesClustering,
    'daal': DAALKMeansClustering.DAALKMeansClustering
}


class LoDGenerator:

    """
    Level-of-Detail Generator class provides grouping of the initial
    [large] data sample (default grouping mode is k-means clustering).
    """

    def __init__(self, dataset, mode=None, num_groups=None, features=None):
        """
        Initialization.

        :param dataset: Input data sample.
        :type dataset: pandas.DataFrame
        :param mode: Mode of grouping (default: minibatch).
        :type mode: str/None
        :param num_groups: Level of Detail value.
        :type num_groups: int/None
        :param features: List of features used for grouping.
        :type features: list/None
        """
        self.dataset = dataset.copy()
        self.num_initial_elements = self.dataset.shape[0]
        self.grouped_dataset = None
        self.grouping_key = 'group_id'

        self._init_metadata = {'mode': mode or MODE_DEFAULT,
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

        if mode in CLUSTERING_BY_MODE:
            self.grouping_key = '_cluster_id'

            clustering_ = CLUSTERING_BY_MODE[mode]()
            clustering_.set_parameters(num_groups)
            self.dataset[self.grouping_key] = clustering_.process_data(
                self.dataset if not features
                else self.dataset.loc[:, features])

            if mode != 'kprototypes':
                self.dataset.set_index(self.grouping_key)

            self.grouped_dataset = self._get_groups_mean()
            self._update_groups_metadata(
                groups=self.dataset.groupby(self.grouping_key))

        elif mode == 'param_categorical':
            self.grouping_key = features
            self.grouped_dataset = self._get_groups_mean()
            self._update_groups_metadata(
                groups=self.dataset.groupby(self.grouping_key))

        elif mode == 'param_num_continuous':
            selected_feature = features[0]
            self.grouping_key = f'{selected_feature}_intervals'
            self.grouped_dataset = pd.DataFrame()

            groups = []
            for i in self.get_intervals(self.dataset[selected_feature].max()):
                group = self.dataset[((self.dataset[selected_feature] >= i[0]) &
                                      (self.dataset[selected_feature] < i[1]))]
                name = f'{i[0]}-{i[1]}'
                group_mean = self.f(group)
                group_mean[self.grouping_key] = name
                self.grouped_dataset = self.grouped_dataset.append(
                    group_mean, ignore_index=True)

                groups.append((name, group))

            self.grouped_dataset.set_index(self.grouping_key, inplace=True)
            self._update_groups_metadata(groups=groups)

        else:
            raise NotImplementedError

    def get_intervals(self, max_value):
        dur_ = max_value / self._init_metadata['value']
        return [(i * dur_, (i + 1) * dur_)
                for i in range(self._init_metadata['value'])]  # TODO: Re-work

    def f(self, data):
        columns_dict = {}
        for i in data.columns:
            if (data[i].dtype.name in
                    ['int64', 'float64', 'int32', 'float32', 'int', 'float']):
                columns_dict[i] = data[i].mean()
            else:
                columns_dict[i] = ', '.join(data[i].unique())
        return pd.Series(dict(columns_dict))

    def _get_groups_mean(self):
        result = self.dataset.groupby(self.grouping_key).apply(self.f)
        # We cannot drop self.group_features if we group by it,
        # cause in that case it serves as an index
        try:
            result = result.drop(self.grouping_key, axis=1)
        except KeyError:
            pass
        return result
        # return self.dataset.groupby(self.group_features).mean()

    def _update_groups_metadata(self, groups):
        """
        Groups metadata is set in a form of list of dictionaries:
        for each groups:
        - group_name
        - group_number
        - group_indexes
        - group_length
        - group_koeff
        """
        if self.grouped_dataset is not None:

            if self._groups_metadata:
                del self._groups_metadata[:]

            # store in groups metadata original groups with its numbers
            for idx, (name, group) in enumerate(groups):
                self._groups_metadata.append({
                    'group_name': str(name),
                    'group_number': idx,
                    'group_indexes': group.index.tolist(),
                    'group_length': len(group),
                    'group_koeff': log1p(len(group) * 100 /
                                         self.num_initial_elements)})

    def get_full_metadata(self):
        output = dict(self._init_metadata)
        output['groups'] = self._groups_metadata
        return output

    def get_groups_metadata(self):
        return self._groups_metadata
