from itertools import cycle

import numpy as np
import pygame


class Tileset:
    """A tileset"""

    def __init__(self, file, size=(16, 16), margin=1, spacing=1):
        self.file = file
        self.size = size
        self.margin = margin
        self.spacing = spacing
        self.image = pygame.image.load(file)
        self.scaled_image = self.image
        self.rect = self.scaled_image.get_rect()
        self.tiles = []
        self.load()

    def load(self):
        """Load the tileset"""
        self.tiles = []
        x0 = y0 = self.margin
        w, h = self.rect.size
        dx = self.size[0] + self.spacing
        dy = self.size[1] + self.spacing

        for x in range(x0, w, dx):
            for y in range(y0, h, dy):
                tile = pygame.Surface(self.size)
                tile.blit(self.scaled_image, (0, 0), (x, y, *self.size))
                self.tiles.append(tile)

    def rescale(self, scale):
        """Rescaled the tileset"""
        self.scaled_image = pygame.transform.rotozoom(self.image, 0, scale)
        self.rect = self.scaled_image.get_rect()
        self.load()

    def __str__(self):
        return f"{self.__class__.__name__} file:{self.file} tile:{self.size}"


class Tilemap:
    """A tilemap"""

    def __init__(self, tileset, size=(10, 20), tile_size=16, rect=None):
        self.size = size
        self.tileset = tileset
        self.map = np.zeros(size, dtype=int)
        self.tile_size = tile_size

        self.image = pygame.Surface(tuple(map(lambda x: x * tile_size, size)))
        if rect:
            self.rect = pygame.Rect(rect)
        else:
            self.rect = self.image.get_rect()

    def render(self):
        """Render the tilemap"""
        m, n = self.map.shape
        for i in range(m):
            for j in range(n):
                tile = self.tileset.tiles[self.map[i, j]]
                self.image.blit(tile, (j * self.tile_size, i * self.tile_size))

    def set_random(self):
        """Randomly set the tilemap"""
        n = len(self.tileset.tiles)
        self.map = np.random.randint(n, size=self.size)
        self.render()

    def set_ordered(self):
        """Set the tilemap in order"""
        n = len(self.tileset.tiles)
        n_cells = self.size[0] * self.size[1]
        tile_cycle = cycle(range(n))
        array = [next(tile_cycle) for _ in range(n_cells)]
        self.map = np.reshape(array, self.size)
        print(self.map)
        self.render()

    def __str__(self):
        return f"{self.__class__.__name__} {self.size}"
