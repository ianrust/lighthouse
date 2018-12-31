#!/usr/bin/python3

from flask import Flask
import itertools
import queue
import threading
import time

from lib.color import Color
from lib.gradient import Gradient, interpolate_gradients
from lib.neopixel_writer import create_neopixel_writer
from lib.schedule import update_from_schedule_async, get_seconds_now
from lib.server import setup_endpoint


class LighthausController(object):
    def __init__(
            self,
            writer,
            initial_color_1: Color,
            initial_color_2: Color,
            initial_scroll_speed: float = 0,
            sleep_time: float = 0.01,
            brightness: float = 1.0,
            fade_in_time: float = 5.0,
            fade_out_time: float = 20.0,
    ):
        self.writer = writer
        self.scheduled_gradient = Gradient(
                seconds=get_seconds_now(),
                color_1=initial_color_1,
                color_2=initial_color_2,
                scroll_speed=initial_scroll_speed,
                brightness=brightness
            )
        self.current_gradient = self.scheduled_gradient
        self.user_gradient = Gradient(
                seconds=0,
                color_1=initial_color_1,
                color_2=initial_color_2,
                scroll_speed=initial_scroll_speed,
                brightness=brightness
            )
        self.transition_gradient = Gradient(
                seconds=0,
                color_1=initial_color_1,
                color_2=initial_color_2,
                scroll_speed=initial_scroll_speed,
                brightness=brightness
            )
        self.sleep_time = sleep_time
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time

        self.is_running = False

    def _run(self, in_q: queue.Queue):
        current_offset = 0

        while True:
            # Run a counter to scroll the gradient
            current_offset = (current_offset + self.scroll_speed) % 1

            # Fade in/out the user inputs from the flask server
            time_since_input = get_seconds_now() - self.transition_gradient.seconds

            # default, be on schedule
            faded_gradient = self.scheduled_gradient
            user_ratio = 0
            if time_since_input < self.fade_in_time:
                user_ratio = time_since_input / self.fade_in_time
                user_ratio = max(user_ratio, 0.0)
                user_ratio = min(user_ratio, 1.0)
                faded_gradient = interpolate_gradients(self.transition_gradient, self.user_gradient, user_ratio)
            elif time_since_input > self.fade_in_time and time_since_input < (self.fade_in_time + self.fade_out_time):
                user_ratio = 1.0 - ((time_since_input - self.fade_in_time) / self.fade_out_time)
                user_ratio = max(user_ratio, 0.0)
                user_ratio = min(user_ratio, 1.0)
                faded_gradient = interpolate_gradients(self.transition_gradient, self.user_gradient, user_ratio)

            writer.write_gradient(faded_gradient, offset=current_offset)

            # store for passing to transition_gradient when a new color is received
            self.current_gradient = faded_gradient
            self.current_gradient.seconds = get_seconds_now()

            self._check_queue(in_q)
            time.sleep(self.sleep_time)

    def _check_queue(self, in_q: queue.Queue):
        try:
            new_config = in_q.get(block=False)
            print('new_config', new_config)

            if 'scheduled_gradient' in new_config:
                self.scheduled_gradient = new_config['scheduled_gradient']
            if 'user_gradient' in new_config:
                self.user_gradient = new_config['user_gradient']
                self.transition_gradient = self.current_gradient

            in_q.task_done()
        except queue.Empty:
            pass

    def run(self) -> queue.Queue:
        in_q = queue.Queue()

        graphics_thread = threading.Thread(target=self._run, args=(in_q,), daemon=True)
        graphics_thread.start()

        return in_q


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
    controller_in_q = controller.run()
    update_from_schedule_async(controller_in_q)

    app = Flask(__name__)
    setup_endpoint(app, controller_in_q)

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
