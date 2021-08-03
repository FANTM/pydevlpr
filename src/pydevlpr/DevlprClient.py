import asyncio
import threading
import logging
import websockets
from websockets import server

from .protocol import unwrap, wrap, PacketType
from .typing import CallbackList

class DevlprClient:
    ADDRESS = ("localhost", 8765)
    def __init__(self) -> None:
        self.CONNECTION_SYNC = threading.Lock()
        self.TELEM_SYNC      = threading.Lock()
        self.CALLBACKS: dict[str, dict[int, CallbackList]] = dict()
        self.loop: asyncio.AbstractEventLoop = None
        self.connection: server.WebSocketServerProtocol = None
        self.t: threading.Thread = None

    async def connect(self, uri: str) -> None:
        self.loop = asyncio.get_event_loop()
        try:
            async with websockets.connect(uri) as websocket:
                self.connection = websocket
                self.CONNECTION_SYNC.release()
                async for message in websocket:
                    with self.TELEM_SYNC:
                        topic, pin, data = unwrap(message)
                        if topic in self.CALLBACKS:
                            for callback in self.CALLBACKS[topic][pin]:
                                callback(data)
        except ConnectionError:
            logging.error("Failed to connect")
        finally:
            if self.CONNECTION_SYNC.locked():
                self.CONNECTION_SYNC.release()
            if self.TELEM_SYNC.locked():
                self.TELEM_SYNC.release()

    def start(self, uri: str) -> None:
        """Initializes a connection to the DEVLPR backend. Must be called first if you want anything else to work"""

        self.t = threading.Thread(target=asyncio.run, args=[self.connect(uri)])
        self.CONNECTION_SYNC.acquire()
        self.t.start()

    def start_if_needed(self):
        """Tries to intelligently determine if we're already connected, and only connects if we're not"""

        if self.t is None or self.t.is_alive() == False:
            uri = "ws://{}:{}".format(DevlprClient.ADDRESS[0], DevlprClient.ADDRESS[1])
            self.start(uri)

    async def subscribe(self, topic: str, connection: server.WebSocketServerProtocol) -> None:
        await connection.send(wrap(PacketType.SUBSCRIBE, topic))