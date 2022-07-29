import enum
import random
from dataclasses import dataclass

# The number of spaces on the grid
# Keep in mind that the grid is 0-indexed, so the only valid positions are:
# 0 <= x < X_SPACES
# 0 <= y < Y_SPACES
X_SPACES = 16
Y_SPACES = 12


class Direction(enum.Enum):
    """A movement direction"""

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass
class Point:
    """The ordered pair position of a game object"""

    x: int
    y: int


@dataclass
class Object:
    """A game object"""

    position: Point

    def move(self, direction: Direction):
        """Move object one space in `direction`"""
        match direction:
            case Direction.UP:
                self.position.y -= 1
            case Direction.DOWN:
                self.position.y += 1
            case Direction.LEFT:
                self.position.x -= 1
            case Direction.RIGHT:
                self.position.x += 1

        # TODO: Add obstacle check?

        # bounds check
        if self.position.y < 0:
            self.position.y = 0
        if self.position.y >= Y_SPACES:
            self.position.y = Y_SPACES - 1
        if self.position.x < 0:
            self.position.x = 0
        if self.position.x >= X_SPACES:
            self.position.x = X_SPACES - 1


@dataclass
class Player(Object):
    """A player"""


class Obstacle(Object):
    """An obstacle"""


class Game:
    """A game"""

    def __init__(self):
        self.player1 = Player(Point(-1, -1))
        self.player2 = Player(Point(-1, -1))
        self.turns = 0
        self.initialized = False

    def initialize(self):
        """Generate the map and set initial positions"""
        self.player1.position = Point(
            x=random.choice(range(X_SPACES // 4)),
            y=random.choice(range(Y_SPACES)),
        )
        self.player2.position = Point(
            x=random.choice(range(3 * X_SPACES // 4, X_SPACES)),
            y=random.choice(range(Y_SPACES)),
        )
        self.turns = 0
        self.initialized = True

    def reset(self):
        """Reset the game"""
        self.initialize()
