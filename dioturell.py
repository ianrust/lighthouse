#!/usr/bin/python3

import requests
import datetime
import struct
from dateutil import parser
from time import sleep
from flask import Flask, request, jsonify
import threading
import time
# import board
# import neopixel
import sys

# color_specfile = '/home/pi/Lighthouse/colorspec.txt'
color_specfile = 'colorspec.txt'

sun_query = 'https://api.sunrise-sunset.org/json?lat=37.7749&lng=-122.4194&date=today&formatted=0'

num_pixels = 120
# pixels = neopixel.NeoPixel(board.D18, num_pixels, brightness=1.0, auto_write=False,
#                            pixel_order=neopixel.GRB)
pixels = [0 for _ in range(num_pixels)]

app = Flask(__name__)

colorspec = []  # tuple of time of day (in military time), colors (2 rgb triples), scrollinterval

user_gradient = [[0, 0, 0], [0, 0, 0], 1, None]  # 2 rgb triples and scrollinterval and brightness
user_timer_start = datetime.datetime.min
color_mutex = threading.Lock()

FADE_IN_SECS = 5.0
FADE_OUT_SECS = 20.0

NORMAL_SPEED = 10000.0

gradient1 = None
gradient2 = None

current_color1 = None
current_color2 = None
current_speed = None
transition_color1 = None
transition_color2 = None
transition_speed = None


# endpoint for accepting color
@app.route('/', methods=['POST'])
def updateUserGradient():
    global user_timer_start, user_gradient, current_color1, current_color2, current_speed, \
        transition_color1, transition_color2, transition_speed
    color_mutex.acquire()
    try:
        user_gradient[0] = [request.json['color'][0]['r'],
                            request.json['color'][0]['g'],
                            request.json['color'][0]['b']]
        user_gradient[1] = [request.json['color'][1]['r'],
                            request.json['color'][1]['g'],
                            request.json['color'][1]['b']]
        user_gradient[2] = request.json['scrollspeed']

        try:
            user_gradient[3] = request.json['brightness']
        except:
            user_gradient[3] = None

        user_timer_start = datetime.datetime.now()

        transition_color1 = current_color1
        transition_color2 = current_color2
        transition_speed = current_speed

        print('Received new gradient: {}'.format(user_gradient))
        sys.stdout.flush()
        color_mutex.release()

        return jsonify({'success': True}), 201
    except:
        color_mutex.release()
        print('Received bad request: {}'.format(request.json))
        sys.stdout.flush()
        return jsonify({'success': False}), 400


def interpolateColors(color1, color2, ratio):
    color = (int(color2[0] * ratio + color1[0] * (1 - ratio)),
             int(color2[1] * ratio + color1[1] * (1 - ratio)),
             int(color2[2] * ratio + color1[2] * (1 - ratio)))
    return color


def updateGradientSchedule():
    global gradient1, gradient2

    sun_resp = requests.get(sun_query).json()

    now = datetime.datetime.now()
    sunrise_utc = parser.parse(sun_resp['results']['sunrise'])
    sunrise_secs = (sunrise_utc - sunrise_utc.replace(hour=8, minute=0, second=0, microsecond=0)).total_seconds()
    sunset_utc = parser.parse(sun_resp['results']['sunset'])
    sunset_secs = (sunset_utc + datetime.timedelta(hours=24) -
                   sunset_utc.replace(hour=8, minute=0, second=0, microsecond=0)).total_seconds()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Colorspec headers:
    with open(color_specfile, 'r') as c:
        for line in c:
            cols = line.split(',')
            timeslot = cols[0]
            second = 0
            if timeslot == 'SR':
                second = int(sunrise_secs)
            elif timeslot == 'SS':
                second = int(sunset_secs)
            else:
                hour = int(timeslot.split(':')[0])
                minute = int(timeslot.split(':')[1])
                second = hour * 3600 + minute * 60

            colorspec.append((second,
                              (int(cols[1]), int(cols[2]), int(cols[3])),
                              (int(cols[4]), int(cols[5]), int(cols[6])),
                              int(cols[7]),
                              int(cols[8])
                              ))

    seconds_in_day = (now - midnight).total_seconds()
    gradient1 = colorspec[-1]
    gradient2 = colorspec[0]
    last_gradient = colorspec[0]
    for gradient in colorspec:
        if seconds_in_day > last_gradient[0] and seconds_in_day < gradient[0]:
            gradient1 = last_gradient
            gradient2 = gradient
        last_gradient = gradient


