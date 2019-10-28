let clustering_parameters = [
    ['KMeans',
        'KMeans',
        {
            'name': 'numberofcl_KMeans',
            'label': 'Number of clusters',
            'type': 'integer',
            'attributes': [['placeholder', '5']],
            'defvalue': '5',
            'min': 1,
            'max': 40
        }],
    ['MiniBatchKMeans',
        'MiniBatchKMeans',
        {
            'name': 'numclusters_MiniBatchKMeans',
            'label': 'Number of clusters',
            'type': 'integer',
            'attributes': [['placeholder', '5']],
            'defvalue': '5',
            'min': 1,
            'max': 40
        },
        {
            'name': 'batchsize_MiniBatchKMeans',
            'label': 'Number of samples in minibatch',
            'type': 'integer',
            'attributes': [['placeholder', '100']],
            'defvalue': '100',
            'min': 5,
            'max': 99999
        }],
    ['DAALKMeans',
        'DAALKMeans',
        {
            'name': 'numclusters_DAALKMeans',
            'label': 'Number of clusters',
            'type': 'integer',
            'attributes': [['placeholder', '5']],
            'defvalue': '5',
            'min': 1,
            'max': 100
        }],
    ['KPrototypes',
        'KPrototypes',
        {
            'name': 'cluster_number_KPrototypes',
            'label': 'Number of clusters',
            'type': 'integer',
            'attributes': [['placeholder', '5']],
            'defvalue': '5',
            'min': 1,
            'max': 40
        },
        {
            'name': 'categorical_data_weight_KPrototypes',
            'label': 'Weight of categorical data in distance',
            'type': 'float',
            'attributes': [['placeholder', 'Enter negative weight to calculate automatically']],
            'min': -10000,
            'max': 10000
        }],
    ['Hierarchical',
        'Hierarchical',
        {
            'name': 'cluster_number_Hierarchical',
            'label': 'Number of clusters',
            'type': 'integer',
            'attributes': [['placeholder', '5']],
            'defvalue': '5',
            'min': 1,
            'max': 40
        },
        {
            'name': 'categorical_data_weight_Hierarchical',
            'label': 'Weight of categorical data in distance',
            'type': 'float',
            'attributes': [['placeholder', 'Enter negative weight to calculate automatically']],
            'min': -10000,
            'max': 10000
        }],
    ['DBSCAN',
        'DBSCAN',
        {
            'name': 'min_samples_DBSCAN',
            'label': 'min_samples',
            'type': 'integer',
            'attributes': [['placeholder', '5']],
            'defvalue': '5',
            'min': 1,
            'max': 200
        },
        {
            'name': 'eps_DBSCAN',
            'label': 'epsilon',
            'type': 'float',
            'attributes': [['placeholder', '0.5']],
            'defvalue': '0.5',
            'min': 0,
            'max': 50
        }],
    ['GroupData',
        'GroupData',
        {
            'name': 'feature_name_GroupData',
            'label': 'feature name',
            'type': 'list',
            'attributes': [['placeholder', '']],
            'values': get_categorical_features_names()
        }]
];