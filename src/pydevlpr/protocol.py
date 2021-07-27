from enum import Enum
import logging
from typing import Tuple

# PacketTypes must be 1 character to avoid overlap with DataTopic
class PacketType():
    SUBSCRIBE = "s"
    DATA = "d"
    UNSUBSCRIBE = "u"

# All DataTopics should be 2 characters to avoid overlap with PacketType
class DataTopic():
    RAW_DATA_TOPIC = "ra"
    FLEX_TOPIC     = "fl"
    PEAK_TO_PEAK_TOPIC = "pp"
    PEAK_AMP_TOPIC  = "pa"
    WINDOW_AVG_TOPIC = "wa"
    NOTCH_60_TOPIC = "60"
    NOTCH_50_TOPIC = "50"

DELIM = "|"  # Agreed upon protocol delimiter with daemon

# Packages the messages in the way that the daemon expects
def wrap(msg_type: PacketType, msg: str) -> str:
    return "{}{}{}".format(str(msg_type), DELIM, msg)

# Extracts the data, pin and topic from the incoming message from the daemon.
def unwrap(msg: str) -> Tuple[str, int, str]:
    unwrapped = msg.split(DELIM, maxsplit=2)
    if len(unwrapped) < 3:
        logging.warning("Invalid message")
        return ("", "", "")
    try:
        pin = int(unwrapped[1])
    except ValueError:
        logging.error("Invalid pin value: {}".format(unwrapped[1]))
        pin = -1
    return (unwrapped[0], pin, unwrapped[2])