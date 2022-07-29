import asyncio
import threading

import pygame
import websockets

from .messaging import Message, MessageType

msg_queue = []  # list of messages to send to the server


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


def main() -> None:
    """Client entry point"""
    pygame.init()
    pygame.display.set_caption("Electric Elves Game")

    screen_size = (800, 600)
    screen = pygame.display.set_mode(screen_size)

    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)

    prey = pygame.Rect(300, 200, 10, 10)
    hunter = pygame.Rect(100, 500, 40, 40)

    messages = ["[SERVER] Test Message 1", "[SERVER] Test Message 2"]
    message_window = pygame.Rect(500, 0, 300, 600)

    # Connect to the server!
    socket_thread = threading.Thread(target=asyncio.run, args=(connect(),))
    socket_thread.daemon = True
    socket_thread.start()

    while True:
        for event in pygame.event.get():
            # Check if window should be closed
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
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

        pygame.draw.rect(screen, "red", prey)
        pygame.draw.rect(screen, "blue", hunter)
        pygame.display.flip()


if __name__ == "__main__":
    main()
