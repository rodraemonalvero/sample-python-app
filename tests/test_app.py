from app import calculate_average, divide_numbers


def test_divide_numbers():
    assert divide_numbers(10, 2) == 5


def test_calculate_average():
    assert calculate_average([2, 4, 6]) == 4