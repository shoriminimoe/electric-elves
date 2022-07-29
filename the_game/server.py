"""Server module"""
import asyncio
import json
import logging
from dataclasses import astuple

import websockets
from websockets.exceptions import ConnectionClosedError
from websockets.server import WebSocketServerProtocol

from .game_elements import Direction, Game
from .messaging import Message, MessageType

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger(__name__)

connected_clients: set[WebSocketServerProtocol] = set()
game = Game()


async def send(websocket, message):
    try:
        await websocket.send(message)
    except websockets.ConnectionClosed:
        pass


def broadcast(message: str):
    for websocket in connected_clients:
        asyncio.create_task(send(websocket, message))


def process_message(message: Message) -> str:
    """Process a client message

    This is where the server-side business logic lives.
    """
    match message["type"]:
        case MessageType.QUIT:
            LOG.info("received a QUIT message. resetting game")
            game.reset()
            return "quit"
        case MessageType.MOVE:
            LOG.info("received a MOVE message")
            game.move_player(Direction(message["content"]))
            return json.dumps(
                {
                    "hunter": (game.hunter.x, game.hunter.y),
                    "prey": (game.prey.x, game.prey.y),
                }
            )
        case _:
            raise ValueError(f"invalid message type: {message['type']}")


async def handler(websocket: WebSocketServerProtocol):
    """Client connection handler"""
    connected_clients.add(websocket)
    LOG.info("client connected: %s", websocket.id)

    try:
        while len(connected_clients) < 2:
            LOG.info(
                f"waiting for 2 clients to connect. connected: {len(connected_clients)}"
            )
            await asyncio.sleep(1)

        if not game.initialized:
            # initiate the game
            # TODO: make sure the player IDs are in the right order
            game.initialize()
            broadcast(
                Message(
                    MessageType.READY,
                    json.dumps(
                        {
                            "hunter": (game.hunter.x, game.hunter.y),
                            "prey": (game.prey.x, game.prey.y),
                        }
                    ),
                ).serialize()
            )

        async for message in websocket:
            LOG.info("message from %s: %s", websocket.id, message)

            try:
                msg = Message.deserialize(message)
                result = process_message(msg)
                response = Message(msg["type"], result)
            except ValueError as exc:
                LOG.error(
                    "failed to process message due to exception: %s %s",
                    f"message: {message!s}",
                    f"exception: {exc}",
                )
                result = str(exc)
                response = Message(MessageType.ERROR, result)

            # send the message to all connected clients
            broadcast(response.serialize())

    except ConnectionClosedError:
        LOG.info("client disconnected: %s", websocket.id)

    finally:
        connected_clients.remove(websocket)


async def main():
    """Server entrypoint"""
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
