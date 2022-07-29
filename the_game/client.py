import asyncio
import json
import threading

import pygame
import websockets

from .game import X_SPACES, Y_SPACES
from .messaging import Message, MessageType

msg_queue = []  # list of messages to send to the server

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
            msg = msg_queue[0]
            msg_queue.remove(msg)
            await socket.send(msg)
        await asyncio.sleep(0.1)


async def recv(socket):
    """Recieves data from the server"""
    while True:
        print(await socket.recv())


async def connect():
    """Joins the websocket server"""
    async with websockets.connect("ws://localhost:8001") as socket:
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
        case MessageType.READY:
            initial_positions = json.loads(message["content"])
            for thing, (x, y) in initial_positions.items():
                initial_positions[thing] = convert_position(x, y)
            return initial_positions
        case MessageType.MOVE:
            # TODO: something meaningful with the message content
            return message["content"]
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
    message_window = pygame.Rect(500, 0, 300, 600)

    # Connect to the server!
    socket_thread = threading.Thread(target=asyncio.run, args=(connect(),))
    socket_thread.daemon = True
    socket_thread.start()

    screen.fill("black")
    screen.blit(
        font.render("Waiting for server...", True, "lightgray"),
        (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2),
    )

    # Wait at this point until the server is ready i.e. waiting for 2 clients
    # to connect
    server_ready = False
    while not server_ready:
        for message in msg_queue:
            msg = Message.deserialize(message)
            if msg["type"] == MessageType.READY:
                result = process_message(msg)
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    msg_queue.append(
                        Message(MessageType.MOVE, "left click test").serialize()
                    )

        clock.tick(60)

        screen.fill("black")

        # Draw Messages
        screen.fill((127, 127, 127), message_window)
        screen.blit(font.render("Messages", True, "white"), (525, 25))
        for i, message in enumerate(messages):
            screen.blit(font.render(message, True, "lightgray"), (525, 60 + i * 25))

        pygame.draw.rect(screen, "red", game_objects["prey"])
        pygame.draw.rect(screen, "blue", game_objects["hunter"])
        pygame.display.flip()


if __name__ == "__main__":
    main()
