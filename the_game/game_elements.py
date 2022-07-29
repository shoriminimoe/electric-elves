import numpy as np

from enum import IntEnum, auto

from queue import Queue

class CellType(IntEnum):
    EMPTY = auto()
    WALL = auto()

class Map:
    def __init__(self, width, height):
        self.grid = np.array(CellType.EMPTY, (width, height))

        # TODO: Construct a map

    def calc_distances(self, x, y):
        dist = np.array(-1, shape=self.grid.shape)
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


class PlayerType(IntEnum):
    HUNTER = auto()
    PREY = auto()

class Player:
    def __init__(self, x, y, map: Map):
        self.x = x
        self.y = y
        self.map = map
        self.distances = None # used to store distances from a certain point to not have to repeatedly call the dist calc function when checking valid movements
        self.point_distances_calcd = [-1, -1]
        self.type = None

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

