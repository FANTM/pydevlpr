#!/usr/bin/env python

import asyncio
import collections
import logging
import threading
from typing import Callable, List

import websockets
from websockets import server

from .protocol import *
CallbackList_t = List[Callable[[str], None]]

BUF_SIZE = 64
TOPICS  = set()
KILL_SYNC = threading.Lock()
TELEM_SYNC = threading.Lock()
CONNECTION_SYNC = threading.Lock()
CONN_INFO = ("localhost", 8765)
TELEMETRY: dict[str, collections.deque] = dict()
CALLBACKS: dict[str, CallbackList_t] = dict()
connection: server.WebSocketServerProtocol = None
loop: asyncio.AbstractEventLoop = None
t: threading.Thread = threading.Thread(target=None)
kill: bool = False

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
                    if topic in CALLBACKS:
                        for callback in CALLBACKS[topic]:
                            callback(data)
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
            logging.error("Failed to close connection gracefully")
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
        logging.error("Not connected, nothing to watch")
        return
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

def reduce_to_flag(topic: str) -> bool:
    if topic not in TELEMETRY:
        logging.error("Not watching topic")
        return False
    with TELEM_SYNC:
        ret = TELEMETRY[topic].count("True")
        TELEMETRY[topic].clear()
    return ret > 0

def reduce_to_float(topic: str) -> float:
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

def add_callback(fn: Callable[[str], None], topic: str):
    if topic not in CALLBACKS:
        CALLBACKS[topic] = list()
    CALLBACKS[topic].append(fn)
