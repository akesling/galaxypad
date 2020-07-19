import uuid
from typing import Any
from dataclasses import dataclass, field


@dataclass
class Game:
    """
    This should wrap the competition game engine"
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """ Configure the game and run until user click requested"""
        pass

    def click(self, x, y):
        """ Update game with a click from the user """
        # self.game.click(x, y)
        pass

    def to_json(self):
        # display: DrawState = game.get_display()
        # TODO: Convert display to PNG

        return {
            "display_png": "",  # Base64 encoded PNG
            "width": 100,
            "height": 100,
        }
