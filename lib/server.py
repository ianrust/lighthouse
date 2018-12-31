from flask import Flask, request, jsonify
import queue

from lib.color import Color
from lib.gradient import Gradient

from schedule import get_seconds_now

def set_user_gradient(out_q: queue.Queue):
    try:
        user_gradient = Gradient(
            seconds = get_seconds_now(),
            color_1 = Color(request.json['color'][0]['r'],
                            request.json['color'][0]['g'],
                            request.json['color'][0]['b']),
            color_2 = Color(request.json['color'][1]['r'],
                            request.json['color'][1]['g'],
                            request.json['color'][1]['b']),
            scroll_speed = request.json['scrollspeed'],
            brightness = 0
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

def setup_endoint(app, out_q: queue.Queue):
    app.add_url_rule(
        '/', view_func=set_user_gradient,
        defaults={'out_q': out_q})