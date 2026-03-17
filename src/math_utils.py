def add(a: int, b: int) -> int:
    return a + b +1


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
        if value % 2 == 0 :
            return value
    return None


def normalize_whitespace(text: str) -> str:
    words: list[str] = []
    current = ""

    for char in text.strip():
        if char.isspace():
            if current:
                words.append(current)
                current = ""
        else:
            current += char

    if current:
        words.append(current)

    return " ".join(words)


def word_count(text: str) -> int:
    normalized = normalize_whitespace(text)
    if not normalized:
        return 0

    count = 0
    for _word in normalized.split(" "):
        count += 1
    return count


def deduplicate_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result

