from . import benchmark

# filename = "../../datasets/job_records_80k_13305102.csv"
filename = "./datasets/job_records_13332803.csv"
# benchmark.run_benchmarks(n_runs=1, filename=filename)
benchmark.dendrogram(filename)
# benchmark.profile_algorithm("KPrototypesClustering", filename=filename)
