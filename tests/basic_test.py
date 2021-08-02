import logging
import websockets
import pydevlpr
import pytest
import time
import sys, os
from .MockServer import MockServer

sys.path.insert(0, os.path.dirname((os.path.abspath(__file__))))

from pydevlpr.main import CALLBACKS, loop, subscribe, connect, start, start_if_needed, stop, add_callback, remove_callback

def callback():
    logging.warning("Printed")

@pytest.fixture()
def server() -> MockServer:
    global CALLBACKS, loop
    server = MockServer()
    server.start()
    CALLBACKS = dict()
    loop = server.loop
    yield server
    server.stop()

@pytest.mark.asyncio
async def test_subscribe(server: MockServer):
    uri = "ws://{}:{}".format(server.address[0], server.address[1])
    async with websockets.connect(uri) as ws:
        topic = "test"
        await subscribe(topic, ws)
        echo = await ws.recv()
        assert echo == "s|{}".format(topic)

# @pytest.mark.asyncio
# async def test_connect(server: MockServer):
#     uri = "ws://{}:{}".format(server.address[0], server.address[1]) 

@pytest.mark.asyncio
async def test_addCallback(server):
    uri = "ws://{}:{}".format(server.address[0], server.address[1])
    async with websockets.connect(uri) as ws:
        topic = "test"
        pin = 0
        add_callback(topic, pin, callback, ws)
        assert CALLBACKS[topic][pin][0] is callback  # Added to callback list
        assert MockServer.recv_buffer[0] == "s|{}".format(topic)  # Sent a subscribe

@pytest.mark.asyncio
async def test_removeCallback(server):
    uri = "ws://{}:{}".format(server.address[0], server.address[1])
    async with websockets.connect(uri) as ws:
        topic = "test"
        pin = 0
        CALLBACKS[topic] = dict()
        CALLBACKS[topic][pin] = list()
        CALLBACKS[topic][pin].append(callback)
        assert len(CALLBACKS[topic][pin]) == 1
        assert CALLBACKS[topic][pin][0] == callback
        remove_callback(topic, pin, callback)
        assert len(CALLBACKS[topic][pin]) == 0
        

@pytest.mark.asyncio
async def test_stop(server):
    pass