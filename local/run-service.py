#!/usr/bin/env python3
import asyncio
import json
import logging
import random
from functools import singledispatchmethod
from pathlib import Path

import click
import websockets
from websocket import WebSocket

from digital_twins.wrappers import initialize_wrapper
from local.things_api.client_wrapper import WebSocketWrapper
from local.things_api.data import ServiceInstance
from local.things_api.helpers import setup_logger
from local.things_api.messages import Register, Message, ExecuteServiceAction, ExecutionResult


class ServiceDevice:

    def __init__(self, service_instance: ServiceInstance):
        self.service_instance = service_instance
        self.wrapper = initialize_wrapper(self.service_instance.service_spec)

        self._current_state = self.service_instance.service_spec.initial_state
        self.logger = setup_logger(self.service_instance.service_id)

    @classmethod
    def from_spec(cls, spec_path: Path) -> "ServiceDevice":
        data = json.loads(spec_path.read_text())
        target_instance = ServiceInstance.from_json(data)
        return ServiceDevice(target_instance)

    async def async_main(self, spec: Path):
        self.logger.info(f"Loading service spec from {spec}...")
        data = json.loads(spec.read_text())

        async with websockets.connect("ws://localhost:8765") as websocket:
            # register
            self.logger.info("Registering to server...")
            register_message = Register(ServiceInstance.from_json(data))
            await WebSocketWrapper.send_message(websocket, register_message)
            while True:
                self.logger.info("Waiting for messages from the server...")
                message = await WebSocketWrapper.recv_message(websocket)
                await self._handle(message, websocket)

    @singledispatchmethod
    async def _handle(self, message: Message, websocket: WebSocket):
        self.logger.error(f"cannot handle messages of type {message.TYPE}")

    @_handle.register
    async def _handle_execute_service_action(self, message: ExecuteServiceAction, websocket: WebSocket):
        action = message.action
        starting_state = self._current_state
        transitions_from_current_state = self.wrapper.transition_function[starting_state]
        next_service_states, reward = transitions_from_current_state[action]
        states, probabilities = zip(*next_service_states.items())
        new_state = random.choices(states, probabilities)[0]
        self._current_state = new_state
        self.wrapper.update(starting_state, action)
        message = ExecutionResult(new_state, self.wrapper.transition_function)
        await WebSocketWrapper.send_message(websocket, message)


@click.command()
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
def main(spec):
    """Start service."""
    service_device = ServiceDevice.from_spec(Path(spec))
    asyncio.run(service_device.async_main(Path(spec)))


if __name__ == '__main__':
    main()
