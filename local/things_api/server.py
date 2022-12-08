import asyncio
import json
import logging
import signal
from asyncio import AbstractEventLoop, CancelledError
from functools import singledispatchmethod
from threading import Thread
from typing import Dict, Optional, List, cast

import websockets
from websocket import WebSocket
from websockets.exceptions import ConnectionClosedOK

from local.things_api.client_wrapper import WebSocketWrapper
from local.things_api.data import ServiceInstance, target_to_json, TargetInstance
from local.things_api.helpers import ServiceId, TargetId, setup_logger
from local.things_api.messages import from_json, Message, Register, Update, RegisterTarget, RequestTargetAction, \
    ResponseTargetAction, ExecuteServiceAction, ExecutionResult, DoMaintenance
from stochastic_service_composition.target import Target


logger = setup_logger(name="server")


class ServiceRegistry:

    def __init__(self):
        self.services: Dict[ServiceId, ServiceInstance] = {}
        self.sockets_by_service_id: Dict[ServiceId, WebSocket] = {}
        self.service_id_by_sockets: Dict[WebSocket, ServiceId] = {}

        self.targets: Dict[TargetId, TargetInstance] = {}
        self.sockets_by_target_id: Dict[TargetId, WebSocket] = {}
        self.target_id_by_sockets: Dict[WebSocket, TargetId] = {}

    def has_service(self, service_id: ServiceId) -> bool:
        return service_id in self.services

    def has_target(self, target_id: TargetId) -> bool:
        return target_id in self.targets

    def get_services(self) -> List[ServiceInstance]:
        return list(self.services.values())

    def get_service(self, service_id: ServiceId) -> Optional[ServiceInstance]:
        return self.services.get(service_id, None)

    def get_targets(self) -> List[TargetInstance]:
        return list(self.targets.values())

    def get_target(self, target_id: TargetId) -> Optional[Target]:
        return self.targets.get(target_id, None)

    def add_service(self, service_instance: ServiceInstance, socket: WebSocket):
        if service_instance.service_id in self.services:
            raise ValueError(f"already registered a service with id {service_instance.service_id}")
        self.services[service_instance.service_id] = service_instance
        self.sockets_by_service_id[service_instance.service_id] = socket
        self.service_id_by_sockets[socket] = service_instance.service_id

    def remove_service(self, service_id: ServiceId):
        self.services.pop(service_id)
        socket = self.sockets_by_service_id.pop(service_id)
        self.service_id_by_sockets.pop(socket)

    def update_service(self, service_id: ServiceId, service_instance: ServiceInstance) -> None:
        assert self.has_service(service_id)
        self.services[service_id] = service_instance

    def add_target(self, target_instance: TargetInstance, socket: WebSocket):
        if target_instance.target_id in self.targets:
            raise ValueError(f"already registered a targert service with id {target_instance.target_id}")
        self.targets[target_instance.target_id] = target_instance
        self.sockets_by_target_id[target_instance.target_id] = socket
        self.target_id_by_sockets[socket] = target_instance.target_id

    def update_target(self, target_id: TargetId, target_instance: TargetInstance) -> None:
        assert self.has_target(target_id)
        self.targets[target_id] = target_instance

    def remove_target(self, target_id: TargetId):
        self.targets.pop(target_id)
        socket = self.sockets_by_target_id.pop(target_id)
        self.target_id_by_sockets.pop(socket)


