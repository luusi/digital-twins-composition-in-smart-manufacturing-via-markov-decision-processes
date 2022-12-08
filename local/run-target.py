#!/usr/bin/env python3
import asyncio
import json
import logging
from functools import singledispatchmethod
from pathlib import Path

import click
import websockets
from websocket import WebSocket

from digital_twins.Devices.utils import target_from_json
from digital_twins.target_simulator import TargetSimulator
from local.things_api.client_wrapper import WebSocketWrapper
from local.things_api.data import ServiceType, TargetInstance
from local.things_api.helpers import TargetId
from local.things_api.messages import to_json, RegisterTarget, from_json, Message, RequestTargetAction, \
    ResponseTargetAction
from stochastic_service_composition.target import Target


def setup_logger():
    """Set up the logger."""
    logger = logging.getLogger("digital_twins")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


class TargetDevice:

    def __init__(self, target_instance: TargetInstance):
        self.target_instance = target_instance
        self._simulator = TargetSimulator(self.target_instance.target_spec)

        self.logger = setup_logger()

    @classmethod
    def from_spec(cls, spec_path: Path) -> "TargetDevice":
        logging.info(f"Loading service spec from {spec_path}...")
        data = json.loads(spec_path.read_text())
        target_instance = TargetInstance.from_json(data)
        return TargetDevice(target_instance)

    async def async_main(self):
        async with websockets.connect("ws://localhost:8765") as websocket:
            # register
            logging.info("Registering to server...")
            message = RegisterTarget(self.target_instance)
            json_message = to_json(message)
            await websocket.send(json.dumps(json_message))

            while True:
                logging.info("Waiting for messages from the server...")
                message = await WebSocketWrapper.recv_message(websocket)
                await self._handle(message, websocket)

    @singledispatchmethod
    async def _handle(self, message: Message, websocket: WebSocket):
        self.logger.error(f"cannot handle messages of type {message.TYPE}")

    @_handle.register
    async def _handle_request_target_action(self, message: RequestTargetAction, websocket: WebSocket):
        self.logger.info("Sampling next action!")
        self.logger.info(f"Current state before executing command: {self._simulator.current_state}")
        action = self._simulator.sample_action()
        self.logger.info(f"Sampled action: {action}")
        self._simulator.update_state(action)
        self.logger.info(f"Current state after executing command: {self._simulator.current_state}")
        self.logger.info(f"Sending action {action} to orchestrator")
        response = ResponseTargetAction(action)
        await WebSocketWrapper.send_message(websocket, response)


@click.command()
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
def main(spec):
    """Start target."""
    target_device = TargetDevice.from_spec(Path(spec))
    asyncio.run(target_device.async_main())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
