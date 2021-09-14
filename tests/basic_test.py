import logging
import pydevlpr_protocol
from pydevlpr.DevlprClient import DevlprClient
from pydevlpr_protocol import wrap_packet, PacketType, DataTopic
import pytest
import sys, os

from pydevlpr.DevlprServer import DevlprServer
from .MockServer import MockServer

sys.path.insert(0, os.path.dirname((os.path.abspath(__file__))))

from pydevlpr.main import devlpr_client, stop, add_callback, remove_callback

def callback():
    logging.warning("Printed")

@pytest.fixture()
def client() -> DevlprClient:
    client = DevlprClient()
    client.start_if_needed()
    yield client
    client.stop()

@pytest.fixture()
def server() -> DevlprServer:
    server = DevlprServer()
    server.start_if_needed()
    yield server
    server.stop()

def test_addCallback(server, client):
    topic = pydevlpr_protocol.DataTopic.RAW_DATA_TOPIC
    pin = 0
    client.add_callback(topic, pin, callback)
    logging.warning(client.CALLBACKS)
    assert client.CALLBACKS[topic][pin][0] is callback  # Added to callback list

def test_removeCallback(server, client):
    topic = DataTopic.RAW_DATA_TOPIC
    pin = 0
    client.CALLBACKS[topic] = dict()
    client.CALLBACKS[topic][pin] = list()
    client.CALLBACKS[topic][pin].append(callback)
    assert len(client.CALLBACKS[topic][pin]) == 1
    assert client.CALLBACKS[topic][pin][0] == callback
    print(client.CALLBACKS[topic][pin])
    client.remove_callback(topic, pin, callback)
    print(client.CALLBACKS[topic][pin])
    assert len(client.CALLBACKS[topic][pin]) == 0

def test_stop(server, client):
    client.stop()
    assert client.connection is None

    