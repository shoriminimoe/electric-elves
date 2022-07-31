"""Server module"""
import asyncio
import json
import logging
from uuid import UUID

import websockets
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol

from game_elements import Direction, Game
from messaging import Message, MessageType

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger(__name__)

connected_clients: set[WebSocketServerProtocol] = set()
game = Game()


async def send(websocket: WebSocketServerProtocol, message: str):
    """Send a serialized message to websocket"""
    try:
        await websocket.send(message)
    except ConnectionClosed:
        pass


def broadcast(message: str):
    """Send a serialized message to all connected clients

    See broadcasting example at https://websockets.readthedocs.io/en/stable/topics/broadcast.html#the-concurrent-way
    """
    for websocket in connected_clients:
        asyncio.create_task(send(websocket, message))


def process_message(message: Message, sender: UUID) -> Message:
    """Process a client message

    This is where the server-side business logic lives.
    """
    match message["type"]:
        case MessageType.QUIT:
            LOG.info("received a QUIT message. resetting game")
            game.reset()
            return Message(MessageType.QUIT, "quit")
        case MessageType.MOVE:
            LOG.info("received a MOVE message")
            try:
                game.move_player(sender, Direction(message["content"]))
            except RuntimeError as exc:
                return Message(MessageType.ERROR, f"{exc}")
            return Message(
                MessageType.MOVE,
                json.dumps(
                    {
                        "hunter": (
                            game.players[0].x,
                            game.players[0].y,
                        ),
                        "prey": (
                            game.players[1].x,
                            game.players[1].y,
                        ),
                    }
                ),
            )
        case _:
            raise ValueError(f"invalid message type: {message['type']}")


async def handler(websocket: WebSocketServerProtocol):
    """Client connection handler"""
    LOG.info("client connected: %s", websocket.id)
    try:
        game.init_player(websocket.id)
    except RuntimeError as exc:
        await websocket.close(reason=f"{exc}")
    connected_clients.add(websocket)

    try:
        while len(connected_clients) < 2:
            LOG.info(
                f"waiting for 2 clients to connect. connected: {len(connected_clients)}"
            )
            # make sure user client hasn't disconnected
            await websocket.ping()
            
            await asyncio.sleep(1)

        LOG.info("Both clients connected! ")

        if not game.initialized:
            # initiate the game
            # TODO: make sure the player IDs are in the right order
            game.initialize()
            broadcast(
                Message(
                    MessageType.READY,
                    json.dumps(
                        {
                            "hunter": (
                                game.players[0].x,
                                game.players[0].y,
                            ),
                            "prey": (
                                game.players[1].x,
                                game.players[1].y,
                            ),
                        }
                    ),
                ).serialize()
            )

        async for message in websocket:
            LOG.info("message from %s: %s", websocket.id, message)

            try:
                msg = Message.deserialize(message)
                response = process_message(msg, websocket.id)
            except ValueError as exc:
                LOG.error(
                    "failed to process message due to exception: %s %s",
                    f"message: {message!s}",
                    f"exception: {exc}",
                )
                response = Message(MessageType.ERROR, str(exc))

            # send the message to all connected clients
            broadcast(response.serialize())

    except ConnectionClosed:
        LOG.info("client disconnected: %s", websocket.id)

    finally:
        connected_clients.remove(websocket)
        game.deinit_player(websocket.id)


async def main():
    """Server entrypoint"""
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
