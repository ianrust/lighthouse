#!/usr/bin/python3

import datetime
from flask import Flask
import itertools
import queue
import sys
import threading
import time

from lib.color import Color
from lib.gradient import Gradient, interpolate_gradients
from lib.neopixel_writer import create_neopixel_writer
from lib.schedule import update_from_schedule_async, get_seconds_since_epoch
from lib.server import setup_endpoint
from lib.utils import clamp


class LighthausController(object):
    def __init__(
            self,
            writer,
            initial_color_1: Color,
            initial_color_2: Color,
            initial_scroll_speed: float = 0,
            sleep_time: float = 0.01,
            brightness: float = 1.0,
            fade_in_duration: float = 5.0,
            sustain_user_duration: float = 30.0,
            fade_out_duration: float = 20.0,
            speedup_factor: float = 5000.0,
    ):
        self.writer = writer

        # gradient coming from color schedule file
        self.scheduled_gradient = Gradient(
                seconds=get_seconds_since_epoch(),
                color_1=initial_color_1,
                color_2=initial_color_2,
                scroll_speed=initial_scroll_speed,
                brightness=brightness
            )

        # gradient last set to leds
        self.current_gradient = self.scheduled_gradient

        # gradient sent by user
        self.user_gradient = Gradient(
                seconds=0,
                color_1=initial_color_1,
                color_2=initial_color_2,
                scroll_speed=initial_scroll_speed,
                brightness=brightness
            )

        # gradient set to leds when a new user gradient arrived
        self.transition_gradient = Gradient(
                seconds=0,
                color_1=initial_color_1,
                color_2=initial_color_2,
                scroll_speed=initial_scroll_speed,
                brightness=brightness
            )
        self.sleep_time = sleep_time
        self.fade_in_duration = fade_in_duration
        self.fade_out_duration = fade_out_duration
        self.sustain_user_duration = sustain_user_duration
        self.speedup_factor = speedup_factor
        # float of time it was requested if needed, else None
        self.fast_mode_ref = None

        self.is_running = False

        # function for getting the schedule
        self.schedule_interpolator = None

    def _run(self, in_q: queue.Queue):
        current_offset = 0.0

        while True:

            # evaluate interpolator, apply speedup only if set that way
            if not self.schedule_interpolator is None:
                self.scheduled_gradient = self.schedule_interpolator(self.fast_mode_ref, self.speedup_factor)

            # Fade in/out the user inputs from the flask server
            time_since_input = get_seconds_since_epoch() - self.transition_gradient.seconds

            # default, be on schedule
            gradient_to_write = self.scheduled_gradient

            total_user_input_duration = (
                    self.fade_in_duration + self.sustain_user_duration + self.fade_out_duration)
            sustain_user_input_end = self.fade_in_duration + self.sustain_user_duration

            is_fading_in = time_since_input < self.fade_in_duration
            is_sustaining_user_input = self.fade_in_duration <= time_since_input < sustain_user_input_end
            is_fading_out = sustain_user_input_end <= time_since_input < total_user_input_duration

            if is_fading_in:
                # in fade-in transition between the transition gradient and the selected user gradient
                user_ratio = clamp(time_since_input / self.fade_in_duration, 0, 1)
                gradient_to_write = interpolate_gradients(self.transition_gradient, self.user_gradient,
                                                          user_ratio)
            elif is_sustaining_user_input:
                gradient_to_write = self.user_gradient
            elif is_fading_out:
                # in fade out go between user gradient and the scheduled gradient
                time_into_fade_out = time_since_input - sustain_user_input_end
                scheduled_ratio = clamp(time_into_fade_out / self.fade_out_duration, 0, 1)
                gradient_to_write = interpolate_gradients(self.user_gradient, self.scheduled_gradient,
                                                          scheduled_ratio)

            # Run a counter to scroll the gradient
            current_offset = (current_offset + gradient_to_write.scroll_speed) % 1
            # scroll with current gradient
            writer.write_gradient(gradient_to_write, offset=current_offset)

            # store for passing to transition_gradient when a new color is received
            self.current_gradient = gradient_to_write
            self.current_gradient.seconds = get_seconds_since_epoch()

            self._check_queue(in_q)
            time.sleep(self.sleep_time)

    def _check_queue(self, in_q: queue.Queue):
        try:
            new_config = in_q.get(block=False)

            # silent message parsing
            if 'schedule_interpolator' in new_config:
                self.schedule_interpolator = new_config['schedule_interpolator']
            else:
                # print out other messages coming in
                print('new_config', new_config)
                sys.stdout.flush()

            # logged message parsing
            if 'user_gradient' in new_config:
                self.user_gradient = new_config['user_gradient']
                self.transition_gradient = self.current_gradient
            if 'fast_mode' in new_config:
                if (new_config['fast_mode']):
                    self.fast_mode_ref = datetime.datetime.now()
                else:
                    self.fast_mode_ref = None

            in_q.task_done()
        except queue.Empty:
            pass

    def run(self) -> queue.Queue:
        assert not self.is_running
        self.is_running = True

        in_q = queue.Queue()

        graphics_thread = threading.Thread(target=self._run, kwargs=dict(in_q=in_q), daemon=True)
        graphics_thread.start()

        return in_q


if __name__ == '__main__':
    writer = create_neopixel_writer()

    controller = LighthausController(
        writer=writer,
        initial_color_1=Color(red=255, blue=0, green=0),
        initial_color_2=Color(red=0, blue=255, green=0),
        initial_scroll_speed=0.01,
    )

    controller_in_q = controller.run()
    update_from_schedule_async(controller_in_q)

    app = Flask(__name__)
    setup_endpoint(app, controller_in_q)
