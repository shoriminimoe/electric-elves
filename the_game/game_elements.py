import random
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from queue import Queue
from uuid import UUID

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
    """Enumeration for setting cell contents"""

    EMPTY = auto()
    WALL = auto()


class Map:
    """A game map"""

    def __init__(self, width: int, height: int):
        self.grid = np.full((width, height), CellType.EMPTY)

        # TODO: Construct a map

    def calc_distances(self, x, y):
        """Calculate distances"""
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


class Obstacle(Object):
    """An obstacle"""


class PlayerType(IntEnum):
    """Enumeration for player types"""

    HUNTER = auto()
    PREY = auto()


@dataclass
class Player(Movable):
    """A player"""

    def __init__(self, x, y, map: Map):
        super().__init__(x, y)
        self.map = map
        # used to store distances from a certain point to not have to
        # repeatedly call the dist calc function when checking valid movements
        self.distances = None
        self.point_distances_calcd = [-1, -1]

    # mp = movement points
    def is_valid(self, x, y, nx, ny, mp):
        """Return True if the movement is legal"""
        if self.distances is None or self.point_distances_calcd != (x, y):
            self.distances = self.map.calc_distances(x, y)
            self.point_distances_calcd = (x, y)

        return self.distances[ny][nx] <= mp

    def update(self, nx, ny):
        """Update the player position"""
        self.x, self.y = nx, ny
        self.distances = None


class Hunter(Player):
    """The hunter"""

    def __init__(self, x, y, map: Map):
        super().__init__(x, y, map)
        self.type = PlayerType.HUNTER


class Prey(Player):
    """The prey"""

    def __init__(self, x, y, map: Map):
        super().__init__(x, y, map)
        self.type = PlayerType.PREY


class Game:
    """A game"""

    def __init__(self):
        self.map = Map(X_SPACES, Y_SPACES)
        self.player_ids = []
        self.players = {}
        self.objects = {}
        self.turns = 0
        self.initialized = False

    def initialize(self):
        """Generate the map and set initial positions"""
        self.players[self.player_ids[0]] = Hunter(
            random.choice(range(X_SPACES // 4)),
            random.choice(range(Y_SPACES)),
            self.map,
        )
        self.players[self.player_ids[1]] = Prey(
            random.choice(range(X_SPACES // 4, X_SPACES)),
            random.choice(range(Y_SPACES)),
            self.map,
        )
        self.turns = 0
        self.initialized = True

    def reset(self):
        """Reset the game"""
        self.player_ids = []
        self.players = {}
        self.initialized = False

    def init_player(self, player_id: UUID):
        """Add a player to the game"""
        if len(self.player_ids) >= 2:
            raise RuntimeError("maximum players are added")
        if len(self.player_ids) == 0:
            self.players[player_id] = Hunter(-1, -1, self.map)
        else:
            self.players[player_id] = Prey(-1, -1, self.map)
        self.player_ids.append(player_id)

    def move_player(self, player_id: UUID, direction: Direction):
        """Move a player in the given direction"""
        current_player_id = self.player_ids[self.turns % 2]
        if current_player_id != player_id:
            raise RuntimeError("not your turn")
        self.players[current_player_id].move(direction)
        self.turns += 1
