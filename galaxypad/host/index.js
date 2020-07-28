const rust = import('./pkg');

class Display {
    constructor(canvas) {
        this.WIDTH = 512;
        this.HALF_WIDTH = this.WIDTH / 2;
        this.HEIGHT = 512;
        this.HALF_HEIGHT = this.HEIGHT / 2;

        this.canvas = canvas;
        this.ctx = this.canvas.getContext('2d');
        this.data = this.ctx.getImageData(0, 0, this.WIDTH, this.HEIGHT);
        this.initialize();
    }

    initialize() {
        console.log("initializing canvas");

        if (this.ctx.imageSmoothingEnabled !== undefined) {
            this.ctx.imageSmoothingEnabled = false;
        }

        this.canvas.width = this.WIDTH;
        this.canvas.height = this.HEIGHT;

        this.clear();
    }

    registerCallback(onClickHandler) {
        const click = (event) => {
            const click_x = event.layerX;
            const click_y = event.layerY;
            // First, convert to canvas pixel coordinate
            const canvas_x = this.WIDTH * (event.layerX / this.canvas.clientWidth);
            const canvas_y = this.HEIGHT * (event.layerY / this.canvas.clientHeight);
            // Then, adjust to have <0, 0> be in the center of the canvas
            const game_x = this.HALF_WIDTH - canvas_x;
            const game_y = this.HALF_HEIGHT - canvas_y;
            console.log(`Registered click at Element(${click_x}, ${click_y}) => Canvas(${canvas_x}, ${canvas_y}) => Game(${game_x}, ${game_y})`);
            onClickHandler(game_x, game_y);
        };

        this.canvas.addEventListener('mouseup', click);
    }

    clear() {
        this.ctx.clearRect(0, 0, this.WIDTH, this.HEIGHT);
        this.data = this.ctx.getImageData(0, 0, this.WIDTH, this.HEIGHT);
    }

    drawLayers(layers, colors) {
        this.clear();
        for (let i=layers.length-1; i >= 0; i--) {
            this.drawPoints(layers[i], colors[i]);
        }
    }

    drawPoints(points, RGBA) {
        points.forEach((p, index) => {
            this.setPixel(this.data, this.HALF_WIDTH+p[0], this.HALF_HEIGHT+p[1], RGBA);
        });
        this.ctx.putImageData(this.data, 0, 0);
    }

    drawPixels(pixelCoords, RGBA) {
        const new_layer = new ImageData(this.WIDTH, this.HEIGHT);

        pixelCoords.forEach((coord, index) => {
            this.setPixel(new_layer, coord[0], coord[1], RGBA);
        });
        this.ctx.putImageData(new_layer, 0, 0);
    }

    setPixel(image, x, y, RGBA) {
        const redIndex = this.getPixelIndex(image, x, y);
        const blueIndex = redIndex + 1;
        const greenIndex = blueIndex + 1;
        const alphaIndex = greenIndex + 1;

        image.data[redIndex] = RGBA[0];
        image.data[blueIndex] = RGBA[1];
        image.data[greenIndex] = RGBA[2];
        image.data[alphaIndex] = RGBA[3];
    }

    getPixelIndex(image, x, y) {
        const colorChannels = 4;
        return y * (image.width * colorChannels) + x * colorChannels;
    }
}

window.galaxyPadDisplay = new Display(document.getElementById('canvas'));

const LAYER_COLORS = [
    [0, 0, 0, 255], // #000000ff
    [255, 102, 89, 255], // #ff6659ff
    [123, 31, 162, 255], // #7b1fa2ff
    [48, 63, 159, 255], // #303f9fff
    [2, 136, 209, 255], // #0288d1ff
    [0, 121, 107], // #00796bff
    [104, 159, 56], // #689f38ff
    [245, 124, 0], // #f57c00ff
]

rust
  .then(m => {
      console.log("Before", performance.now());
    const renderer = (layers) => {
        console.log(`Javascript rendering: `, layers);
        window.galaxyPadDisplay.drawLayers(layers, LAYER_COLORS);
    }
    const galaxyCallback = m.start_galaxy_pad(renderer);
    window.galaxyPadDisplay.registerCallback((x, y) => {
        console.log("Starting callback", performance.now());
        m.call_callback(galaxyCallback, x, y, renderer);
        console.log("Callback finished", performance.now());
    });
    console.log("After", performance.now());
  })
  .catch(console.error);
