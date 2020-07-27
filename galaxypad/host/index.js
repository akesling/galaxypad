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

//        this.drawPoints([[0, 0], [1, 0], [1, 1], [2, 2], [3, 3], [4, 4]], [0, 0, 0, 255]);
    }

    clear() {
        this.ctx.clearRect(0, 0, this.WIDTH, this.HEIGHT);
        this.data = this.ctx.getImageData(0, 0, this.WIDTH, this.HEIGHT);
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

rust
  .then(m => {
      console.log("Before", performance.now());
      try {
        const renderer = (points) => {
            console.log(`Javascript rendering: [${points}]`, points);
            window.galaxyPadDisplay.drawPoints(points, [0, 0, 0, 255]);
        }
        m.start_galaxy_pad(renderer);
      } catch (e) {
          console.log("Caught", e);
          console.log("Continuing...");
      }
      console.log("After", performance.now());
  })
  .catch(console.error);
