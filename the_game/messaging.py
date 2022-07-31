import json
import logging
from collections import UserDict
from enum import IntEnum, auto
from typing import Any

from websockets.typing import Data

logging.basicConfig(
    level=logging.DEBUG,
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

    # Signals to the receiver that the sender is ready
    READY = auto()
    # Signals to the receiver that their last message failed
    ERROR = auto()
    MOVE = auto()
    # Signals to the receiver to quit
    QUIT = auto()


class Message(UserDict):
    """Message dictionary

    Use the `serialize` method to prepare the message string for the websocket.
    Use the `deserialize` classmethod to reconstruct a message object from the
    websocket.
    """

    def __init__(self, type: MessageType | int, content: Any, **kwargs):
        if isinstance(type, int):
            type = MessageType(type)

        if type not in MessageType:
            raise ValueError(f"{type} is not a valid MessageType")

        LOG.debug(f"Message(type:{type}, content:{content}")
        super().__init__(type=type, content=content, **kwargs)

    def serialize(self):
        """Return serialized string for message

        Use this method to prepare the message to be sent throught the
        websocket. For example::

            >>> message = Message(type=MessageType.MOVE, content="up")
            >>> socket.send(message.serialize())

        """
        return json.dumps(self.data)

    @classmethod
    def deserialize(cls, message: Data | str):
        """Construct a Message from a serialized Message

        Use this method to construct a Message object from a serialized message
        from the websocket. For example::

            >>> message_str = await socket.recv()
            >>> message = Message.deserialize(message_str))

        This is the reverse operation of `serialize`. So this should always work::

            >>> message = Message(type=MessageType.MOVE, content="up")
            >>> assert message == Message.deserialize(message.serialize())
        """
        LOG.debug(f"deserializing: '{message!s}'")
        try:
            message_dict = json.loads(message)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed message - JSONDecodeError({exc})") from exc

        try:
            return cls(MessageType(message_dict["type"]), message_dict["content"])
        except KeyError as exc:
            raise ValueError("message must include 'type' and 'content' keys") from exc
