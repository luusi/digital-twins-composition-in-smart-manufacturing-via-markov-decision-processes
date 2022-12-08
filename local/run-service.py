#!/usr/bin/env python3
import asyncio
import json
import logging
from pathlib import Path

import click
import websockets

from local.things_api.data import ServiceInstance
from local.things_api.messages import Register, to_json, Update


async def async_main(spec: Path):
    logging.info(f"Loading service spec from {spec}...")
    data = json.loads(spec.read_text())

    async with websockets.connect("ws://localhost:8765") as websocket:
        # register
        logging.info("Registering to server...")
        message = Register(ServiceInstance.from_json(data))
        json_message = to_json(message)
        await websocket.send(json.dumps(json_message))

        while True:
            logging.info("Waiting for messages from the server...")
            print(await websocket.recv())


@click.command()
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
def main(spec):
    """Start service."""
    asyncio.run(async_main(Path(spec)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
