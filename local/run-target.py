#!/usr/bin/env python3
import asyncio
import json
from asyncio import CancelledError
from functools import singledispatchmethod
from pathlib import Path

import click
import websockets
from websocket import WebSocket
from websockets.exceptions import ConnectionClosedOK

from digital_twins.target_simulator import TargetSimulator
from local.things_api.client_wrapper import WebSocketWrapper
from local.things_api.data import TargetInstance
from local.things_api.helpers import setup_logger
from local.things_api.messages import RegisterTarget, Message, RequestTargetAction, \
    ResponseTargetAction


class TargetDevice:

    def __init__(self, target_instance: TargetInstance, host: str = "localhost", port: int = 8765):
        self.target_instance = target_instance
        self._simulator = TargetSimulator(self.target_instance.target_spec)

        self.logger = setup_logger(self.target_instance.target_id)
        self.host = host
        self.port = port

    @classmethod
    def from_spec(cls, spec_path: Path, **kwargs) -> "TargetDevice":
        data = json.loads(spec_path.read_text())
        target_instance = TargetInstance.from_json(data)
        return TargetDevice(target_instance, **kwargs)

    async def async_main(self):
        self.logger.info(f"Starting target '{self.target_instance.target_id}'...")
        async with websockets.connect(f"ws://{self.host}:{self.port}") as websocket:
            # register
            self.logger.info("Registering to server...")
            message = RegisterTarget(self.target_instance)
            await WebSocketWrapper.send_message(websocket, message)
            while True:
                try:
                    self.logger.info("Waiting for messages from the server...")
                    message = await WebSocketWrapper.recv_message(websocket)
                    self.logger.info("Received message from server, handling it...")
                    await self._handle(message, websocket)
                except (KeyboardInterrupt, ConnectionClosedOK, CancelledError):
                    self.logger.info("Close connection")
                    await websocket.close()
                    break

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
@click.option("--host", type=str, default="localhost")
@click.option("--port", type=int, default=8765)
def main(spec, host, port):
    """Start target."""
    target_device = TargetDevice.from_spec(Path(spec), host=host, port=port)
    loop = asyncio.get_event_loop()
    task = loop.create_task(target_device.async_main())
    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.cancel()
        loop.run_until_complete(task)
    finally:
        loop.close()


if __name__ == '__main__':
    main()
