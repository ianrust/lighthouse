from typing import Tuple, List

from lib.utils import interpolate_value, generate_ratios


class Color(object):
    def __init__(self, red: int, green: int, blue: int):
        self._validate_color(red)
        self._validate_color(green)
        self._validate_color(blue)

        self.red = red
        self.green = green
        self.blue = blue

    @staticmethod
    def _validate_color(color):
        assert 0 <= color <= 255

    def to_rgb_tuple(self) -> Tuple[int, int, int]:
        return self.red, self.green, self.blue

    def __repr__(self):
        return '<Color red={red} blue={blue} green={green} />'.format(
            red=self.red, blue=self.blue, green=self.green)


def interpolate_colors(color_1: Color, color_2: Color, ratio: float, brightness: float = 1) -> Color:
    """

    :param color_1:
    :param color_2:
    :param ratio: 0 -> color_1, 1 -> color_2
    :param brightness:
    :return:
    """
    color = Color(
        red=int(interpolate_value(color_1.red, color_2.red, ratio) * brightness),
        green=int(interpolate_value(color_1.green, color_2.green, ratio) * brightness),
        blue=int(interpolate_value(color_1.blue, color_2.blue, ratio) * brightness),
    )

    return color


def generate_color_gradient(
        color_1: Color,
        color_2: Color,
        num_steps: int,
        brightness: float
) -> List[Color]:
    ratios = generate_ratios(num_steps)

    color_list = [
        interpolate_colors(color_1, color_2, ratio, brightness)
        for ratio in ratios
    ]

    return color_list
