import os
from typing import Dict

from flask import Flask, send_from_directory, render_template
from flask_socketio import SocketIO, join_room, emit
# from flask_cors import CORS

from game_wrapper import ExampleGame

# initialize Flask
app = Flask(__name__, static_folder='/solution/ui/frontend/build')
# CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
ROOMS: Dict[str, ExampleGame] = {}  # dict to track active rooms

# Websocket message types
GAME_STATE = "GameState"

# Add game backends here
REGISTERED_BACKENDS = {
    "Default": ExampleGame,
    ExampleGame.name(): ExampleGame,
}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@socketio.on('game_types')
def on_request_game_types(data):
    """Create a game lobby"""
    print("Transmit backends list")
    emit('game_backends', {'backends': list(REGISTERED_BACKENDS.keys())})


@socketio.on('create')
def on_create(data):
    """Create a game lobby"""
    print("Creating room.")
    gm = REGISTERED_BACKENDS[data['game_type']]()
    room = gm.id
    ROOMS[room] = gm
    join_room(room)
    emit('join_room', {'room': room})


@socketio.on('join')
def on_join(data):
    """Join a game lobby"""
    room = data['room']
    if room in ROOMS:
        join_room(room)
        emit(GAME_STATE, ROOMS[room].to_json(), room=room)
    else:
        emit('error', {'error': 'Unable to join room. Room does not exist.'})


@socketio.on('user_click')
def on_user_click(data):
    room = data['room']
    click_x, click_y = data['click_coordinates']
    if room not in ROOMS:
        emit('error', {'error': 'Unable to join room. Room does not exist.'})

    ROOMS[room].click(click_x, click_y)
    emit(GAME_STATE, ROOMS[room].to_json(), room=room)


if __name__ == '__main__':
    print("Starting game server")
    socketio.run(app, debug=True, host='0.0.0.0')
