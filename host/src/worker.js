const rust = import('../pkg');

const INITIALIZED = 0
const WORKING = 1
const WAITING = 2

if (self.Worker) {
    let state = INITIALIZED;
    self.onmessage = function({data}) {
        const msg = data;

        if (state === INITIALIZED) {
            state = WORKING;
            console.log('Message received from main script');
            rust
                .then(m => {
                    const renderer = (layers) => {
                        console.log(`Passing Drawlist to main: `, layers);
                        self.postMessage({layers: layers});
                    }
                    const galaxyCallback = m.start_galaxy_pad(renderer);
                    self.click_callback = ((x, y) => {
                        console.log("Starting callback", performance.now());
                        m.call_callback(galaxyCallback, x, y, renderer);
                        console.log("Callback finished", performance.now());
                    });
                    state = WAITING;
                })
                .catch(console.error);
        } else if (state === WORKING) {
            self.postMessage({err: new Error("Already working, ignoring message.")});
        } else if (state === WAITING) {
            state = WORKING;
            if (msg.click) {
                self.click_callback(msg.click.x, msg.click.y);
            } else {
                self.postMessage({err: new Error("Unknown message received", msg)});
            }
            state = WAITING;
        } else {
            self.postMessage({err: new Error("Unknown state achieved, ignoring message")});
        }
    }
}
