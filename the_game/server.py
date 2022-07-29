"""Server module"""
import asyncio
import logging
from dataclasses import astuple
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosedError
from websockets.server import WebSocketServerProtocol

from .game import Game
from .messaging import Message, MessageType

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger(__name__)

connected_clients: set[WebSocketServerProtocol] = set()
game = Game()


def process_message(message: Message) -> Any:
    """Process a client message

    This is where the server-side business logic lives.
    """
    match message["type"]:
        case MessageType.QUIT:
            LOG.info("received a QUIT message. resetting game")
            game.reset()
        case MessageType.MOVE:
            # TODO: something meaningful with the message content
            return message["content"]
        case _:
            raise ValueError(f"invalid message type: {message['type']}")


async def handler(websocket: WebSocketServerProtocol):
    """Client connection handler"""
    connected_clients.add(websocket)

    while len(connected_clients) < 2:
        LOG.info(
            f"waiting for 2 clients to connect. connected: {len(connected_clients)}"
        )
        await asyncio.sleep(1)

    if not game.initialized:
        # initiate the game
        game.initialize()
        websockets.broadcast(
            connected_clients,
            Message(
                MessageType.READY,
                {
                    "hunter": astuple(game.player1.position),
                    "prey": astuple(game.player2.position),
                },
            ).serialize(),
        )

    try:
        async for message in websocket:
            LOG.info("message from %s: %s", websocket.id, message)

            try:
                msg = Message.deserialize(message)
                result = process_message(msg)
                response = Message(msg["type"], result)
            except ValueError as exc:
                LOG.error(
                    "failed to process message due to exception: %s %s",
                    f"message: {message}",
                    f"exception: {exc}",
                )
                result = str(exc)
                response = Message(MessageType.ERROR, result)

            # send the message to all connected clients
            await websocket.send(response.serialize())
            websockets.broadcast(connected_clients, result)

    except ConnectionClosedError:
        LOG.info("client disconnected: %s", websocket.id)

    finally:
        for connection in connected_clients:
            await connection.close()
            connected_clients.remove(connection)
        game.reset()


async def main():
    """Server entrypoint"""
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
