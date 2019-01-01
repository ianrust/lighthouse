from typing import Dict

from flask import Flask, request, jsonify
import queue
import sys

from lib.color import Color
from lib.gradient import Gradient
from lib.schedule import get_seconds_since_epoch
from lib.utils import clamp


def get_color_from_dict(color_dict: Dict[str, int]) -> Color:
    return Color(
        red=color_dict['r'],
        green=color_dict['g'],
        blue=color_dict['b'],
    )


def set_user_gradient(out_q: queue.Queue):
    request_json = request.get_json()
    color_1 = get_color_from_dict(request_json['color'][0])
    color_2 = get_color_from_dict(request_json['color'][1])

    scroll_speed = request_json.get('scroll_speed', 0.5)
    scroll_speed = clamp(scroll_speed, 0, 1)

    brightness = request_json.get('brightness', 0.5)
    brightness = clamp(brightness, 0, 1)

    try:
        user_gradient = Gradient(
            seconds=get_seconds_since_epoch(),
            color_1=color_1,
            color_2=color_2,
            scroll_speed=scroll_speed,
            brightness=brightness,
        )

        out_q.put({
            'user_gradient': user_gradient
        })

        print('Received new gradient: {}'.format(user_gradient))
        sys.stdout.flush()

        return jsonify({'success': True}), 201
    except:
        print('Received bad request: {}'.format(request.json))
        sys.stdout.flush()
        return jsonify({'success': False}), 400

def set_fast_mode(out_q: queue.Queue):
    try:
        print(request.json)
        sys.stdout.flush()
        out_q.put({
            'fast_mode': request.json['fast_mode']
        })

        print('Received new fast mode: {}'.format(request.json['fast_mode']))
        sys.stdout.flush()

        return jsonify({'success': True}), 201
    except:
        print('Received bad request: {}'.format(request.json))
        sys.stdout.flush()
        return jsonify({'success': False}), 400

def setup_endpoint(app, out_q: queue.Queue):
    app.add_url_rule(
        '/',
        view_func=set_user_gradient,
        defaults={'out_q': out_q},
        methods=['POST'])
    app.add_url_rule(
        '/fast_mode',
        view_func=set_fast_mode,
        defaults={'out_q': out_q},
        methods=['POST'])
    app.run(host='0.0.0.0', debug=False)
