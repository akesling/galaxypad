from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, emit, send
from game import Game
from typing import Dict

# initialize Flask
app = Flask(__name__)
socketio = SocketIO(app)
ROOMS: Dict[str, Game] = {}  # dict to track active rooms

# Websocket message types
GAME_STATE = "GameState"

@app.route('/')
def index():
    """Serve the index HTML"""
    return render_template('index.html')


@socketio.on('create')
def on_create(data):
    """Create a game lobby"""
    print("Creating room.")
    gm = Game()
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
    """ flip card and rebroadcast game object """
    room = data['room']
    click_x, click_y = data['click_coordinates']
    ROOMS[room].click(click_x, click_y)
    emit(GAME_STATE, ROOMS[room].to_json(), room=room)


if __name__ == '__main__':
    print("Starting game server")
    socketio.run(app, debug=True, host='0.0.0.0')
