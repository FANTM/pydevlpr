import logging
import websockets
import pydevlpr
from pydevlpr.DevlprClient import DevlprClient
import pytest
import time
import sys, os
from .MockServer import MockServer

sys.path.insert(0, os.path.dirname((os.path.abspath(__file__))))

from pydevlpr.main import devlpr_client, stop, add_callback, remove_callback

def callback():
    logging.warning("Printed")

@pytest.fixture()
def server() -> MockServer:
    global devlpr_client
    server = MockServer()
    server.start()
    devlpr_client.CALLBACKS = {}
    devlpr_client.loop = server.loop
    yield server
    server.stop()

@pytest.mark.asyncio
async def test_subscribe(server: MockServer):
    uri = "ws://{}:{}".format(server.address[0], server.address[1])
    async with websockets.connect(uri) as ws:
        topic = "test"
        await devlpr_client.subscribe(topic, ws)
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
        assert devlpr_client.CALLBACKS[topic][pin][0] is callback  # Added to callback list
        assert MockServer.recv_buffer[0] == "s|{}".format(topic)  # Sent a subscribe

@pytest.mark.asyncio
async def test_removeCallback(server):
    global devlpr_client
    uri = "ws://{}:{}".format(server.address[0], server.address[1])
    async with websockets.connect(uri) as ws:
        topic = "test"
        pin = 0
        devlpr_client.CALLBACKS[topic] = dict()
        devlpr_client.CALLBACKS[topic][pin] = list()
        devlpr_client.CALLBACKS[topic][pin].append(callback)
        assert len(devlpr_client.CALLBACKS[topic][pin]) == 1
        assert devlpr_client.CALLBACKS[topic][pin][0] == callback
        print(devlpr_client.CALLBACKS[topic][pin])
        remove_callback(topic, pin, callback)
        print(devlpr_client.CALLBACKS[topic][pin])
        assert len(devlpr_client.CALLBACKS[topic][pin]) == 0
        

@pytest.mark.asyncio
async def test_stop(server):
    global devlpr_client
    uri = "ws://{}:{}".format(server.address[0], server.address[1])
    devlpr_client.start(uri)
    logging.info("Run for 2 seconds")
    time.sleep(2)
    logging.info("Shutdown")
    stop()
    assert devlpr_client.connection is None
    assert not devlpr_client.t.is_alive()
    