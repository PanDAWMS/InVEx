import time
from datetime import timedelta
from importlib import import_module
import pprofile
import pandas as pd
import re


parameters = {
    "KMeansClustering": (5, []),
    "MiniBatchKMeansClustering": (5, 200),
    "DBScanClustering": (5, 0.5),
    "HierarchicalClustering": (5, None),
    "KPrototypesClustering": (5, None)
}
results = {
    "KMeansClustering": [],
    "MiniBatchKMeansClustering": [],
    "DBScanClustering": [],
    "HierarchicalClustering": [],
    "KPrototypesClustering": []
}


def _numeric_columns_from_csv(filename):
    dataset = pd.read_csv(filename)
    return dataset.select_dtypes(include=('int64', 'float64', 'int32', 'float32', 'int', 'float'))


def _benchmark_algorithm(algorithm_name, dataset):
    algorithm_module = import_module("..." + algorithm_name, package=__name__)
    algorithm = getattr(algorithm_module, algorithm_name)
    algorithm_instance = algorithm()
    algorithm_instance.set_parameters(*(parameters[algorithm_name]))
    start_time = time.monotonic()
    algorithm_instance.process_data(dataset)
    end_time = time.monotonic()
    return timedelta(microseconds=((end_time - start_time) * 1000))


def run_benchmarks(n_runs, filename):
    dataset = _numeric_columns_from_csv(filename)
    dataset.dropna(axis=0, how='any', inplace=True)
    for algorithm_name in parameters:
        for i in range(0, n_runs):
            elapsed_time = _benchmark_algorithm(algorithm_name, dataset)
            print(f"{algorithm_name[:-10]} - Run №{i + 1} done in {elapsed_time.microseconds} ms")
            results[algorithm_name].append(elapsed_time.microseconds)
    for algorithm_name, result in results.items():
        print(f"{algorithm_name}: {sum(result) / n_runs} ms")


def dendrogram(filename):
    dataset = _numeric_columns_from_csv(filename)
    dataset.dropna(axis=0, how='any', inplace=True)
    algorithm_module = import_module("..." + "HierarchicalClustering", package=__name__)
    algorithm = getattr(algorithm_module, "HierarchicalClustering")
    algorithm_instance = algorithm()
    algorithm_instance.set_parameters(5, None)
    algorithm_instance.find_linkage(dataset)
    algorithm_instance.dendrogram()


def profile_algorithm(algorithm_name, filename):
    dataset = _numeric_columns_from_csv(filename)
    dataset.dropna(axis=0, how='any', inplace=True)

    prof = pprofile.Profile()
    with prof:
        _benchmark_algorithm(algorithm_name, dataset)
    prof.dump_stats(filename="./calc/benchmarks/profiling.log")

    with open("./calc/benchmarks/profiling.log", 'r') as prof_file:
        with open("./calc/benchmarks/profiling_stripped.log", 'w') as stripped_file:
            for line in prof_file:
                line = re.sub(r'^.*\|.*0\.00%\|.*$\n', r'', line)
                stripped_file.write(line)
