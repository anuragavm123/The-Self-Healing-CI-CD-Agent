from src.math_utils import add, factorial, find_first_even, sum_upto


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
