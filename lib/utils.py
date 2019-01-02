from typing import List, Union


# maps line of 0-1 to a triangle from 0 to 1 back to 0
def triangle(ratio: float) -> float:
    doubled_ratio = 2.0 * ratio
    if doubled_ratio <= 1.0:
        return doubled_ratio
    else:
        return -doubled_ratio + 2.0


def generate_ratios(num_steps: int) -> List[float]:
    if num_steps == 0:
        return [0]

    return [
        triangle(step * 1 / (num_steps - 1))
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
    :param ratio:  0 -> value_1, 1 -> value_2
    :return:
    """
    new_val = value_2 * ratio + value_1 * (1 - ratio)

    return new_val


def clamp(val: float, min_val: float, max_val: float) -> float:
    assert max_val > min_val
    return max(min(val, max_val), min_val)
