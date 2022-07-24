"""Server module"""
import asyncio
import logging

import websockets
from websockets.exceptions import ConnectionClosedError
from websockets.server import WebSocketServerProtocol

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger(__name__)


connected_clients: set[WebSocketServerProtocol] = set()


async def handler(websocket: WebSocketServerProtocol):
    """Client connection handler"""
    connected_clients.add(websocket)

    try:
        async for message in websocket:
            LOG.info("message from %s: %s", websocket.id, message)

            # TODO handle game state updates

            # send the message to all connected clients
            websockets.broadcast(connected_clients, message)

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
