from sklearn import preprocessing
from sklearn.impute import SimpleImputer
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import os
import errno
from django.conf import settings
import json

class DatasetInfo():

    def __init__(self):
        pass

    def get_info_from_dataset(self, df, dsID):
        """
        Prepare dataset object and gathering dataset information from the POST request:
        - cleaning initial dataset from rows and columns where all elements are NaN
        - assigning parameters from POST request to dataset object
        :param df:
        :param dsID:
        :param filepath:
        :return:
        """
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(axis=0, how='all', inplace=True)
        self.dsID = dsID
        self.get_dataset_stats(df)
        self.description = ''
        self.features = self.from_dataframe(df)

    def update_dataset_info(self, dsID, index_name, features, num_records):
        """
        Update Dataset Info from clients panel
        :param dsID:
        :param index_name:
        :param filepath:
        :param features:
        :param num_records:
        :return:
        """
        self.dsID = dsID
        self.index_name = index_name
        self.features = features
        self.num_records = num_records

    # TODO
    # def save_to_redis(self):
    #     pass

    def drop_nan_column(self, df, column):
        """
        Drop column if the number of NaNs exceeds 50%
        :param df:
        :param column:
        :return:
        """
        if (df[column].isna().sum() / df[column].count()) > 0.5:
            df.drop(column, 1, inplace=True)

    def get_dataset_stats(self, df):
        """
        Gathering initial statistics from pandas.DataFrame object
        :param df:
        :return:
        """
        self.num_records = df.shape[0]
        self.index_name = df.index.name

    def from_dataframe(self, df):
        """
        Gathering statistics for all pandas.DataFrame columns
        :param df:
        :return array of FeatureStatistics objects:
        """
        features = []
        # df_scaled = self.df_scaler(df)
        for column in df:
            _name = column
            _type = df[column].dtype.name
            _percentage_missing = self.get_percentage_missing(df, column)
            _count = df[column].shape[0]

            _is_numeric = self.is_numeric(df[column])
            _is_cat = self.likely_cat(df[column],_type)
            _is_object = self.is_object(df[column])

            _measures_type = 'unknown'

            if _is_numeric and _is_cat:
                _measure_type = 'ordinal'
            elif _is_numeric and not _is_cat:
                _measure_type = 'continuous'
            if _is_object:
                _measure_type = 'nominal'

            if _is_numeric:
                if _is_cat:
                    _unique_values = df[column].dropna().unique().tolist()
                    _distribution = self.unique_values_distribution(df[column])
                    features.append(FeatureStatistics(feature_name=_name,
                                                      feature_type=_type,
                                                      measure_type=_measure_type,
                                                      count=_count,
                                                      unique_values=_unique_values,
                                                      unique_number=len(_unique_values),
                                                      distribution=_distribution,
                                                      percentage_missing=_percentage_missing,
                                                      enabled='false'))
                else:
                    _min = df[column].min()
                    _max = df[column].max()
                    _mean = df[column].mean()
                    _q10 = df[column].quantile(0.1)
                    _q25 = df[column].quantile(0.25)
                    _q50 = df[column].quantile(0.5)
                    _q75 = df[column].quantile(0.75)
                    _q90 = df[column].quantile(0.9)
                    _std = df[column].std()
                    # _scaled_min = df_scaled[column].min()
                    # _scaled_max = df_scaled[column].max()
                    # _scaled_mean = df_scaled[column].mean()
                    # _scaled_std = df_scaled[column].std()
                    # _scaled_q10 = df_scaled[column].quantile(0.1)
                    # _scaled_q25 = df_scaled[column].quantile(0.25)
                    # _scaled_q50 = df_scaled[column].quantile(0.5)
                    # _scaled_q75 = df_scaled[column].quantile(0.75)
                    # _scaled_q90 = df_scaled[column].quantile(0.9)
                    features.append(FeatureStatistics(feature_name=_name,
                                                      feature_type=_type,
                                                      measure_type=_measure_type,
                                                      count=_count,
                                                      min=_min,
                                                      max=_max,
                                                      mean=_mean,
                                                      std=_std,
                                                      q10=_q10,
                                                      q25=_q25,
                                                      q50=_q50,
                                                      q75=_q75,
                                                      q90=_q90,
                                                      percentage_missing=_percentage_missing,
                                                      enabled='true'))
                                                      # scaled_max=_scaled_max * 100,
                                                      # scaled_min=float(_scaled_min) * 100,
                                                      # scaled_mean=_scaled_mean * 100,
                                                      # scaled_std=_scaled_std * 100,
                                                      # scaled_q10=_scaled_q10 * 100,
                                                      # scaled_q25=_scaled_q25 * 100,
                                                      # scaled_q50=_scaled_q50 * 100,
                                                      # scaled_q75=_scaled_q75 * 100,
                                                      # scaled_q90=_scaled_q90 * 100))
            if _is_object:
                result = self.to_datetime(column, df[column])
                _unique_number = len(df[column].dropna().unique().tolist())
                _distribution = {}
                if result is not None:
                    _unique_values = [result.min().isoformat(), result.max().isoformat()]
                    _measure_type = 'range'
                else:
                    if _is_cat:
                        _unique_values = df[column].dropna().unique().tolist()
                    #if _is_cat:
                        _distribution = df[column].value_counts().to_dict()
                    elif not _is_cat:
                        _unique_values = df[column].dropna().unique().tolist()[:10]
                    #    _unique_values = self.process_strings(_unique_values)
                        _measure_type = 'non-categorical'
                features.append(FeatureStatistics(feature_name=_name,
                                                  feature_type=_type,
                                                  measure_type=_measure_type,
                                                  count=_count,
                                                  unique_values=_unique_values,
                                                  unique_number=_unique_number,
                                                  distribution=_distribution,
                                                  percentage_missing=_percentage_missing,
                                                  enabled='false'))
        return features

    def unique_values_distribution(self, data):
        """
        Generating pandas.Series with frequencies of unique column values
        :param data: pandas.Series
        :return:
        """
        return {str(k): v for k, v in data.value_counts().to_dict().items()}
        #return {str(k): str(k) for k, v in data.value_counts().to_dict().items()}

    def to_datetime(self, column, data):
        """
        Convert all pandas.DataFrame columns, which names contains
        'datetime'-related words to datetime datatype
        :param column: column name
        :param data: pandas.Series
        :return: - None if column doesn't have 'datetime'-related words,
                 - pandas.Series if column has been successfully
                 converted to datetime datatype
        """
        names = ["time", "date", "datetime", "start", "end"]
        if any(st in column for st in names):
            try:
                return pd.to_datetime(data.dropna())
            except ValueError as e:
                return None

    def likely_cat(self, data, type):
        """
        Checking if column values look like categorical.
        - 'object' datatypes - almost all such columns can be categorical
        - numerical datatypes - if the number of unique numerical values exceeds 30,
                                such column treated as continuous (or ratio)
                              - if the number of unique numerical values < 30,
                                such column treated as categorical.
        :param data: pandas.Series
        :param type: column datatype
        :return:
        """
        if type == 'object':
            return 1. * data.nunique() / data.count() < 0.1
        else:
            return 1. * data.nunique() / data.count() < 0.1
            # if len(data.dropna().unique().tolist()) <= 50:
            #     return  1. * data.nunique() / data.count() < 0.03
            # else:
            #     return False
            # top_n = 10
            # return 1. * data.value_counts(normalize=True).head(top_n).sum() > 0.8

    def process_strings(self, data):
        """
        K-means clusterization of strings.
        If the number of 'object' datatype unique values too big,
        we can't deal with it as with categorical.
        Instead, the k-means clusterization are applied to all column values,
        to search for clusters sharing the same terms.
        :param data: pandas.Series
        :return: clustered array of terms
        """
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(data)

        true_k = 10
        model = KMeans(n_clusters=true_k, init='k-means++', max_iter=100, n_init=1)
        model.fit(X)

        order_centroids = model.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names()
        clusters = []
        for i in range(true_k):
            cluster_str = ''
            for ind in order_centroids[i, :10]:
                cluster_str += terms[ind] + ' '
            clusters.append(cluster_str)
        return clusters

    def df_scaler(self, df):
        df_numeric = df._get_numeric_data()
        imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
        df_imputer = pd.DataFrame(imputer.fit_transform(df_numeric), columns=df_numeric.columns)
        scaler = preprocessing.MinMaxScaler()
        scaled_df = scaler.fit_transform(df_imputer)
        scaled_df = pd.DataFrame(scaled_df, columns=df_imputer.columns)
        return scaled_df

    def is_numeric(self, data):
        """
        Checking if column is numerical.
        :param data: pandas.Series
        :return:
        """
        return data.dtype.name in ['int64', 'float64', 'int32', 'float32', 'int', 'float']

    def is_object(self, data):
        """
        Checking if column is object.
        :param data: pandas.Series
        :return:
        """
        return data.dtype.name == 'object'

    def is_datetime(self, data):
        """
        Checking if column is datetime.
        :param data: pandas.Series
        :return:
        """
        data.dtype.name == 'datetime64'

    def get_percentage_missing(self, df, column):
        """ Calculates percentage of NaN values in DataFrame column
        :param df: Pandas DataFrame object
        :param column: name of DataFrame column
        :return: float
        """
        return (np.count_nonzero(df[column].isnull()) * 100) / len(df[column])

    def silentremove(self, filename):
        try:
            os.remove(filename)
        except OSError as e:  # this would be "except OSError, e:" before Python 2.6
            if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
                raise  # re-raise exception if a different error occurred

    def save_to_file(self):
        filename = os.path.join(settings.MEDIA_ROOT, self.dsID, self.dsID + '.stat')
        self.silentremove(filename)
        file = open(filename, "w")
        data = {}
        data['dsID'] = self.dsID
        data['num_records'] = self.num_records
        data['index_name'] = self.index_name
        data['features'] = json.loads(pd.DataFrame.from_records([f.__dict__ for f in self.features]).T.to_json())
        file.write(json.dumps(data))
        file.close()


class FeatureStatistics():

    def __init__(self, **kwargs):
        for attr in ['feature_name','feature_type','count','min','max','distribution','measure_type','unique_number',
                     'unique_values','mean','std','q10','q25','q50','q75','q90','percentage_missing',
                     'scaled_min', 'scaled_max', 'scaled_mean', 'scaled_std',
                     'scaled_q10', 'scaled_q25', 'scaled_q50', 'scaled_q75', 'scaled_q90','enabled'
                     ]:
            if attr in kwargs:
                self.__setattr__(attr, kwargs.get(attr))

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)