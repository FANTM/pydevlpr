#!/usr/bin/env python

import asyncio
import websockets
import threading
import collections

BUF_SIZE = 64
TOPICS = set()
KILL_SYNC = threading.Semaphore(1)
TELEM_SYNC = threading.Semaphore(1)

TELEMETRY: dict[str, collections.deque] = dict()
t: threading.Thread = threading.Thread(target=None)
kill: bool = False

async def connect(uri: str, topic: str):
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            KILL_SYNC.acquire()
            if kill:
                KILL_SYNC.release()
                break
            KILL_SYNC.release()
            TELEM_SYNC.acquire()
            TELEMETRY[topic].append(message)
            TELEM_SYNC.release()

async def __start():  
    await asyncio.gather(
        *[connect("ws://localhost:8765/{topic}".format(topic=topic), topic) for topic in TOPICS]
    )

def _start():
    asyncio.run(__start())

## API ##

def start():
    global t
    t = threading.Thread(target=_start)
    t.start()

def stop():
    global kill, t
    if t.is_alive:
        KILL_SYNC.acquire()
        kill = True
        KILL_SYNC.release()
        t.join()

def watch(topic: str):
    TELEM_SYNC.acquire()
    TELEMETRY[topic] = collections.deque(maxlen=BUF_SIZE)
    TELEM_SYNC.release()
    TOPICS.add(topic)

def chomp(topic: str):
    if topic not in TELEMETRY:
        raise IndexError
    
    TELEM_SYNC.acquire()
    if len(TELEMETRY[topic]) == 0:
        TELEM_SYNC.release()
        return None
    
    ret = TELEMETRY[topic].popleft()
    TELEM_SYNC.release()
    return ret

def reduceToFlag(topic: str, target: bool) -> bool:
    if topic not in TELEMETRY:
        raise IndexError
    TELEM_SYNC.acquire()
    ret = TELEMETRY[topic].count(str(target))
    TELEMETRY[topic].clear()
    TELEM_SYNC.release()
    return ret > 0

def reduceToFloat(topic: str) -> float:
    if topic not in TELEMETRY:
        raise IndexError
    ret = 0
    TELEM_SYNC.acquire()
    telem_count = len(TELEMETRY)

    if telem_count == 0:
        TELEM_SYNC.release()
        return None

    while len(TELEMETRY[topic]) > 0:
        ret += float(TELEMETRY[topic].popleft())
    
    TELEM_SYNC.release()
    return ret / telem_count