def updateColor(offset):
    global user_timer_start, user_gradient, gradient1, gradient2, pixels, current_color1, current_color2, \
        current_speed, transition_color1, transition_color2, transition_speed

    # don't run until schedule is updated
    if gradient1 is None or gradient2 is None:
        pass

    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_in_day = (now - midnight).total_seconds()

    time2 = gradient2[0]
    if gradient1[0] > gradient2[0]:
        time2 += 86400
    if gradient1[0] > seconds_in_day:
        seconds_in_day += 86400

    # interpolate
    ratio = float(seconds_in_day - gradient1[0]) / float(time2 - gradient1[0])

    scheduled_color1 = interpolateColors(gradient1[1], gradient2[1], ratio)
    scheduled_color2 = interpolateColors(gradient1[2], gradient2[2], ratio)
    scheduled_brightness = gradient2[4] * ratio + gradient1[4] * (1 - ratio)
    scheduled_speed = (gradient2[3] * ratio + gradient1[3] * (1 - ratio)) / NORMAL_SPEED

    # interpolate colors from user input
    color_mutex.acquire()
    user_secs = (now - user_timer_start).total_seconds()
    user_ratio = user_secs / FADE_IN_SECS
    if user_secs > (FADE_IN_SECS + FADE_OUT_SECS):
        current_color1 = scheduled_color1
        current_color2 = scheduled_color2
        current_speed = scheduled_speed
    elif user_ratio > 1.0:
        user_ratio = 1.0 - ((user_secs - FADE_IN_SECS) / FADE_OUT_SECS)
        user_ratio = max(user_ratio, 0.0)
        user_ratio = min(user_ratio, 1.0)
        current_color1 = interpolateColors(scheduled_color1, user_gradient[0], user_ratio)
        current_color2 = interpolateColors(scheduled_color2, user_gradient[1], user_ratio)
        current_speed = user_gradient[2] / NORMAL_SPEED * user_ratio + scheduled_speed * (1 - user_ratio)
    else:
        user_ratio = max(user_ratio, 0.0)
        user_ratio = min(user_ratio, 1.0)
        current_color1 = interpolateColors(transition_color1, user_gradient[0], user_ratio)
        current_color2 = interpolateColors(transition_color2, user_gradient[1], user_ratio)
        # current_speed = user_gradient[2] / normal_speed * user_ratio + transition_speed * (1-user_ratio)

    color_mutex.release()

    faded_color1 = [int(float(cc) * scheduled_brightness / 100.0) for cc in current_color1]
    faded_color2 = [int(float(cc) * scheduled_brightness / 100.0) for cc in current_color2]

    # set the colors
    for i in range(int(num_pixels / 2)):
        left_index = i
        right_index = int(i + (num_pixels / 2 - i) * 2 - 1)
        gradient_ratio = 2.0 * float((i + offset) % int(num_pixels / 2)) / float(num_pixels / 2)

        if (gradient_ratio > 1.0):
            gradient_ratio = -gradient_ratio + 2.0
        this_color = interpolateColors(faded_color1, faded_color2, gradient_ratio)
        try:
            pixels[left_index] = this_color
            pixels[right_index] = this_color
        except BaseException as e:
            print('{0} when setting color {1} on pixel {2}"'.format(e, this_color, i))
            print('Interpolation data:')
            now = datetime.datetime.now()
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_in_day = (now - midnight).total_seconds()
            print('seconds in day: {}'.format(seconds_in_day))
            print('Gradient1: {}'.format(gradient1))
            print('Gradient2: {}'.format(gradient2))
            print('Scheduled Color1: {}'.format(scheduled_color1))
            print('Scheduled Color2: {}'.format(scheduled_color2))
            print('Scheduler ratio: {}'.format(ratio))
            print('Transition Color1: {}'.format(transition_color1))
            print('Transition Color2: {}'.format(transition_color2))
            print('User Color1: {}'.format(user_gradient[0]))
            print('User Color2: {}'.format(user_gradient[1]))
            print('User ratio: {}'.format(user_ratio))
            print('Current Final Color1: {}'.format(current_color1))
            print('Current Final Color2: {}'.format(current_color2))
            print('Current Final Color2: {}'.format(current_color2))
            print('Gradient Ratio: {}'.format(gradient_ratio))
            print('Scheduled brightness: {}'.format(scheduled_brightness))
            sys.stdout.flush()

    # TODO: update this to show the neopixels on computer / board
    # pixels.show()
    # print(pixels)
    time.sleep(0.01)


def colorUpdateLoop():
    global current_speed
    offset = 0
    while 1:
        updateColor(offset)
        offset += current_speed
        if offset >= int(num_pixels / 2):
            offset = 0


def gradientUpdateLoop():
    while 1:
        try:
            updateGradientSchedule()
        except BaseException as e:
            print('{!r}; restarting color scheduling thread'.format(e))
            sys.stdout.flush()
        time.sleep(1)


def startColorRunner():
    fastThread = threading.Thread(target=colorUpdateLoop)
    fastThread.daemon = True
    slowThread = threading.Thread(target=gradientUpdateLoop)
    slowThread.daemon = True
    fastThread.start()
    slowThread.start()


if __name__ == "__main__":
    updateGradientSchedule()
    startColorRunner()
    app.run(host='0.0.0.0', debug=True)
