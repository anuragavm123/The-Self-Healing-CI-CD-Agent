from src.math_utils import (
    add,
    deduplicate_preserve_order,
    factorial,
    find_first_even,
    normalize_whitespace,
    sum_upto,
    word_count,
)


class TestAddDemo:
    def test_add_zero_values(self) -> None:
        assert add(0, 0) == 0

    def test_add_is_commutative(self) -> None:
        assert add(7, 3) == add(3, 7)

    def test_add_large_numbers(self) -> None:
        assert add(1_000_000, 2_000_000) == 3_000_000

    def test_add_mixed_sign_values(self) -> None:
        assert add(-10, 3) == -7

    def test_add_two_negative_values(self) -> None:
        assert add(-4, -6) == -10


class TestMathUtilityDemo:
    def test_sum_upto_zero(self) -> None:
        assert sum_upto(0) == 0

    def test_sum_upto_ten(self) -> None:
        assert sum_upto(10) == 55

    def test_factorial_zero(self) -> None:
        assert factorial(0) == 1

    def test_find_first_even_in_mixed_list(self) -> None:
        assert find_first_even([9, 7, 4, 3]) == 4


class TestGeneralUtilityDemo:
    def test_normalize_whitespace_empty_input(self) -> None:
        assert normalize_whitespace("   \n\t  ") == ""

    def test_word_count_empty_input(self) -> None:
        assert word_count("   ") == 0

    def test_deduplicate_preserve_order_with_unique_values(self) -> None:
        assert deduplicate_preserve_order(["x", "y", "z"]) == ["x", "y", "z"]
