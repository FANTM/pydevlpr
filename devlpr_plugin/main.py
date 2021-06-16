#!/usr/bin/env python

import asyncio
import logging
from typing import Tuple
import websockets
from websockets import server
import threading
import collections
from enum import Enum

BUF_SIZE = 64

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

TOPICS  = set()
KILL_SYNC = threading.Lock()
TELEM_SYNC = threading.Lock()
CONNECTION_SYNC = threading.Lock()
CONN_INFO = ("localhost", 8765)
TELEMETRY: dict[str, collections.deque] = dict()
connection: server.WebSocketServerProtocol = None
loop: asyncio.AbstractEventLoop = None
t: threading.Thread = threading.Thread(target=None)
kill: bool = False

def wrap(msg_type: PacketType, msg: str) -> str:
    return "{}{}{}".format(str(msg_type), PROTOCOL, msg)

def unwrap(msg: str) -> Tuple[str, str]:
    unwrapped = msg.split(PROTOCOL, maxsplit=1)
    if len(unwrapped) < 2:
        print("[Warn] Invalid message")
        return ("", "")
    return (unwrapped[0], unwrapped[1])

async def subscribe(topic: str):
    await connection.send(wrap(PacketType.SUBSCRIBE, topic))

async def connect(uri: str):
    global connection, loop
    loop = asyncio.get_event_loop()
    try:
        async with websockets.connect(uri) as websocket:
            connection = websocket
            CONNECTION_SYNC.release()
            async for message in websocket:
                with KILL_SYNC:
                    if kill:
                        break
                with TELEM_SYNC:
                    topic, data = unwrap(message)
                    TELEMETRY[topic].append(data)
    finally:
        if CONNECTION_SYNC.locked():
            CONNECTION_SYNC.release()
        if KILL_SYNC.locked():
            KILL_SYNC.release()
        if TELEM_SYNC.locked():
            TELEM_SYNC.release()

def _start():
    uri = "ws://{}:{}".format(CONN_INFO[0], CONN_INFO[1])
    asyncio.run(connect(uri))

## API ##

# start(None)
# Called first. It initializes a connection to the DEVLPR backend. Must be called first if you want anything else to work
def start():
    global t
    t = threading.Thread(target=_start)
    CONNECTION_SYNC.acquire()
    t.start()

# stop(None)
# Called last. It will disconnect from the backend and end all communication
def stop():
    global kill, t, connection
    if t.is_alive:
        res = asyncio.run_coroutine_threadsafe(connection.close(), loop=loop)
        try:
            res.result(2)  # Timeout after 2 seconds if it really can't close
        except asyncio.TimeoutError:
            print("Failed to close connection gracefully")
        with KILL_SYNC:
            kill = True
        t.join()
        connection = None

# watch(topic:str)
# Start collecting data from a channel.
def watch(topic: str):
    with CONNECTION_SYNC:
        pass  # Makes sure we have actually connected
    if connection is None:
        print("[Err] Not conncted, nothing to watch")
    TELEM_SYNC.acquire()
    TELEMETRY[topic] = collections.deque(maxlen=BUF_SIZE)
    TELEM_SYNC.release()
    asyncio.run(subscribe(topic))
    TOPICS.add(topic)

def chomp(topic: str):
    if topic not in TELEMETRY:
        raise IndexError
    
    with TELEM_SYNC:
        if len(TELEMETRY[topic]) == 0:
            return None
    
        ret = TELEMETRY[topic].popleft()
    return ret

def reduceToFlag(topic: str) -> bool:
    if topic not in TELEMETRY:
        logging.error("Not watching topic")
        return False
    with TELEM_SYNC:
        ret = TELEMETRY[topic].count("True")
        TELEMETRY[topic].clear()
    return ret > 0

def reduceToFloat(topic: str) -> float:
    if topic not in TELEMETRY:
        logging.error("Not watching topic")
        return False
    ret = 0
    with TELEM_SYNC:
        telem_count = len(TELEMETRY)

        if telem_count == 0:
            return None

        while len(TELEMETRY[topic]) > 0:
            try:
                ret += float(TELEMETRY[topic].popleft())
            except ValueError:
                telem_count -= 1  # We don't want invalid values to count!
    if telem_count == 0:
        return 0.0
    else:
        return ret / telem_count