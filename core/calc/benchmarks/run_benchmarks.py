from . import benchmark
import cProfile

cProfile.run('benchmark.run_benchmarks()')