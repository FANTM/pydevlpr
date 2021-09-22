# pydevlpr

## Overview

Enables simple muscle to application connections. 
Pydevlpr is the front-end for `devlprd <https://github.com/FANTM/devlprd>`_, and the third piece of the muscle-to-app pipeline.

## Getting Started

After installing pydevlpr, integrating it into a project is straightforward.
First launch the `devlprd daemon <https://github.com/FANTM/devlprd>`_, and then use the ``add_callback(...)`` function to attach a handler to the incoming data.
The callback you attach will get the incoming payload as its only parameter, and then the data is yours to handle.

## Supported Topics

This list will expand as the package matures, but when adding/removing callbacks use a data topic from this list as it maps directly to the daemon.

* DataTopic.RAW_DATA_TOPIC - Data straight off the DEVLPR Arduino Shield. Range: 0-1023.
* DataTopic.FLEX_TOPIC - 1 when there has been a flex, 0 when muscle is relaxed.

## API

*def stop() -> None:*

> Stops listening to the server.

*def add_callback(topic: str, pin: int, fn: Callable[[str], None], ws: websocket.server.WebSocketServerProtocol = None) -> None:*

> Attaches a function to be called whenever a message is received at a particular topic and relating to a particular DEVLPR (as specified by the *pin* parameter).

> - topic: str - Specifies the data stream, differentiating filtered vs. raw data.
- pin: int - Connects the callback to a physical board. Each DEVLPR is connection to the Arduino via an analog pin, and the message from the daemon relates which pin this is.
- fn: Callable[[str], None] - Function to be called when a message is received that is both the specified topic and pin. It expects to receive the payload of the incoming message.
- ws: websocket.server.WebSocketServerProtocol - Websocket connection, by default set to None and uses pydevlprs global connection.
Pass a connection in if it is going to be used in another context, or for testing.

*def remove_callback(topic: str, pin: int, fn: Callable[[str], None]) -> None:*

> Stops a function from being called whenever a new qualified packet is received.

> - topic: str - The data stream the existing callback is attached to.
- pin: int - The DEVLPR the callback is attached to.
- fn: Callable[[str], None] - Function to remove from the callback list.

