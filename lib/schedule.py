import csv
import datetime
from collections import namedtuple
import queue
from typing import Tuple, List
import threading
import time

import maya
import requests

from lib.gradient import Gradient, interpolate_gradients
from lib.color import Color

ref = datetime.datetime.now()

def get_seconds_into_day(warp_reference = None, speed = 1.0):
    now = datetime.datetime.now()
    if not warp_reference is None:
        warp_diff = now - warp_reference
        now += warp_diff * speed
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    seconds_into_day = (now - midnight).total_seconds()
    return seconds_into_day


def get_seconds_since_epoch():
    now = datetime.datetime.now()
    epoch = datetime.datetime.utcfromtimestamp(0)

    seconds_now = (now - epoch).total_seconds()
    return seconds_now


SUNRISE_SUNSET_QUERY_URL = (
    'https://api.sunrise-sunset.org/json?lat=37.7749&lng=-122.4194&date={date_string}&formatted=0'
)


def get_sunrise_and_sunset_seconds() -> Tuple[int, int]:
    query_url = SUNRISE_SUNSET_QUERY_URL.format(date_string=datetime.date.today().isoformat())
    json_resp = requests.get(query_url).json()

    midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    sunrise_dt = maya.parse(json_resp['results']['sunrise']).datetime(to_timezone='US/Pacific', naive=True)
    sunrise_secs = (sunrise_dt - midnight).total_seconds()
    print("sunrise secs", sunrise_secs)

    sunset_dt = maya.parse(json_resp['results']['sunset']).datetime(to_timezone='US/Pacific', naive=True)
    sunset_secs = (sunset_dt - midnight).total_seconds()
    print("sunrise secs", sunrise_secs)

    return int(sunrise_secs), int(sunset_secs)


def get_gradients_from_schedule_file(schedule_file_name: str) -> List[Gradient]:
    sunrise_secs, sunset_secs = get_sunrise_and_sunset_seconds()

    gradients = []

    with open(schedule_file_name) as schedule_file:
        reader = csv.DictReader(schedule_file)

        for line in reader:
            time_string = line['timeslot']

            if time_string == 'SR':
                seconds = sunrise_secs
            elif time_string == 'SS':
                seconds = sunset_secs
            else:
                [hour, minute] = time_string.split(':')
                seconds = int(hour) * 3600 + int(minute) * 60

            color_1 = Color(
                red=int(line['red_1']),
                green=int(line['green_1']),
                blue=int(line['blue_1']),
            )

            color_2 = Color(
                red=int(line['red_2']),
                green=int(line['green_2']),
                blue=int(line['blue_2']),
            )

            gradients.append(
                Gradient(
                    seconds=seconds,
                    color_1=color_1,
                    color_2=color_2,
                    brightness=float(line['brightness']) / 100.0,
                    scroll_speed=float(line['scroll_speed']),
                )
            )
        return sorted(gradients, key=lambda gradient: gradient.seconds)


SECONDS_IN_DAY = 24 * 60 * 60


# Returns a functions that will quickly interpolate based on "now"
def get_scheduled_gradient_interpolator(
        schedule_file_name: str = 'color_schedule.csv'
) -> Gradient:
    """
    Get scheduled colors. The schedule file stores a series of points in the day. Each point of the day
    has two colors.

    We look at the current time of day, find the time points on either side, and interpolate between
    those two time points.

    This is the only part of the code where the time of day is in the seconds slot of Gradient. When
    this returns it has seconds as now since epoch, as with all other gradients

    :param schedule_file_name:
    :return: (color_1, color_2, brightness, speed) - scheduled colors
    """
    gradients = get_gradients_from_schedule_file(schedule_file_name)

    def schedule_interpolator():
        # Get time points before and after the current time
        min_seconds = gradient_infos[0].seconds
        max_seconds = gradient_infos[-1].seconds

        if seconds_into_day <= min_seconds or seconds_into_day >= max_seconds:
            gradient_1 = gradient_infos[-1]
            gradient_2 = gradient_infos[0]

            gradient_1_to_midnight = SECONDS_IN_DAY - gradient_1.seconds

            # (seconds from midnight to gradient_1) + (seconds from gradient_2 to end of day)
            delta_between_gradients = gradient_2.seconds + gradient_1_to_midnight

            if seconds_into_day <= min_seconds:
                ratio = (gradient_1_to_midnight + seconds_into_day) / delta_between_gradients
            else:
                assert seconds_into_day >= max_seconds
                ratio = (seconds_into_day - gradient_1.seconds) / delta_between_gradients
        else:
            earlier_gradients = [
                g for g in gradient_infos
                if tpi.seconds <= seconds_into_day
            ]
            later_gradients = [
                g for g in gradient_infos
                if tpi.seconds >= seconds_into_day
            ]

            gradient_1 = earlier_gradients[-1]
            gradient_2 = later_gradients[0]

            if gradient_1 == gradient_2:
                ratio = 0
            else:
                delta_between_gradients = gradient_2.seconds - gradient_1.seconds
                ratio = (seconds_into_day - gradient_1.seconds) / delta_between_gradients

        scheduled_gradient = interpolate_gradients(gradient_1, gradient_2, ratio)
        scheduled_gradient.seconds = get_seconds_now()

        return scheduled_gradient

    return schedule_interpolator


def update_from_schedule_continuously(out_q: queue.Queue):
    while True:
        schedule_interpolator = get_schedule_gradient_interpolator()

        out_q.put({
            'schedule_interpolator': schedule_interpolator 
        })

        time.sleep(0.01)


def update_from_schedule_async(out_q: queue.Queue):
    thread = threading.Thread(target=update_from_schedule_continuously, kwargs=dict(out_q=out_q), daemon=True)
    thread.start()

