from typing import List, Union


# maps line of 0-1 to a triangle from 0 to 1 back to 0 (in the same distance)
def line_to_triangle(ratio: float) -> float:
    # equation for like from 0 to 1 in half the distance (0 to 0.5)
    if ratio <= 0.5:
        return ratio * 2

    assert ratio <= 1.0
    # equation from 1 to 0 starting at 0.5 and going to 1
    return (1 - ratio) * 2


# takes a line from offset to 1+offset and moves it inside
# the window from 0-1
def shift(ratio: float, offset: float) -> float:
    shifted_ratio = ratio + offset
    if shifted_ratio < 0:
        return shifted_ratio + 1.0
    elif shifted_ratio > 1.0:
        return shifted_ratio - 1.0
    else:
        return shifted_ratio


def generate_ratios(num_steps: int, offset: float) -> List[float]:
    if num_steps == 0:
        return [0]

    return [
        line_to_triangle(shift(step / num_steps, offset))
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
