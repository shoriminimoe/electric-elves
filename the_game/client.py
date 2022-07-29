import asyncio
import json
import logging
import threading
from collections import deque
from time import sleep

import pygame
import websockets

from .game_elements import X_SPACES, Y_SPACES
from .messaging import Message, MessageType

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

msg_queue = []  # list of messages to send to the server
inbound_messages = deque()

SCREEN_SIZE = (1100, 600)
GAME_AREA = (
    0,
    0,
    800,
    SCREEN_SIZE[1],
)
GRID_WIDTH = GAME_AREA[2] / X_SPACES
GRID_HEIGHT = GAME_AREA[3] / Y_SPACES
OBJECT_SIZE = (GRID_WIDTH * 0.8, GRID_HEIGHT * 0.8)
MESSAGE_AREA = (
    GAME_AREA[2],
    0,
    SCREEN_SIZE[0] - GAME_AREA[2],
    SCREEN_SIZE[1],
)


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
        inbound_messages.append(message)
        await asyncio.sleep(0.1)


async def connect():
    """Joins the websocket server"""
    async with websockets.connect("ws://localhost:8001") as socket:
        LOG.debug(f"connected to server as {socket.id}")
        await asyncio.gather(recv(socket), send(socket))


def convert_position(x: int, y: int) -> tuple[int, int]:
    """Convert a grid indexed point to a pixel indexed point"""
    return (x * GRID_WIDTH, y * GRID_HEIGHT)


def process_message(message: Message):
    """Process a server message

    This is where the client handles messages from the server

    Note:
        Game object positions come through indexed by the game grid. These need
        to be converted to pixels based on the screen size.
    """
    match message["type"]:
        case MessageType.READY | MessageType.MOVE:
            positions = json.loads(message["content"])
            for thing, (x, y) in positions.items():
                positions[thing] = convert_position(x, y)
            return positions
        case _:
            raise ValueError(f"invalid message type: {message['type']}")


def main() -> None:
    """Client entry point"""
    pygame.init()
    pygame.display.set_caption("Electric Elves Game")

    screen = pygame.display.set_mode(SCREEN_SIZE)

    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)

    game_objects = {
        "prey": pygame.Rect((300, 200), OBJECT_SIZE),
        "hunter": pygame.Rect((100, 500), OBJECT_SIZE),
    }

    messages = ["[SERVER] Test Message 1", "[SERVER] Test Message 2"]
    message_window = pygame.Rect(MESSAGE_AREA)

    # Connect to the server!
    LOG.debug("connecting to server")
    socket_thread = threading.Thread(target=asyncio.run, args=(connect(),))
    socket_thread.daemon = True
    socket_thread.start()

    screen.fill("black")
    screen.blit(
        font.render("Waiting for server...", True, "lightgray"),
        (SCREEN_SIZE[0] // 2 - 75, SCREEN_SIZE[1] // 2),
    )
    pygame.display.update()

    # Wait at this point until the server is ready i.e. waiting for 2 clients
    # to connect
    server_ready = False
    while not server_ready:
        LOG.debug("waiting for other client")
        if inbound_messages:
            message = Message.deserialize(inbound_messages.popleft())
            if message["type"] == MessageType.READY:
                # Any other messages from the server are discarded at this
                # point
                result = process_message(message)
                for thing, position in result.items():
                    game_objects[thing] = pygame.Rect(position, OBJECT_SIZE)
                server_ready = True
                break

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
                # FIXME: wait for new positions. this is a bad way to do it.
                sleep(0.1)
                message = Message.deserialize(inbound_messages.popleft())
                result = process_message(message)
                for thing, position in result.items():
                    game_objects[thing] = pygame.Rect(position, OBJECT_SIZE)

        clock.tick(60)

        screen.fill("black")

        # Draw Messages
        screen.fill((127, 127, 127), message_window)
        screen.blit(font.render("Messages", True, "white"), (825, 25))
        for i, message in enumerate(messages):
            screen.blit(font.render(message, True, "lightgray"), (825, 60 + i * 25))

        pygame.draw.rect(screen, "red", game_objects["prey"])
        pygame.draw.rect(screen, "blue", game_objects["hunter"])
        pygame.display.flip()


if __name__ == "__main__":
    try:
        main()
    finally:
        msg_queue.append(Message(MessageType.QUIT, ""))
