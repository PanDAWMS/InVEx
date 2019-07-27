import time
from datetime import timedelta
from importlib import import_module
import pandas as pd


N_RUNS = 10

parameters = {
    "KMeansClustering": (5, []),
    "MiniBatchKMeansClustering": (5, 200),
    "DBScanClustering": (5, 0.5),
    "KPrototypesClustering": (5, None)
}
results = {
    "KMeansClustering": [],
    "MiniBatchKMeansClustering": [],
    "DBScanClustering": [],
    "KPrototypesClustering": []
}

def numeric_columns_from_csv(filename):
    dataset = pd.read_csv(filename)
    return dataset.select_dtypes(include=('int64', 'float64', 'int32', 'float32', 'int', 'float'))

def benchmark_algorithm(algorithm_name, algorithm_parameters, dataset):
    algorithm_module = import_module("..." + algorithm_name, package=__name__)
    algorithm = getattr(algorithm_module, algorithm_name)
    algorithm_instance = algorithm()
    algorithm_instance.set_parameters(*(parameters[algorithm_name]))
    start_time = time.monotonic()
    algorithm_instance.process_data(dataset)
    end_time = time.monotonic()
    return timedelta(microseconds=((end_time - start_time) * 1000))

def run_benchmarks():
    dataset = numeric_columns_from_csv("../datasets/test.csv")
    for algorithm_name, algorithm_parameters in parameters.items():
        for i in range(0, N_RUNS):
            elapsed_time = benchmark_algorithm(algorithm_name, algorithm_parameters, dataset)
            results[algorithm_name].append(elapsed_time.microseconds)
    for algorithm_name, result in results.items():
        print(f"{algorithm_name}: {sum(result) / N_RUNS} ms")

if __name__ == "__main__":
    run_benchmarks()