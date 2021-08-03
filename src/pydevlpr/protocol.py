import logging
from typing import Tuple

class PacketType():
    """Shorthands for the packet types the daemon sends/recvs.
    
    PacketTypes must be 1 character to avoid overlap with DataTopic.
    """

    SUBSCRIBE = "s"
    DATA = "d"
    UNSUBSCRIBE = "u"  # TODO

class DataTopic():
    """Shorthands for each of the supported topics.
    
    All DataTopics should be 2 characters to avoid overlap with PacketType.
     """

    RAW_DATA_TOPIC = "ra"
    FLEX_TOPIC     = "fl"
    PEAK_TO_PEAK_TOPIC = "pp"
    PEAK_AMP_TOPIC  = "pa"
    WINDOW_AVG_TOPIC = "wa"
    NOTCH_60_TOPIC = "60"
    NOTCH_50_TOPIC = "50"

DELIM = "|"  # Agreed upon protocol delimiter with daemon

def wrap(msg_type: str, msg: str) -> str:
    """Packages the messages in the way that the daemon expects."""

    return "{}{}{}".format(msg_type, DELIM, msg)

def unwrap(msg: str) -> Tuple[str, int, str]:
    """Extracts the data, pin and topic from the incoming message from the daemon."""

    unwrapped = msg.split(DELIM, maxsplit=2)
    if len(unwrapped) < 3:
        logging.warning("Invalid message")
        return ("", -1, "")
    try:
        pin = int(unwrapped[1])
    except ValueError:
        logging.error("Invalid pin value: {}".format(unwrapped[1]))
        pin = -1
    return (unwrapped[0], pin, unwrapped[2])