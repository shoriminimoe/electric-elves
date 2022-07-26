"""Server module"""
import asyncio
import logging

import websockets
from websockets.exceptions import ConnectionClosedError
from websockets.server import WebSocketServerProtocol

from messaging import Message, MessageType

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger(__name__)


def process_message(message: Message) -> str:
    """Process a client message

    This is where the server-side business logic lives.
    """
    match message["type"]:
        case MessageType.MOVE:
            # TODO: something meaningful with the message content
            return message["content"]
        case _:
            raise ValueError(f"invalid message type: {message['type']}")


connected_clients: set[WebSocketServerProtocol] = set()


async def handler(websocket: WebSocketServerProtocol):
    """Client connection handler"""
    connected_clients.add(websocket)

    try:
        async for message in websocket:
            LOG.info("message from %s: %s", websocket.id, message)

            try:
                result = process_message(Message.deserialize(message))
            except ValueError as exc:
                LOG.error(
                    "failed to process message due to exception: %s %s",
                    f"message: {message}",
                    f"exception: {exc}",
                )
                result = str(exc)

            # send the message to all connected clients
            websockets.broadcast(connected_clients, result)

    except ConnectionClosedError:
        # TODO handle the game state for disconnection errors
        LOG.info("disconnection error for %s", websocket.id)

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
