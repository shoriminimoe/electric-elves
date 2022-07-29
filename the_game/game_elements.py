import random
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from queue import Queue

import numpy as np
import pygame

# The number of spaces on the grid
# Keep in mind that the grid is 0-indexed, so the only valid positions are:
# 0 <= x < X_SPACES
# 0 <= y < Y_SPACES
X_SPACES = 16
Y_SPACES = 12


class Direction(Enum):
    """A movement direction"""

    UP = pygame.K_UP
    DOWN = pygame.K_DOWN
    LEFT = pygame.K_LEFT
    RIGHT = pygame.K_RIGHT


class CellType(IntEnum):
    EMPTY = auto()
    WALL = auto()


class Map:
    def __init__(self, width: int, height: int):
        self.grid = np.full((width, height), CellType.EMPTY)

        # TODO: Construct a map

    def calc_distances(self, x, y):
        dist = np.full_like(self.grid, -1)
        dist[y][x] = 0

        q = Queue()
        q.put([x, y])

        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        while q.not_empty:
            x, y = q.get()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if dist[y][x] + 1 < dist[ny][nx] or dist[ny][nx] == -1:
                    dist[ny][nx] = dist[y][x] + 1
                    q.put([nx, ny])

        return dist


@dataclass
class Object:
    """A game object"""

    x: int
    y: int


@dataclass
class Movable(Object):
    """A movable object"""

    def move(self, direction: Direction):
        """Move object one space in `direction`"""
        match direction:
            case Direction.UP:
                self.y -= 1
            case Direction.DOWN:
                self.y += 1
            case Direction.LEFT:
                self.x -= 1
            case Direction.RIGHT:
                self.x += 1

        # TODO: Add obstacle check?

        # bounds check
        if self.y < 0:
            self.y = 0
        if self.y >= Y_SPACES:
            self.y = Y_SPACES - 1
        if self.x < 0:
            self.x = 0
        if self.x >= X_SPACES:
            self.x = X_SPACES - 1


@dataclass
class Point:
    """The ordered pair position of a game object"""

    x: int
    y: int


class Obstacle(Object):
    """An obstacle"""


class PlayerType(IntEnum):
    HUNTER = auto()
    PREY = auto()


@dataclass
class Player(Movable):
    def __init__(self, x, y, map: Map):
        super().__init__(x, y)
        self.map = map
        self.distances = None  # used to store distances from a certain point to not have to repeatedly call the dist calc function when checking valid movements
        self.point_distances_calcd = [-1, -1]

    # mp = movement points
    def is_valid(self, x, y, nx, ny, mp):
        if self.distances is None or self.point_distances_calcd != (x, y):
            self.distances = self.map.calc_distances(x, y)
            self.point_distances_calcd = (x, y)

        return self.distances[ny][nx] <= mp

    def update(self, nx, ny):
        self.x, self.y = nx, ny
        self.distances = None


class Hunter(Player):
    def __init__(self, x, y, map: Map):
        super().__init__(x, y, map)
        self.type = PlayerType.HUNTER


class Prey(Player):
    def __init__(self, x, y, map: Map):
        super().__init__(x, y, map)
        self.type = PlayerType.PREY


class Game:
    """A game"""

    def __init__(self):
        self.map = Map(X_SPACES, Y_SPACES)
        self.hunter = Hunter(-1, -1, self.map)
        self.prey = Prey(-1, -1, self.map)
        self.objects = {}
        self.turns = 0
        self.initialized = False

    def initialize(self):
        """Generate the map and set initial positions"""
        self.hunter.x = random.choice(range(X_SPACES // 4))
        self.hunter.y = random.choice(range(Y_SPACES))
        self.prey.x = random.choice(range(3 * X_SPACES // 4, X_SPACES))
        self.prey.y = random.choice(range(Y_SPACES))
        self.turns = 0
        self.current_player = self.hunter
        self.initialized = True

    def reset(self):
        """Reset the game"""
        self.initialized = False

    def move_player(self, direction: Direction):
        """Move an object in the given direction"""
        self.current_player.move(direction)
        if self.current_player == self.hunter:
            self.current_player = self.prey
        else:
            self.current_player = self.hunter
        self.turns += 1
