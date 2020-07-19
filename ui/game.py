import uuid
from typing import Any
from dataclasses import dataclass, field
import base64
import time


@dataclass
class Game:
    """
    This should wrap the competition game engine"
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """ Configure the game and run until user click requested"""
        self.game_moves = 0

    def click(self, x, y):
        """ Update game with a click from the user """
        # self.game.click(x, y)
        print(f"Got click at ({x}, {y})")
        if self.game_moves <= 4:
            self.game_moves += 1
            time.sleep(1)

    def to_json(self):
        # display: DrawState = game.get_display()
        # TODO: Convert display to PNG

        with open("logo512.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        return {
            "is_done": self.game_moves > 4,
            "display_png": encoded,  # Base64 encoded PNG
            "width": 512,
            "height": 512,
            "backend_name": "Example Game",
        }
