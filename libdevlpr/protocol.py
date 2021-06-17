from enum import Enum
from typing import Tuple

class PacketType(Enum):
    SUBSCRIBE = "s"
    DATA = "d"
    UNSUBSCRIBE = "u"
    def __str__(self) -> str:
        return self.value

PROTOCOL = "|"

RAW_DATA_TOPIC = "r"
MAIN_DATA_TOPIC = "d"
GRIP_RIGHT_TOPIC = "gr"
GRIP_LEFT_TOPIC = "gl"

def wrap(msg_type: PacketType, msg: str) -> str:
    return "{}{}{}".format(str(msg_type), PROTOCOL, msg)

def unwrap(msg: str) -> Tuple[str, str]:
    unwrapped = msg.split(PROTOCOL, maxsplit=1)
    if len(unwrapped) < 2:
        print("[Warn] Invalid message")
        return ("", "")
    return (unwrapped[0], unwrapped[1])