#!/usr/bin/env python3
import asyncio
import json
import logging
from pathlib import Path

import click
import websockets

from digital_twins.Devices.utils import target_from_json
from local.things_api.data import ServiceType
from local.things_api.helpers import TargetId
from local.things_api.messages import to_json, RegisterTarget


async def async_main(spec: Path):
    logging.info(f"Loading service spec from {spec}...")
    data = json.loads(spec.read_text())
    target_id = TargetId(data["id"])
    assert data["attributes"]["type"] == ServiceType.TARGET.value
    target = target_from_json(data)

    async with websockets.connect("ws://localhost:8765") as websocket:
        # register
        logging.info("Registering to server...")
        message = RegisterTarget(target_id, target)
        json_message = to_json(message)
        await websocket.send(json.dumps(json_message))

        while True:
            logging.info("Waiting for messages from the server...")
            print(await websocket.recv())


@click.command()
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
def main(spec):
    """Start target."""
    asyncio.run(async_main(Path(spec)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
