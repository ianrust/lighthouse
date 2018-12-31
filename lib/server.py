from flask import Flask, request, jsonify
import queue
import sys

from lib.color import Color
from lib.gradient import Gradient
from lib.schedule import get_seconds_now

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
            scroll_speed = 0.01, # TODO send a real one
            brightness = 0 # TODO send a real one
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

def setup_endpoint(app, out_q: queue.Queue):
    app.add_url_rule(
        '/',
        view_func=set_user_gradient,
        defaults={'out_q': out_q},
        methods=['POST'])
    app.run(host='0.0.0.0', debug=True)