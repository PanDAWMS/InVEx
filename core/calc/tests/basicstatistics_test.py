from calc import basicstatistics
import pandas as pd


def isclose(a, b, rel_tol=1e-04, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def run_test(test):
    calc = basicstatistics.BasicStatistics()
    result = calc.process_data(test[0])
    print("Testing calculations")
    for i in range(len(result)):
        for j in range(len(result[i])):
            if not isclose(result[i][j], test[1][i][j]):
                assert False
    print("Testing saving results")
    saved = calc.save_results()
    calc = basicstatistics.BasicStatistics()
    assert calc.load_results(saved)
    result = calc.results
    for i in range(len(result)):
        for j in range(len(result[i])):
            if not isclose(result[i][j], test[1][i][j]):
                assert False

    return True


def run():
    testset = [[pd.DataFrame([[1, 2, 3, 4], [4, 3, 2, 1], [-1, -2, -3, -4], [0, 0, 0, 0], [0, 0, 0, 0]]),
                [[-1, -2, -3, -4], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [1.0, 2.0, 2.0, 1.0], [4, 3, 3, 4],
                 [4, 3, 2, 1], [1.92354, 1.94936, 2.30217, 2.86356]]],
               [pd.DataFrame([[1, 2, 3, 4], [4, 3, 2, 1]]),
                [[1, 2, 2, 1], [1.75, 2.25, 2.25, 1.75], [2.5, 2.5, 2.5, 2.5], [3.25, 2.75, 2.75, 3.25], [4, 3, 3, 4],
                 [5, 5, 5, 5], [2.12132, 0.70711, 0.70711, 2.12132]]],
               [pd.DataFrame(
                   [[7, 1, 3, 3], [6, 4, 8, 9], [1, 1, 0, 8], [6, 2, 0, 4], [2, 4, 2, 2], [7, 9, 2, 3], [9, 7, 7, 2],
                    [5, 9, 8, 10]]),
                   [[1, 1, 0, 2], [4.25, 1.75, 1.5, 2.75], [6.0, 4.0, 2.5, 3.5], [7.0, 7.5, 7.25, 8.25], [9, 9, 8, 10],
                    [43, 37, 30, 41], [2.66927, 3.33542, 3.41216, 3.31393]]]]
    print("Performing test of BasicStatistics")
    for i in range(len(testset)):
        print(f"Testing on testset number {i}:")
        assert run_test(testset[i])
        print("Passed")
