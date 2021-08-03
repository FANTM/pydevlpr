import websockets as ws
import asyncio
import threading
import logging
from typing import List

class MockServer:
    recv_buffer: List[str] = list()
    
    def __init__(self):
        self.address = ('localhost', 8777)
        self.loop = asyncio.new_event_loop()
        self.server = None

    @staticmethod
    async def handler(websocket, path):
        async for message in websocket:
            MockServer.recv_buffer.append(message)
            await websocket.send(message)

    async def runner(self):
        serve = ws.serve(MockServer.handler, self.address[0], self.address[1])
        async with serve as s:
            self.server = s
            await s.wait_closed()

    def start(self):
        MockServer.stop_fut = asyncio.Future(loop=self.loop)
        self.thread = threading.Thread(target=self.loop.run_until_complete, args=[self.runner()])
        self.thread.start()
        while self.server is None:
            pass

    def stop(self):
        self.server.close()
        asyncio.run_coroutine_threadsafe(self.server.wait_closed(), loop=self.loop)