import numpy as np
import pygame


class Tileset:
    """A tileset"""

    def __init__(self, file, size=(16, 16), margin=1, spacing=1):
        self.file = file
        self.size = size
        self.margin = margin
        self.spacing = spacing
        self.image = pygame.image.load(file).convert()
        self.rect = self.image.get_rect()
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
                tile.blit(self.image, (0, 0), (x, y, *self.size))
                self.tiles.append(tile)

    def __str__(self):
        return f"{self.__class__.__name__} file:{self.file} tile:{self.size}"


class Tilemap:
    """A tilemap"""

    def __init__(self, tileset, screen, size=(10, 20), rect=None):
        self.size = size
        self.tileset = tileset
        self.map = np.zeros(size, dtype=int)

        self.image = screen
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
                self.image.blit(tile, (j * 16, i * 16))

    def set_random(self):
        """Randomly set the tilemap"""
        n = len(self.tileset.tiles)
        self.map = np.random.randint(n, size=self.size)
        print(self.map)
        self.render()

    def __str__(self):
        return f"{self.__class__.__name__} {self.size}"
