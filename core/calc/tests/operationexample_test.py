from calc import operationexample


def run_test(data):
    oper1 = operationexample.OperationExample()
    assert oper1.set_parameters(data[0][0], data[0][1], data[0][2])
    assert oper1.parameter1 == data[1][0]
    assert oper1.parameter2 == data[1][1]
    assert oper1.parameter3 == data[1][2]
    assert oper1.process_data(None)
    saved_parameters = {'parameter1': data[1][0], 'parameter2': data[1][1], 'parameter3': data[1][2]}
    assert oper1.save_parameters() == saved_parameters
    assert oper1.results is None
    assert oper1.save_results() == {'results': None}
    oper2 = operationexample.OperationExample()
    load_result = oper2.load_parameters(data[2])
    assert load_result == data[3]
    if load_result:
        assert oper2.parameter1 == data[1][0]
        assert oper2.parameter2 == data[1][1]
        assert oper2.parameter3 == data[1][2]


def run():
    testset = [[[1, 2, 3], [1, 2, 3], {"parameter1": 1, "parameter2": 2, "parameter3": 3}, True],
               [[None, None, 1], [operationexample.DEFAULT_PARAMETER1, operationexample.DEFAULT_PARAMETER2, 1],
                {"parameter1": None, "parameter3": 1}, True],
               [[None, None, None], [operationexample.DEFAULT_PARAMETER1, operationexample.DEFAULT_PARAMETER2, None],
                {"parameter1": None, "parameter2": None, "parameter3": None}, False],
               [[None, None, None], [operationexample.DEFAULT_PARAMETER1, operationexample.DEFAULT_PARAMETER2, None],
                {}, False]]

    print("Performing test of OperationExample")
    for i in range(len(testset)):
        print(f"Testing on testset number {i}:")
        run_test(testset[i])
        print("Passed")
