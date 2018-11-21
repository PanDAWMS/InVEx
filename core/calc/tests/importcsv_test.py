from calc import importcsv


class ImportCSVFileTest:
    _test_data = [['calc/tests/dataset/testdata_noid_nonames.csv', False, False],
                  ['calc/tests/dataset/testdata_noid_names.csv', True, False],
                  ['calc/tests/dataset/testdata_id_nonames.csv', False, True],
                  ['calc/tests/dataset/testdata_id_names.csv', True, True]]
    _test_data_basic_results = [[None, [0, 1, 2, 3, 4]],
                                [None, ['X', 'Y', 'Z', 'T', 'G']],
                                [0, [1, 2, 3, 4, 5]],
                                ['Names', ['X', 'Y', 'Z', 'T', 'G']]]
    _test_data_object_results = [[[0, 0, [1.2, 1.3, 1.4, 1.5, 1.6]],
                                  [2, 2, [-2.1, -5, 2, 12, 1]],
                                  [1, 1, [4.5, 5, 2.3, 1, 2.77]]],
                                 [[0, 0, [1.2, 1.3, 1.4, 1.5, 1.6]],
                                  [2, 2, [-2.1, -5, 2, 12, 1]],
                                  [1, 1, [4.5, 5, 2.3, 1, 2.77]]],
                                 [['first', 'first', [1.2, 1.3, 1.4, 1.5, 1.6]],
                                  ['third', 'third', [-2.1, -5, 2, 12, 1]],
                                  [1, 'second', [4.5, 5, 2.3, 1, 2.77]]],
                                 [['first', 'first', [1.2, 1.3, 1.4, 1.5, 1.6]],
                                  ['third', 'third', [-2.1, -5, 2, 12, 1]],
                                  [1, 'second', [4.5, 5, 2.3, 1, 2.77]]]]

    def test_no_file(self):
        assert importcsv.import_csv_file('') is None

    def dataset_columns_test(self, test_dataset, results):
        assert test_dataset.index.name == results[0]
        for i in range(len(results[1])):
            assert test_dataset.columns[i] == results[1][i]

    def object_test(self, test_dataset, tests, colnames):
        row = test_dataset.loc[tests[0][0], :]
        assert row.name == tests[0][1]
        for i in range(len(tests[0][2])):
            assert row.iat[i] == tests[0][2][i]
            assert row.at[colnames[i]] == tests[0][2][i]
        row = test_dataset.loc[tests[1][0], :]
        assert row.name == tests[1][1]
        for i in range(len(tests[1][2])):
            assert row.iat[i] == tests[1][2][i]
            assert row.at[colnames[i]] == tests[1][2][i]
        row = test_dataset.iloc[tests[2][0], :]
        assert row.name == tests[2][1]
        for i in range(len(tests[2][2])):
            assert row.iat[i] == tests[2][2][i]
            assert row.at[colnames[i]] == tests[2][2][i]

    def test_file(self, testnum):
        dataset = importcsv.import_csv_file(self._test_data[testnum][0],
                                            column_names=self._test_data[testnum][1],
                                            index=self._test_data[testnum][2])
        print("Import done")
        self.dataset_columns_test(dataset, self._test_data_basic_results[testnum])
        print("Columns test done")
        self.object_test(dataset, self._test_data_object_results[testnum],
                         self._test_data_basic_results[testnum][1])
        print("Object test done")


def run():
    print("Testing import csv:")
    import_csv_test = ImportCSVFileTest()
    print("Testing no file given:")
    import_csv_test.test_no_file()
    print("Passed")
    for i in range(len(import_csv_test._test_data)):
        print(f"Testing testfile number {i}:")
        import_csv_test.test_file(i)
        print("Passed")
