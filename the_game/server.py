"""Server module"""
import asyncio
import json
import logging
from collections import UserDict
from enum import IntEnum, auto

import websockets
from websockets.exceptions import ConnectionClosedError
from websockets.server import WebSocketServerProtocol

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger(__name__)


class MessageType(IntEnum):
    """MessageType enum

    This enum represents all valid message types the server will process. To
    add a new message type:

        1. Add the name to this class definition
        2. Add a case in the match statement of `process_message` to handle the
           message type
    """

    MOVE = auto()


class Message(UserDict):
    """Message dictionary

    Use the `serialize` method to prepare the message string for the websocket.
    Use the `deserialize` classmethod to reconstruct a message object from the
    websocket.
    """

    def __init__(self, type: MessageType | int, content: str):
        if isinstance(type, int):
            type = MessageType(type)

        if type not in MessageType:
            raise ValueError(f"{type} is not a valid MessageType")

        LOG.debug(f"Message(type:{type}, content:{content}")
        self._type_value = type.value
        super().__init__(type=type, content=content)

    def serialize(self):
        """Return serialized string for message

        Use this method to prepare the message to be sent throught the
        websocket. For example::

            >>> message = Message(type=MessageType.MOVE, content="up")
            >>> socket.send(message.serialize())

        """
        return json.dumps(self.data)

    @classmethod
    def deserialize(cls, message: str):
        """Construct a Message from a serialized Message

        Use this method to construct a Message object from a serialized message
        from the websocket. For example::

            >>> message_str = await socket.recv()
            >>> message = Message.deserialize(message_str))

        This is the reverse operation of `serialize`. So this should always work::

            >>> message = Message(type=MessageType.MOVE, content="up")
            >>> assert message == Message.deserialize(message.serialize())
        """
        LOG.info(f"Creating new Message from message: {message}")
        try:
            message_dict = json.loads(message)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed message - JSONDecodeError({exc})") from exc

        try:
            return cls(MessageType(message_dict["type"]), message_dict["content"])
        except KeyError as exc:
            raise ValueError("message must include 'type' and 'content' keys") from exc


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

            # TODO handle game state updates
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