class WebsocketServer:

    def __init__(self, _registry: ServiceRegistry, port: int, loop: Optional[AbstractEventLoop] = None) -> None:
        """Initialize the websocket server."""
        self.registry = _registry
        self.port = port
        self.loop = loop

        self._loop: Optional[AbstractEventLoop] = None
        self._thread = Thread(target=self.serve_sync)
        self._server_task: Optional[asyncio.Task] = None

        self._websockets = []

    def serve_sync(self):
        """Wrapper to the 'serve' async method."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._server_task = self._loop.create_task(self.serve())
        try:
            self._loop.run_until_complete(self._server_task)
        except asyncio.CancelledError:
            pass

    async def serve(self):
        async with websockets.serve(self.request_handler, "localhost", self.port):
            await asyncio.Future()  # run forever

    async def request_handler(self, websocket):
        try:
            # handle registration
            raw_message = await websocket.recv()
            message_json = json.loads(raw_message)
            message = from_json(message_json)
            assert isinstance(message, (Register, RegisterTarget))
            await self._handle(message, websocket)
            # don't close connection - communcation is handled elsewhere
            while True:
                await asyncio.Future()
        except ConnectionClosedOK:
            logger.info(f"Closed connection with {websocket.remote_address}")
        except CancelledError:
            logger.info(f"Tearing down server")
        except Exception as e:
            logger.error(f"an error occurred: {e}")
        finally:
            await self._unsubscribe(websocket)

    async def _unsubscribe(self, websocket: WebSocket):
        if websocket in self.registry.service_id_by_sockets:
            # service registered, removing it
            service_id = self.registry.service_id_by_sockets[websocket]
            logger.info(f"Service {service_id} disconnected, removing it...")
            self.registry.remove_service(service_id)
        if websocket in self.registry.target_id_by_sockets:
            # target registered, removing it
            target_id = self.registry.target_id_by_sockets[websocket]
            logger.info(f"Service {target_id} disconnected, removing it...")
            self.registry.remove_target(target_id)

    @singledispatchmethod
    async def _handle(self, message: Message, websocket: WebSocket) -> None:
        """Handle the message."""

    @_handle.register
    async def _handle_register(self, register: Register, websocket: WebSocket) -> None:
        """Handle the register message."""
        self.registry.add_service(register.service_instance, websocket)
        logger.info(f"Registered service {register.service_instance.service_id}")

    @_handle.register
    async def _handle_update(self, update: Update, websocket: WebSocket) -> None:
        """Handle the update message."""
        try:
            self.registry.update_service(update.service_instance.service_id, update.service_instance)
            logger.info(f"Updated service {update.service_instance.service_id}")
        except Exception as e:
            logger.error(f"An error occurred while updating the service: {e}")
            await websocket.close()

    @_handle.register
    async def _handle_register_target(self, register_target: RegisterTarget, websocket: WebSocket) -> None:
        """Handle the register target message."""
        self.registry.add_target(register_target.target_instance, websocket)
        logger.info(f"Registered target service {register_target.target_instance.target_id}")

    def start(self):
        self._thread.start()

    def stop(self):
        self._loop.call_soon_threadsafe(self._server_task.cancel)
        self._thread.join()


class Api:

    SERVICES: Dict[ServiceId, ServiceInstance] = {}

    def __init__(self, websocket_server: WebsocketServer):
        self.websocket_server = websocket_server

    @property
    def registry(self) -> ServiceRegistry:
        return self.websocket_server.registry

    def _log_call(self, func_name, kwargs: Optional[Dict] = None):
        kwargs = kwargs if kwargs is not None else {}
        logger.info(f"Called '{func_name}' with args: {kwargs}")

    async def get_health(self):
        self._log_call(self.get_health.__name__)
        return "Healthy"

    async def get_services(self):
        self._log_call(self.get_services.__name__)
        return [service.json for service in self.registry.get_services()], 200

    async def get_service(self, service_id: str):
        self._log_call(self.get_service.__name__, dict(service_id=service_id))
        service_id = ServiceId(service_id)
        result = self.registry.get_service(service_id)
        if result is None:
            return f'Service with id {service_id} not found', 404
        return result.json, 200

    async def get_targets(self):
        self._log_call(self.get_targets.__name__)
        return [target.json for target in self.registry.get_targets()], 200

    async def get_target(self, target_id: str):
        self._log_call(self.get_target.__name__, dict(target_id=target_id))
        target_id = TargetId(target_id)
        result = self.registry.get_target(target_id)
        if result is None:
            return f'Target service with id {target_id} not found', 404
        return target_to_json(target_id, result), 200

    async def get_target_request(self, target_id: str):
        self._log_call(self.get_target_request.__name__, dict(target_id=target_id))
        target_id = TargetId(target_id)
        result = self.registry.get_target(target_id)
        if result is None:
            return f'Target service with id {target_id} not found', 404
        websocket = self.registry.sockets_by_target_id[target_id]
        request = RequestTargetAction()
        await WebSocketWrapper.send_message(websocket, request)

        # waiting reply from target
        response = await WebSocketWrapper.recv_message(websocket)
        assert response.TYPE == ResponseTargetAction.TYPE

        return cast(ResponseTargetAction, response).action

    async def execute_service_action(self, service_id: str, body: str):
        self._log_call(self.execute_service_action.__name__, dict(service_id=service_id, body=body))
        action_name = body
        service_id = ServiceId(service_id)
        service = self.registry.get_service(service_id)
        if service is None:
            return f'Service with id {service_id} not found', 404
        websocket = self.registry.sockets_by_service_id[service_id]
        request = ExecuteServiceAction(action_name)
        await WebSocketWrapper.send_message(websocket, request)

        # waiting reply from service
        response = await WebSocketWrapper.recv_message(websocket)
        assert response.TYPE == ExecutionResult.TYPE

        execution_result = cast(ExecutionResult, response)
        service.current_state = execution_result.new_state
        service.transition_function = execution_result.transition_function
        return "", 200

    async def do_maintenance(self):
        self._log_call(self.do_maintenance.__name__)
        for service_id, service in self.registry.services.items():
            logger.info(f"sending maintenance request to service '{service_id}'")
            message = DoMaintenance()
            websocket = self.registry.sockets_by_service_id[service_id]
            await WebSocketWrapper.send_message(websocket, message)
            logger.info(f"resetting transition function for '{service_id}'")
            service.transition_function = service.service_spec.transition_function


class Server:

    SERVICES: Dict[ServiceId, ServiceInstance] = {}

    def __init__(self, http_port: int = 8080, websocket_port: int = 8765, loop: Optional[AbstractEventLoop] = None):
        """Initialize the API service."""
        self._http_port = http_port
        self._websocket_port = websocket_port
        self._loop = loop

        self._registry = ServiceRegistry()
        self._server = WebsocketServer(self._registry, websocket_port, loop=loop)
        self._api = Api(self._server)

        self._original_sigint_handler = signal.getsignal(signal.SIGINT)

    def _sigint_handler(self, signal_, frame):
        self._server.stop()
        self._original_sigint_handler(signal_, frame)

    def _overwrite_sigint_handler(self):
        signal.signal(signal.SIGINT, self._sigint_handler)

    @property
    def api(self) -> Api:
        return self._api

    def run(self, port: int = 8080) -> None:
        from local.things_api.app import app
        self._overwrite_sigint_handler()
        task = self._loop.create_task(self._server.serve())
        app.run(port=port, debug=True, loop=self._loop)


server = Server(loop=asyncio.get_event_loop())
