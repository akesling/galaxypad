import uuid
from typing import Any, Tuple
from dataclasses import dataclass, field
import base64
import time
from abc import abstractmethod


@dataclass
class AbstractGame:
    """
    This should wrap the competition game engine"
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @abstractmethod
    def click(self, x: int, y: int):
        raise NotImplemented

    @abstractmethod
    def get_display(self) -> Tuple[Any, int, int]:
        """ Returns a PNG, width, and height """
        # display: DrawState = game.get_display()
        raise NotImplemented

    @abstractmethod
    def is_done(self) -> bool:
        raise NotImplemented

    @classmethod
    @abstractmethod
    def name(cls):
        return cls.__name__

    def to_json(self):
        png, w, h = self.get_display()
        encoded = base64.b64encode(png).decode()

        return {
            "is_done": self.is_done(),
            "display_png": encoded,  # Base64 encoded PNG
            "width": w,
            "height": h,
            "backend_name": self.name(),
        }

    def render(self, png):
        # Call this function to push an updated game state to the client
        # TODO: Implement this
        pass


@dataclass
class ExampleGame(AbstractGame):
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

    def get_display(self):
        with open("logo512.png", "rb") as f:
            png = f.read()
        return png, 512, 512

    def is_done(self) -> bool:
        return self.game_moves > 4

    @classmethod
    def name(cls):
        return cls.__name__
