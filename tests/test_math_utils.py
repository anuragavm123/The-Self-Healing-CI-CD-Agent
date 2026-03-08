from src.math_utils import add


def test_add_two_positive_numbers() -> None:
    assert add(2, 2) == 4


def test_add_with_negative_number() -> None:
    assert add(5, -2) == 3
