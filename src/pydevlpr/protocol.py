import logging
import asyncio
from typing import Tuple

class DaemonSocket:

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.remote_address = writer.get_extra_info('peername')

    def get_remote_address(self):
        return self.remote_address

    def closed(self):
        return self.writer.is_closing()

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def send(self, msg):
        # make sure we're not closed before trying to write
        if self.closed():
            return
        msg += "\n"
        self.writer.write(msg.encode())
        await self.writer.drain()

    async def recv(self):
        # make sure we're not closed before trying to read
        if self.closed():
            return ''
        msg = await self.reader.readline()
        return msg.decode().strip()

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