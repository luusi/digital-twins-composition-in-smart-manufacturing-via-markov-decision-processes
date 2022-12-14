#!/usr/bin/env python3
import asyncio
import json
import random
from asyncio import CancelledError
from functools import singledispatchmethod
from pathlib import Path

import click
import websockets
from websocket import WebSocket
from websockets.exceptions import ConnectionClosedOK

from digital_twins.wrappers import initialize_wrapper
from local.things_api.client_wrapper import WebSocketWrapper
from local.things_api.data import ServiceInstance
from local.things_api.helpers import setup_logger
from local.things_api.messages import Register, Message, ExecuteServiceAction, ExecutionResult, DoMaintenance


class ServiceDevice:

    def __init__(self, service_instance: ServiceInstance, host: str = "localhost", port: int = 8765):
        self.service_instance = service_instance
        self.wrapper = initialize_wrapper(self.service_instance.service_spec)

        self._current_state = self.service_instance.service_spec.initial_state
        self.logger = setup_logger(self.service_instance.service_id)
        self.host = host
        self.port = port

    @classmethod
    def from_spec(cls, spec_path: Path, **kwargs) -> "ServiceDevice":
        data = json.loads(spec_path.read_text())
        target_instance = ServiceInstance.from_json(data)
        return ServiceDevice(target_instance)

    async def async_main(self):
        self.logger.info(f"Starting target '{self.service_instance.service_id}'...")
        async with websockets.connect(f"ws://{self.host}:{self.port}") as websocket:
            # register
            self.logger.info("Registering to server...")
            register_message = Register(self.service_instance)
            await WebSocketWrapper.send_message(websocket, register_message)
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
    async def _handle_execute_service_action(self, message: ExecuteServiceAction, websocket: WebSocket):
        self.logger.info(f"Processing message of type '{message.TYPE}'")
        action = message.action
        self.logger.info(f"received action '{message.action}'")
        starting_state = self._current_state
        transitions_from_current_state = self.wrapper.transition_function[starting_state]
        next_service_states, reward = transitions_from_current_state[action]
        states, probabilities = zip(*next_service_states.items())
        new_state = random.choices(states, probabilities)[0]
        self._current_state = new_state
        self.logger.info(f"Previous state='{starting_state}', current state={new_state}")
        self.wrapper.update(starting_state, action)
        message = ExecutionResult(new_state, self.wrapper.transition_function)
        self.logger.info(f"Updated transition function: {message.transition_function}")
        self.logger.info(f"Sending result to server")
        await WebSocketWrapper.send_message(websocket, message)

    @_handle.register
    async def _handle_maintenance(self, message: DoMaintenance, websocket: WebSocket):
        self.logger.info(f"Processing message of type '{message.TYPE}'")
        previous_transition_function = self.wrapper.transition_function
        self.wrapper.reset()
        current_transition_function = self.wrapper.transition_function
        self.logger.info(f"Repaired service: previous tf={previous_transition_function}, new tf={current_transition_function}")


@click.command()
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
@click.option("--host", type=str, default="localhost")
@click.option("--port", type=int, default=8765)
def main(spec, host, port):
    """Start service."""
    service_device = ServiceDevice.from_spec(Path(spec), host=host, port=port)
    loop = asyncio.get_event_loop()
    task = loop.create_task(service_device.async_main())
    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.cancel()
        loop.run_until_complete(task)
    finally:
        loop.close()


if __name__ == '__main__':
    main()
