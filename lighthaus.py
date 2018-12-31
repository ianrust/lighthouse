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

    def _run(self, q=queue.Queue):
        current_offset = 0

        while True:
            # TODO: figure out how to fade the colors / speed

            current_offset = (current_offset + self.scroll_speed) % 1

            writer.write_gradient(self.color_1, self.color_2, offset=current_offset,
                                  brightness=self.brightness)

            self._check_queue(q)
            time.sleep(self.sleep_time)

    def _check_queue(self, q: queue.Queue):
        try:
            new_config = q.get(block=False)
            print('new_config', new_config)

            if 'scheduled_gradient' in new_config:
                self.scroll_speed = new_config['scheduled_gradient']

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
        scheduled_gradient = get_colors_from_schedule_file()

        q.put({
            'scheduled_gradient': scheduled_gradient 
        })

        time.sleep(1)
