#!/usr/bin/env python

import asyncio
import logging
import threading

from pydevlpr.DevlprClient import DevlprClient
from .typing import Callback, CallbackList
import websockets
from websockets import server

devlpr_client: DevlprClient = DevlprClient()

def check_can_add_callback(callbacks: dict[str, dict[int, CallbackList]], topic: str, pin: int) -> dict[str, dict[int, CallbackList]]:
    if topic not in callbacks:
        callbacks[topic] = dict()
    if pin not in callbacks[topic]:
        callbacks[topic][pin] = list()
    return callbacks

## API ##

def stop() -> None:
    """Disconnects from the backend and end all communication"""

    if devlpr_client.t is not None and devlpr_client.t.is_alive:
        if devlpr_client.connection is not None and devlpr_client.loop is not None:
            res = asyncio.run_coroutine_threadsafe(devlpr_client.connection.close(), loop=devlpr_client.loop)
            try:
                res.result(2)  # Timeout after 2 seconds if it really can't close
            except asyncio.TimeoutError:
                logging.error("Failed to close connection gracefully")
        devlpr_client.t.join()
        devlpr_client.connection = None
        
def add_callback(topic: str, pin: int, fn: Callback, ws = None) -> None:
    """Adds a callback for a data stream from a topic and pin, also connects to the backend if it is currently disconnected."""

    devlpr_client.start_if_needed()
    devlpr_client.CALLBACKS = check_can_add_callback(devlpr_client.CALLBACKS, topic, pin)
    if len(devlpr_client.CALLBACKS[topic][pin]) == 0:
        with devlpr_client.CONNECTION_SYNC:
            if ws is not None:
                socket = ws
            else:
                socket = devlpr_client.connection
            if socket is None or socket.closed:
                raise ConnectionError
            if devlpr_client.loop is not None:
                asyncio.run_coroutine_threadsafe(devlpr_client.subscribe(topic, socket), loop=devlpr_client.loop)
    devlpr_client.CALLBACKS[topic][pin].append(fn)

def remove_callback(topic: str, pin: int, fn: Callback) -> None:
    """Removes the first instance of a function from the callback list for a topic and pin."""

    if topic not in devlpr_client.CALLBACKS:
        return
    if pin not in devlpr_client.CALLBACKS[topic]:
        return

    # TODO Unsubscribe logic for an efficiency boost.
    devlpr_client.CALLBACKS[topic][pin].remove(fn)
    