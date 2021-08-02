#!/usr/bin/env python

import asyncio
import logging
import threading
from typing import Callable, List

import websockets
from websockets import server

from .protocol import *

Callback_t = Callable[[str], None]
CallbackList_t = List[Callback_t]

KILL_SYNC = threading.Lock()
TELEM_SYNC = threading.Lock()
CONNECTION_SYNC = threading.Lock()
CONN_INFO = ("localhost", 8765)
CALLBACKS: dict[str, dict[int, CallbackList_t]] = dict()
connection: server.WebSocketServerProtocol = None
loop: asyncio.AbstractEventLoop = None
t: threading.Thread = threading.Thread(target=None)
kill: bool = False

def check_can_add_callback(callbacks: dict[str, dict[int, CallbackList_t]], topic: str, pin: int):
    if topic not in CALLBACKS:
        callbacks[topic] = dict()
    if pin not in CALLBACKS[topic]:
        callbacks[topic][pin] = list()
    return callbacks

async def subscribe(topic: str, connection: server.WebSocketServerProtocol) -> None:
    await connection.send(wrap(PacketType.SUBSCRIBE, topic))

async def connect(uri: str) -> None:
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
                    topic, pin, data = unwrap(message)
                    if topic in CALLBACKS:
                        for callback in CALLBACKS[topic][pin]:
                            callback(data)
    except ConnectionError:
        logging.error("Failed to connect")
    finally:
        if CONNECTION_SYNC.locked():
            CONNECTION_SYNC.release()
        if KILL_SYNC.locked():
            KILL_SYNC.release()
        if TELEM_SYNC.locked():
            TELEM_SYNC.release()

# start(None)
# Called first. It initializes a connection to the DEVLPR backend. Must be called first if you want anything else to work
def start():
    global t
    uri = "ws://{}:{}".format(CONN_INFO[0], CONN_INFO[1])
    t = threading.Thread(target=asyncio.run, args=[connect(uri)])
    CONNECTION_SYNC.acquire()
    t.start()

def start_if_needed():
    if t is None or t.is_alive() == False:
        start()

## API ##

# stop(None)
# Called last. It will disconnect from the backend and end all communication
def stop() -> None:
    """ It will disconnect from the backend and end all communication"""

    global kill, t, connection
    if t.is_alive:
        if connection is not None:
            res = asyncio.run_coroutine_threadsafe(connection.close(), loop=loop)
            try:
                res.result(2)  # Timeout after 2 seconds if it really can't close
            except asyncio.TimeoutError:
                logging.error("Failed to close connection gracefully")
        with KILL_SYNC:
            kill = True
        t.join()
        connection = None

def add_callback(topic: str, pin: int, fn: Callback_t, ws = None) -> None:
    global CALLBACKS
    if ws is not None:
        socket = ws
    else:
        socket = connection
    start_if_needed()
    CALLBACKS = check_can_add_callback(CALLBACKS, topic, pin)
    if len(CALLBACKS[topic][pin]) == 0:
        with CONNECTION_SYNC:
            if socket is None or socket.closed:
                raise ConnectionError
            asyncio.run_coroutine_threadsafe(subscribe(topic, socket), loop=loop)
    CALLBACKS[topic][pin].append(fn)

def remove_callback(topic: str, pin: int, fn: Callback_t) -> None:
    if topic not in CALLBACKS:
        return
    if pin not in CALLBACKS[topic]:
        return
    
    # TODO Unsubscribe logic for an efficiency boost.
    CALLBACKS[topic][pin].remove(fn)
    