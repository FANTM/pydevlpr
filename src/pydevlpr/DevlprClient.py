import asyncio
import threading
import queue
import logging
from typing import Optional
from pydevlpr_protocol import unwrap_packet, wrap_packet, PacketType, DaemonSocket
from .typing import Callback, CallbackList
from concurrent.futures import ThreadPoolExecutor

class DevlprClient:
    ADDRESS = ("localhost", 8765)

    def __init__(self) -> None:
        self.CALLBACK_LOCK      = threading.Lock()
        self.CALLBACKS: dict[str, dict[int, CallbackList]] = dict()
        self.connection_loop: Optional[asyncio.AbstractEventLoop] = None
        self.connection: Optional[DaemonSocket] = None
        self.connection_thread: Optional[threading.Thread] = None
        self.callback_thread: Optional[threading.Thread] = None
        self.callback_queue: Optional[queue.Queue] = None

    async def connect(self, host: str, port: int, connect_event: threading.Event) -> None:
        """Tries to connect to the daemon, and blocks the thread until either successful or it fails"""

        # grab the event loop we're listening/subscribing on for future use
        self.connection_loop = asyncio.get_event_loop()
        try:
            reader, writer = await asyncio.open_connection(host, port)
            self.connection = DaemonSocket(reader, writer)
            # we established our connection, so set that event
            connect_event.set()
            # spin on messages
            message = ' '
            while len(message) > 0:
                try:
                    message = await self.connection.recv()
                except:
                    # Note: probably need to handle specific issues
                    logging.error("Failed on DaemonSocket.recv()")
                    message = ''
                
                # Note: Sometimes we get a message that is just whitespace for some reason?
                message = message.strip()
                if len(message) == 0:
                    continue
                
                topic, pin, data = unwrap_packet(message)
                # before we go calling relevant callbacks, let's lock the list
                with self.CALLBACK_LOCK:
                    if topic in self.CALLBACKS and pin in self.CALLBACKS[topic]:
                        for callback in self.CALLBACKS[topic][pin]:
                            # don't call in this thread as we don't know how long it will take
                            self.callback_queue.put((callback,data))
        except ConnectionError:
            logging.error("Failed to connect")
        finally:
            if self.CALLBACK_LOCK.locked():
                self.CALLBACK_LOCK.release()

    async def subscribe(self, topic: str, connection: DaemonSocket) -> None:
        """Sends a message to the daemon telling it that something is listening to a topic."""
        if connection is None or connection.closed():
            raise ConnectionError
        await connection.send(wrap_packet(PacketType.SUBSCRIBE, topic))

    def start(self, connect_event: threading.Event) -> None:
        """Initializes a connection to the DEVLPR backend. Must be called first if you want anything else to work"""

        host = DevlprClient.ADDRESS[0]
        port = DevlprClient.ADDRESS[1]
        self.connection_thread = threading.Thread(target=asyncio.run, args=[self.connect(host, port, connect_event)])
        self.connection_thread.start()

    def start_if_needed(self) -> None:
        """Tries to intelligently determine if we're already connected, and only connects if we're not"""

        # start up a worker thread for handling callbacks
        if self.callback_thread is None or not self.callback_thread.is_alive():
            # create our Queue
            self.callback_queue = queue.Queue()
            self.callback_thread = threading.Thread(target=self.handle_calllbacks, daemon=True)
            self.callback_thread.start()

        # start up the connection to the daemon if need be
        if self.connection_thread is None or not self.connection_thread.is_alive():
            # and also need an event to allow us to wait on connection establishment
            connect_event = threading.Event()
            # start the client, opening a connection on another thread
            self.start(connect_event)
            # and wait for that connection event to go off
            connect_complete = connect_event.wait(timeout=10)
            if not connect_complete: # connect to deamon never completed
                raise ConnectionError
            

    def stop(self) -> None:
        # try to stop the connection thread
        if self.connection_thread is not None and self.connection_thread.is_alive:
            if self.connection is not None and self.connection_loop is not None:
                res = asyncio.run_coroutine_threadsafe(self.connection.close(), loop=self.connection_loop)
                try:
                    res.result(2)  # Timeout after 2 seconds if it really can't close
                except asyncio.TimeoutError:
                    logging.error("Failed to close connection gracefully")
            self.connection_thread.join()
            self.connection = None

    def ensure_can_add_callback(self, topic: str, pin: int) -> None:
        with self.CALLBACK_LOCK:
            if topic not in self.CALLBACKS:
                self.CALLBACKS[topic] = dict()
            if pin not in self.CALLBACKS[topic]:
                self.CALLBACKS[topic][pin] = list()

    def add_callback(self, topic: str, pin: int, fn: Callback, socket = None) -> None:
        # first make sure our callbacks dict is ready
        self.ensure_can_add_callback(topic, pin)
        # if we didn't get a specified socket, then use the one we should have
        if socket is None:
            socket = self.connection
        # assuming we have an event loop for our daemon connection, subscribe to the data topic
        if self.connection_loop is not None:
            asyncio.run_coroutine_threadsafe(self.subscribe(topic, socket), loop=self.connection_loop)
        # and add the actual callback to the callback list
        with self.CALLBACK_LOCK:
            self.CALLBACKS[topic][pin].append(fn)

    def remove_callback(self, topic: str, pin: int, fn: Callback) -> None:
        with self.CALLBACK_LOCK:
            if topic in self.CALLBACKS and pin in self.CALLBACKS[topic]:
                # TODO Unsubscribe logic for an efficiency boost.
                self.CALLBACKS[topic][pin].remove(fn)
    
    def handle_calllbacks(self) -> None:
        while True:
            # callbacks are enqueued as tuples of the callback and the data
            cback, data = self.callback_queue.get()
            cback(data)
            self.callback_queue.task_done()