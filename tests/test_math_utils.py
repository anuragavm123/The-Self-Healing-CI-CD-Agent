from src.math_utils import add, factorial, find_first_even, sum_upto


def test_add_two_positive_numbers() -> None:
    assert add(2, 2) == 4


def test_add_with_negative_number() -> None:
    assert add(5, -2) == 3


def test_sum_upto_includes_limit() -> None:
    assert sum_upto(5) == 15


def test_factorial_of_five() -> None:
    assert factorial(5) == 120


def test_find_first_even_returns_none_when_not_found() -> None:
    assert find_first_even([1, 3, 5]) is None
