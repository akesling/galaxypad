import React, {useState, useEffect} from 'react';
import logo from './logo.svg';
import './App.css';

const io = require('socket.io-client');
const socket = io('http://localhost:5000');

// public method for encoding an Uint8Array to base64
function encode(input) {
    var keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    var output = "";
    var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
    var i = 0;

    while (i < input.length) {
        chr1 = input[i++];
        chr2 = i < input.length ? input[i++] : Number.NaN; // Not sure if the index
        chr3 = i < input.length ? input[i++] : Number.NaN; // checks are needed here

        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;

        if (isNaN(chr2)) {
            enc3 = enc4 = 64;
        } else if (isNaN(chr3)) {
            enc4 = 64;
        }
        output += keyStr.charAt(enc1) + keyStr.charAt(enc2) +
            keyStr.charAt(enc3) + keyStr.charAt(enc4);
    }
    return output;
}

function App() {
    const defaultBackendType = "Default"
    const [inGame, setInGame] = useState(false);
    const [gameState, setGameState] = useState(null);
    const [mouseState, setMouseState] = useState({x: 0, y: 0})
    const [gameId, setGameId] = useState("")
    const [isWaitingForServer, setIsWaitingForServer] = useState(false)
    const [gameBackends, setGameBackends] = useState([defaultBackendType])
    const [selectedBackend, setSelectedBackend] = useState(defaultBackendType)

    function createGame() {
        console.log('Creating game...');
        socket.emit('create', {game_type: selectedBackend});
        setInGame(true);
    }

    // Request the list of game backends
    useEffect(() => {
        socket.emit('game_types', {});
    }, []);


    useEffect(() => {
        if (inGame) {
            console.log('joining room');
            // socket.emit('room', {room: 'test-room'});
        }

        return () => {
            if (inGame) {
                console.log('leaving room');
                // socket.emit('leave room', {
                //   room: 'test-room'
                // })
            }
        }
    }, [inGame]);

    useEffect(() => {
        socket.on('game_backends', payload => {
            console.log("FROM game_backends:", payload['backends']);
            setGameBackends(payload['backends'])
        });
        socket.on('join_room', payload => {
            console.log("FROM join_room:", payload);

            var game_id = payload['room'];
            setGameId(game_id)
            socket.emit('join', {room: game_id});

            setIsWaitingForServer(true);
        });
        socket.on('GameState', payload => {
            // console.log("FROM GameState:", payload);
            setIsWaitingForServer(false);
            setGameState(payload);
        });
    }, []); //only re-run the effect if new message comes in

    function over(e) {
        setMouseState({x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY})
    }

    function handleClick(e) {
        if (gameState.is_done || isWaitingForServer) {
            return
        }
        setIsWaitingForServer(true)
        socket.emit('user_click', {click_coordinates: [mouseState.x, mouseState.y], room: gameId})
    }

    return (
        <div className="App">
            <header className="App-header">
                {!inGame &&
                <div>
                    <button onClick={createGame}>Start a game</button>
                    <select onChange={e => setSelectedBackend(e.currentTarget.value)}>
                        {gameBackends.map(item => (
                            <option key={item} value={item}>
                                {item}
                            </option>
                        ))}
                    </select>
                </div>
                }
                {inGame && gameState != null &&
                <div>
                    <img
                        src={`data:image/png;base64,${gameState.display_png}`}
                        onMouseMove={over}
                        onMouseDown={handleClick}
                        // style={{border: '2px solid #0FFa40'}}  // This will distort the image dimensions
                    />
                    <h2>{isWaitingForServer ? "Waiting For Server" : gameState.is_done ? "Game Done" : "Click To Continue"}</h2>
                    <h3>Stats</h3>
                    Total Image Size: {gameState.width}, {gameState.height}
                    <br/>
                    Mouse Position: {mouseState.x}, {mouseState.y}
                    <br/>
                    Backend: {gameState.backend_name}
                </div>
                }
            </header>
        </div>
    );
}

export default App;
