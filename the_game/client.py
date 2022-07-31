import asyncio
import json
import logging
import threading
from collections import deque
from pathlib import Path
from time import sleep

import numpy as np
import pygame
import websockets

from .game_elements import X_SPACES, Y_SPACES
from .messaging import Message, MessageType
from .tiles import Tilemap, Tileset

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

msg_queue: list = []  # list of messages to send to the server
msgs_received: deque = deque()
print_items: deque = deque(maxlen=20)

SCREEN_SIZE = (1100, 600)
GAME_AREA = (
    0,
    0,
    800,
    SCREEN_SIZE[1],
)
GRID_WIDTH = GAME_AREA[2] // X_SPACES
GRID_HEIGHT = GAME_AREA[3] // Y_SPACES
# The tileset is 16x16
SCALE = GRID_WIDTH / 16
OBJECT_SIZE = (GRID_WIDTH * 0.8, GRID_HEIGHT * 0.8)
MESSAGE_AREA = (
    GAME_AREA[2],
    0,
    SCREEN_SIZE[0] - GAME_AREA[2],
    SCREEN_SIZE[1],
)
tileset = Tileset(
    Path(Path(__file__).parent, "static", "tileset.png"),
    size=(GRID_WIDTH, GRID_HEIGHT),
    margin=0,
    spacing=0,
)
tilemap = Tilemap(tileset, (Y_SPACES, X_SPACES), GRID_WIDTH)


async def send(socket):
    """Sends data to the server"""
    while True:
        if msg_queue:  # checks if there is something in the list
            msg = msg_queue.pop(0)
            await socket.send(msg.serialize())
        await asyncio.sleep(0.1)


async def recv(socket):
    """Recieves data from the server"""
    while True:
        message = await socket.recv()
        LOG.debug(f"received message from server: {message}")
        try:
            process_message(Message.deserialize(message))
        except ValueError:
            LOG.warning("received invalid message: '%s'", message)
        await asyncio.sleep(0.1)


async def connect():
    """Joins the websocket server"""
    async with websockets.connect("ws://localhost:8001") as socket:
        LOG.debug(f"connected to server as {socket.id}")
        await asyncio.gather(recv(socket), send(socket))


def convert_position(x: int, y: int) -> tuple[int, int]:
    """Convert a grid indexed point to a pixel indexed point"""
    return (x * GRID_WIDTH, y * GRID_HEIGHT)


server_ready = False
game_objects: dict[(str, list[pygame.Rect])] = {
    "prey": [pygame.Rect((300, 200), OBJECT_SIZE)],
    "hunter": [pygame.Rect((100, 500), OBJECT_SIZE)],
    "map": [],
    "tree": [],
}


def process_message(message: Message):
    """Process a server message

    This is where the client handles messages from the server

    Note:
        Game object positions come through indexed by the game grid. These need
        to be converted to pixels based on the screen size.
    """
    global server_ready
    match message["type"]:
        case MessageType.READY | MessageType.MOVE:
            positions = json.loads(message["content"])
            # TODO: set the tilemap `map` attribute here then call
            # tilemap.render() below
            for thing, value in positions.items():
                for (x, y) in value:
                    game_objects[thing].append(
                        pygame.Rect(convert_position(x, y), OBJECT_SIZE)
                    )
            server_ready = True
        case MessageType.ERROR:
            print_items.append(message["content"])
        case _:
            raise ValueError(f"invalid message type: {message['type']}")


def main() -> None:
    """Client entry point"""
    pygame.init()
    pygame.display.set_caption("Electric Elves Game")

    screen = pygame.display.set_mode(SCREEN_SIZE)
    tileset.image.convert()
    tileset.rescale(SCALE)
    tilemap.image = screen
    tilemap.map = np.full((Y_SPACES, X_SPACES), 15)

    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)

    message_window = pygame.Rect(MESSAGE_AREA)

    # Connect to the server!
    LOG.debug("connecting to server")
    socket_thread = threading.Thread(target=asyncio.run, args=(connect(),))
    socket_thread.daemon = True
    socket_thread.start()

    screen.fill("black")
    screen.blit(
        font.render("Waiting for game to start...", True, "lightgray"),
        (SCREEN_SIZE[0] // 2 - 75, SCREEN_SIZE[1] // 2),
    )
    pygame.display.update()

    # Wait at this point until the server is ready i.e. waiting for 2 clients
    # to connect. `server_ready` is set to True once the READY message has been
    # received and processed.
    while not server_ready:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                msg_queue.append(Message(MessageType.QUIT, ""))
                return
        LOG.debug("waiting for other client")
        sleep(0.1)

    # Draw Messages
    screen.fill("black")
    screen.fill((127, 127, 127), message_window)
    screen.blit(font.render("Messages", True, "white"), (825, 25))

    tilemap.render()
    # for stone in game_objects["stone"]:
    #     pygame.draw.rect(screen, "grey", stone)
    #
    # for tree in game_objects["tree"]:
    #     pygame.draw.rect(screen, "green", tree)

    while True:
        for event in pygame.event.get():
            # Check if window should be closed
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                msg_queue.append(Message(MessageType.QUIT, ""))
                return
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_UP,
                pygame.K_DOWN,
                pygame.K_RIGHT,
                pygame.K_LEFT,
            ):
                msg_queue.append(Message(MessageType.MOVE, event.key))
                sleep(0.1)

        clock.tick(60)

        for i, message in enumerate(print_items):
            screen.blit(font.render(message, True, "lightgray"), (825, 60 + i * 25))

        pygame.draw.rect(screen, "red", game_objects["prey"][0])
        pygame.draw.rect(screen, "blue", game_objects["hunter"][0])
        pygame.display.flip()


if __name__ == "__main__":
    try:
        main()
    finally:
        msg_queue.append(Message(MessageType.QUIT, ""))
