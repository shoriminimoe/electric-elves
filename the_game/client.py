import asyncio
import json
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


def process_message(message: Message):
    """Process a server message

    This is where the client handles messages from the server
    """
    match message["type"]:
        case MessageType.READY:
            return json.loads(message["content"])
        case MessageType.MOVE:
            # TODO: something meaningful with the message content
            return message["content"]
        case _:
            raise ValueError(f"invalid message type: {message['type']}")


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

    # Wait at this point until the server is ready i.e. waiting for 2 clients
    # to connect
    server_ready = False
    while not server_ready:
        for message in msg_queue:
            msg = Message.deserialize(message)
            if msg["type"] == MessageType.READY:
                result = process_message(msg)
                prey = pygame.Rect(result["prey"][0], result["prey"][1], 10, 10)
                hunter = pygame.Rect(result["hunter"][0], result["hunter"][1], 10, 10)
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

        pygame.draw.rect(screen, "red", prey)
        pygame.draw.rect(screen, "blue", hunter)
        pygame.display.flip()


if __name__ == "__main__":
    main()
