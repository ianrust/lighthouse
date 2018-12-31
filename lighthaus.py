#!/usr/bin/python3

import itertools
import queue
import threading
import time

from lib.color import Color
from lib.neopixel_writer import create_neopixel_writer

# Set the max scrollspeed
from lib.schedule import get_colors_from_schedule_file

MAX_SCROLL_OFFSET = 600


class LighthausController(object):
    def __init__(
            self,
            writer,
            initial_color_1: Color,
            initial_color_2: Color,
            initial_scroll_speed: float = 0,
            sleep_time: float = 0.01,
            brightness: float = 1.0,
    ):
        self.writer = writer
        self.color_1 = initial_color_1
        self.color_2 = initial_color_2
        self.scroll_speed = initial_scroll_speed
        self.sleep_time = sleep_time
        self.brightness = brightness

        self.is_running = False

    def get_num_offsets(self) -> int:
        """
        A slower scroll_speed -> a smaller offset -> higher number of offsets

        :return:
        """
        return int(MAX_SCROLL_OFFSET * self.scroll_speed)

    def _run(self, q=queue.Queue):
        current_offset = 0

        while True:
            # TODO: figure out how to fade the colors / speed

            num_offsets = self.get_num_offsets()
            offset_delta = 1 / (num_offsets + 1)  # The amount we change the offset each round

            current_offset = (current_offset + offset_delta) % 1

            writer.write_gradient(self.color_1, self.color_2, offset=current_offset,
                                  brightness=self.brightness)

            self._check_queue(q)
            time.sleep(self.sleep_time)

    def _check_queue(self, q: queue.Queue):
        try:
            new_config = q.get(block=False)
            print('new_config', new_config)

            if 'scroll_speed' in new_config:
                self.scroll_speed = new_config['scroll_speed']

            if 'color_1' in new_config:
                self.color_1 = new_config['color_1']

            if 'color_2' in new_config:
                self.color_2 = new_config['color_2']

            if 'brightness' in new_config:
                self.brightness = new_config['brightness']

            q.task_done()
        except queue.Empty:
            pass

    def run(self) -> queue.Queue:
        q = queue.Queue()

        graphics_thread = threading.Thread(target=self._run, args=(q,), daemon=True)
        graphics_thread.start()

        return q


if __name__ == '__main__':
    color1 = Color(red=255, blue=0, green=0)
    color2 = Color(red=0, blue=255, green=0)

    writer = create_neopixel_writer()

    controller = LighthausController(
        writer=writer,
        initial_color_1=color1,
        initial_color_2=color2,
        initial_scroll_speed=0.8,
    )
    q = controller.run()

    scroll_speeds = [0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    colors = [
        Color(red=255, blue=0, green=0),
        Color(red=0, blue=10, green=0),
    ]

    # for scroll_speed in itertools.cycle(scroll_speeds):
    #     print('scroll_speed', scroll_speed)
    #     q.put({
    #         'scroll_speed': scroll_speed,
    #         # 'color_1': color,
    #         # 'color_2': color,
    #     })
    #
    #     time.sleep(4)

    while True:
        (color_1, color_2, brightness, scroll_speed) = get_colors_from_schedule_file()

        q.put({
            'color_1': color_1,
            'color_2': color_2,
            'brightness': brightness,
            'scroll_speed': scroll_speed,
        })

        time.sleep(1)
