from . import baseoperationclass
import pandas as pd


DESCRIPTION = ['Count', 'Min', 'Max', 'Mean', 'Std', '25%', '50%', '75%', 'Sum', 'Skew', 'Median']


class BasicStatistics(baseoperationclass.BaseOperationClass):
    _operation_name = "BasicStats"
    _type_of_operation = 'calculation'

    def __init__(self):
        self.results = None

    def process_data(self, dataset):
        self.results = [dataset.count(), dataset.min(), dataset.max(), dataset.mean(), dataset.std(), dataset.quantile(0.25),
                        dataset.quantile(0.5), dataset.quantile(0.75), dataset.sum(), dataset.skew(),
                        dataset.median()]
        return self.results

    def save_results(self):
        dict = {}
        for i in range(len(self.results)):
            dict[i] = self.results[i].to_json()
        return {'results': dict}

    def load_results(self, results_dict):
        if 'results' in results_dict and results_dict['results'] is not None:
            try:
                self.results = [pd.read_json(results_dict['results'][0], typ='series'),
                                pd.read_json(results_dict['results'][1], typ='series'),
                                pd.read_json(results_dict['results'][2], typ='series'),
                                pd.read_json(results_dict['results'][3], typ='series'),
                                pd.read_json(results_dict['results'][4], typ='series'),
                                pd.read_json(results_dict['results'][5], typ='series'),
                                pd.read_json(results_dict['results'][6], typ='series')]
            except Exception:
                self.results = [pd.read_json(results_dict['results']['0'], typ='series'),
                                pd.read_json(results_dict['results']['1'], typ='series'),
                                pd.read_json(results_dict['results']['2'], typ='series'),
                                pd.read_json(results_dict['results']['3'], typ='series'),
                                pd.read_json(results_dict['results']['4'], typ='series'),
                                pd.read_json(results_dict['results']['5'], typ='series'),
                                pd.read_json(results_dict['results']['6'], typ='series')]
        return True


try:
    baseoperationclass.register(BasicStatistics)
except ValueError as error:
    print(repr(error))
