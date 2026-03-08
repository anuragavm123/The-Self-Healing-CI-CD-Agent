from src.math_utils import (
    add,
    deduplicate_preserve_order,
    factorial,
    find_first_even,
    normalize_whitespace,
    sum_upto,
    word_count,
)


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


def test_normalize_whitespace_collapses_spaces() -> None:
    assert normalize_whitespace("  hello   world\nthis\t is   demo  ") == "hello world this is demo"


def test_word_count_handles_irregular_spacing() -> None:
    assert word_count(" one   two\nthree\tfour ") == 4


def test_deduplicate_preserve_order_keeps_first_seen() -> None:
    assert deduplicate_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
