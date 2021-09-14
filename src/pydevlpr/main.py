#!/usr/bin/env python

from pydevlpr.DevlprClient import DevlprClient
from .typing import Callback

devlpr_client: DevlprClient = DevlprClient()

## API ##

def stop() -> None:
    """Disconnects from the backend and end all communication"""

    devlpr_client.stop()

def add_callback(topic: str, pin: int, fn: Callback, ws = None) -> None:
    """Adds a callback for a data stream from a topic and pin, also connects to the backend if it is currently disconnected."""

    devlpr_client.start_if_needed()
    devlpr_client.add_callback(topic, pin, fn, ws)

def remove_callback(topic: str, pin: int, fn: Callback) -> None:
    """Removes the first instance of a function from the callback list for a topic and pin."""

    devlpr_client.remove_callback(topic, pin, fn)