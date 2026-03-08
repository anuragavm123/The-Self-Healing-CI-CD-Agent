def add(a: int, b: int) -> int:
    return a + b


def sum_upto(limit: int) -> int:
    if limit < 0:
        raise ValueError("limit must be non-negative")

    total = 0
    for value in range(limit + 1):
        total += value
    return total


def factorial(number: int) -> int:
    if number < 0:
        raise ValueError("number must be non-negative")

    result = 1
    for value in range(2, number + 1):
        result *= value
    return result


def find_first_even(values: list[int]) -> int | None:
    for value in values:
        if value % 2 == 0:
            return value
    return None

