from typing import List, Union


def generate_ratios(num_steps: int, include_1: bool = True) -> List[float]:
    if num_steps == 0:
        return [0]

    if include_1:
        return [
            step * 1 / (num_steps - 1)
            for step in range(num_steps)
        ]

    return [
        step * 1 / num_steps
        for step in range(num_steps)
    ]


def rotate_list(l: list, n: int) -> list:
    """
    Rotate a list to the left

    :param l:
    :param n:
    :return:
    """
    assert 0 <= n < len(l)
    return l[n:] + l[:n]


def interpolate_value(
        value_1: float,
        value_2: float,
        ratio: float,
) -> float:
    """

    :param value_1:
    :param value_2:
    :param ratio:  0 -> value_2, 1 -> value_1
    :return:
    """
    new_val = value_1 * ratio + value_2 * (1 - ratio)

    return new_val


def clamp(val: float, min_val: float, max_val: float) -> float:
    assert max_val > min_val
    return max(min(val, max_val), min_val)
