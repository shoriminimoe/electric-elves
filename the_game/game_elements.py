import random
from dataclasses import dataclass, field
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


class ObjectType(IntEnum):
    """Enumeration for player types"""

    HUNTER = auto()
    PREY = auto()
    STONE = auto()
    TREE = ()


@dataclass
class Object:
    """A game object"""

    id: UUID
    type: ObjectType
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
class Player(Movable):
    """A player"""

    map: Map
    # used to store distances from a certain point to not have to
    # repeatedly call the dist calc function when checking valid movements
    distances: list | None = field(init=False, default=None)
    point_distances_calcd: tuple[int, int] = field(init=False, default=(-1, -1))

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


class Game:
    """A game"""

    def __init__(self):
        self.map = Map(X_SPACES, Y_SPACES)
        self.players = []
        self.objects = []
        self.turns = 0
        self.initialized = False

    def initialize(self):
        """Generate the map and set initial positions"""
        self.players[0].x = random.choice(range(X_SPACES // 4))
        self.players[0].y = random.choice(range(Y_SPACES))
        self.players[1].x = random.choice(range(3 * X_SPACES // 4, X_SPACES))
        self.players[1].y = random.choice(range(Y_SPACES))
        self.turns = 0
        self.initialized = True

    def reset(self):
        """Reset the game"""
        self.__init__()

    def init_player(self, player_id: UUID):
        """Add a player to the game"""
        if len(self.players) >= 2:
            raise RuntimeError("maximum players are added")
        if len(self.players) == 0:
            self.players.append(Player(player_id, ObjectType.HUNTER, -1, -1, self.map))
        else:
            self.players.append(Player(player_id, ObjectType.PREY, -1, -1, self.map))

    def deinit_player(self, player_id: UUID):
        """Remove a player from the game"""
        for player in self.players:
            if player.id == player_id:
                self.players.remove(player)
                break

    def move_player(self, player_id: UUID, direction: Direction):
        """Move a player in the given direction"""
        current_player_idx = self.turns % 2
        if self.players[current_player_idx].id != player_id:
            raise RuntimeError("not your turn")
        self.players[current_player_idx].move(direction)
        self.turns += 1
