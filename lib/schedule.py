import csv
import datetime
from collections import namedtuple
from typing import Tuple, List

import maya
import requests

from lib.color import Color, interpolate_colors
from lib.utils import interpolate_value


def get_seconds_into_day():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    seconds_into_day = (now - midnight).total_seconds()
    return seconds_into_day


SUNRISE_SUNSET_QUERY_URL = (
    'https://api.sunrise-sunset.org/json?lat=37.7749&lng=-122.4194&date={date_string}&formatted=0'
)


def get_sunrise_and_sunset_seconds() -> Tuple[int, int]:
    query_url = SUNRISE_SUNSET_QUERY_URL.format(date_string=datetime.date.today().isoformat())
    json_resp = requests.get(query_url).json()

    midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    sunrise_dt = maya.parse(json_resp['results']['sunrise']).datetime(to_timezone='US/Pacific', naive=True)
    sunrise_secs = (sunrise_dt - midnight).total_seconds()

    sunset_dt = maya.parse(json_resp['results']['sunset']).datetime(to_timezone='US/Pacific', naive=True)
    sunset_secs = (sunset_dt - midnight).total_seconds()

    return int(sunrise_secs), int(sunset_secs)


TimePointInfo = namedtuple('TimePointInfo', ['seconds', 'color_1', 'color_2', 'brightness', 'scroll_speed'])


def get_time_point_infos_from_schedule_file(schedule_file_name: str) -> List[TimePointInfo]:
    sunrise_secs, sunset_secs = get_sunrise_and_sunset_seconds()

    time_point_infos = []

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

            time_point_infos.append(
                TimePointInfo(
                    seconds=seconds,
                    color_1=color_1,
                    color_2=color_2,
                    brightness=float(line['brightness']),
                    scroll_speed=float(line['scroll_speed']),
                )
            )
        return sorted(time_point_infos, key=lambda time_point: time_point.seconds)


SECONDS_IN_DAY = 24 * 60 * 60


def get_colors_from_schedule_file(
        schedule_file_name: str = 'color_schedule.csv'
) -> Tuple[Color, Color, float, float]:
    """
    Get scheduled colors. The schedule file stores a series of points in the day. Each point of the day
    has two colors.

    We look at the current time of day, find the time points on either side, and interpolate between
    those two time points.

    :param schedule_file_name:
    :return: (color_1, color_2, brightness, speed) - scheduled colors
    """
    time_point_infos = get_time_point_infos_from_schedule_file(schedule_file_name)

    # Get time points before and after the current time
    min_seconds = time_point_infos[0].seconds
    max_seconds = time_point_infos[-1].seconds

    seconds_into_day = get_seconds_into_day()

    if seconds_into_day <= min_seconds or seconds_into_day >= max_seconds:
        time_point_1 = time_point_infos[0]
        time_point_2 = time_point_infos[-1]

        time_point_2_to_midnight = SECONDS_IN_DAY - time_point_2.seconds

        # (seconds from midnight to time_point_1) + (seconds from time_point_2 to end of day)
        delta_between_time_points = time_point_1.seconds + time_point_2_to_midnight

        if seconds_into_day <= min_seconds:
            ratio = (time_point_2_to_midnight + seconds_into_day) / delta_between_time_points
        else:
            assert seconds_into_day >= max_seconds
            ratio = (seconds_into_day - time_point_2.seconds) / delta_between_time_points
    else:
        earlier_time_points = [
            tpi for tpi in time_point_infos
            if tpi.seconds <= seconds_into_day
        ]
        later_time_points = [
            tpi for tpi in time_point_infos
            if tpi.seconds >= seconds_into_day
        ]

        time_point_1 = earlier_time_points[-1]
        time_point_2 = later_time_points[0]

        if time_point_1 == time_point_2:
            ratio = 0
        else:
            delta_between_time_points = time_point_2.seconds - time_point_1.seconds
            ratio = (seconds_into_day - time_point_1.seconds) / delta_between_time_points

    color_1 = interpolate_colors(time_point_1.color_1, time_point_2.color_1, ratio)
    color_2 = interpolate_colors(time_point_1.color_2, time_point_2.color_2, ratio)

    brightness = interpolate_value(time_point_1.brightness, time_point_2.brightness, ratio,
                                   should_round=False)
    brightness = brightness / 100

    scroll_speed = interpolate_value(time_point_1.scroll_speed, time_point_2.scroll_speed, ratio)

    return color_1, color_2, brightness, scroll_speed

