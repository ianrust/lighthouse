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
        should_round: bool = False
) -> Union[float, int]:
    new_val = value_1 * ratio + value_2 * (1 - ratio)

    if should_round:
        return round(new_val)

    return new_val
