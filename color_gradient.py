#!/usr/bin/python3
import time
from typing import List, Tuple


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

    # def __repr__(self):
    #     return f'<Color red={self.red} blue={self.blue} green={self.green} />'


def interpolate_colors(color_1: Color, color_2: Color, ratio: float) -> Color:
    """

    :param color_1:
    :param color_2:
    :param ratio: 0 -> color_1, 1 -> color_2
    :return:
    """

    def interpolate_value(value_1, value_2, ratio_):
        return round(value_1 * ratio_ + value_2 * (1 - ratio_))

    color = Color(
        red=interpolate_value(color_1.red, color_2.red, ratio),
        green=interpolate_value(color_1.green, color_2.green, ratio),
        blue=interpolate_value(color_1.blue, color_2.blue, ratio),
    )

    return color


def generate_ratios(num_steps: int, include_1: bool = True) -> List[float]:
    if include_1:
        return [
            step * 1 / (num_steps - 1)
            for step in range(num_steps)
        ]

    return [
        step * 1 / num_steps
        for step in range(num_steps)
    ]


def generate_color_gradient(color_1: Color, color_2: Color, num_steps: int) -> List[Color]:
    ratios = generate_ratios(num_steps)

    color_list = [
        interpolate_colors(color_1, color_2, ratio)
        for ratio in ratios
    ]

    return color_list


def rotate_list(l: list, n: int) -> list:
    """
    Rotate a list to the left

    :param l:
    :param n:
    :return:
    """
    assert 0 <= n < len(l)
    return l[n:] + l[:n]


class NeoPixelWriter(object):
    def __init__(
            self,
            num_pixels: int,
            pixel_pin,
            pixel_order,
            brightness: float = 1.0,
            auto_write: bool = False,
    ):
        import neopixel

        self.num_pixels = num_pixels

        self.pixels = neopixel.NeoPixel(
            pin=pixel_pin,
            n=num_pixels,
            brightness=brightness,
            auto_write=auto_write,
            pixel_order=pixel_order,
        )

    def _write(self, color_list: List[Color]):
        assert len(color_list) == self.num_pixels

        for i, color in enumerate(color_list):
            self.pixels[i] = color.to_rgb_tuple()

        self.pixels.show()

    def write_gradient(self, color_1: Color, color_2: Color, offset: float = 0):
        """
        The pixels are set up like a snake, so the first pixel is next to the last pixel

        Pixel Layout Example
        3 4
        2 5
        1 6
        0 7

        :param color_1:
        :param color_2:
        :param offset:
        :return:
        """
        half_color_list = generate_color_gradient(
            color_1,
            color_2,
            int(self.num_pixels / 2),
        )

        if offset:
            assert 0 <= offset < 1

            offset_pixels = int(offset * (self.num_pixels / 2 - 1))
            half_color_list = rotate_list(half_color_list, offset_pixels)

        color_list = half_color_list + list(reversed(half_color_list))

        self._write(color_list)


def create_neopixel_writer(pixel_pin=None, num_pixels=None, pixel_order=None) -> NeoPixelWriter:
    import board
    import neopixel

    if not pixel_pin:
        # Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
        # NeoPixels must be connected to D10, D12, D18 or D21 to work.
        pixel_pin = board.D18

    if not num_pixels:
        num_pixels = 120

    if not pixel_order:
        # The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
        # For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
        pixel_order = neopixel.GRB

    writer = NeoPixelWriter(num_pixels=num_pixels, pixel_pin=pixel_pin, pixel_order=pixel_order)
    return writer


if __name__ == '__main__':
    color1 = Color(red=255, blue=0, green=0)
    color2 = Color(red=0, blue=255, green=0)

    writer = create_neopixel_writer()

    while True:
        offsets = generate_ratios(600, include_1=False)

        for offset in offsets:
            writer.write_gradient(color1, color2, offset=offset)
            time.sleep(0.01)
