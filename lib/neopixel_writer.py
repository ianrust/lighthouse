from typing import List

from lib.color import generate_color_gradient, Color
from lib.gradient import Gradient
from lib.utils import rotate_list


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

    def write_gradient(self, gradient: Gradient, offset: float):
        """
        The pixels are set up like a snake, so the first pixel is next to the last pixel

        Pixel Layout Example
        3 4
        2 5
        1 6
        0 7

        :param gradient:
        :return:
        """
        half_color_list = generate_color_gradient(
            gradient.color_1,
            gradient.color_2,
            int(self.num_pixels / 2),
            brightness=gradient.brightness,
            offset=offset,
        )

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
