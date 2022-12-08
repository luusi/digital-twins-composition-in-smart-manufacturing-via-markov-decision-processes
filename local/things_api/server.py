import asyncio
import json
import logging
import signal
from asyncio import AbstractEventLoop
from functools import singledispatchmethod
from threading import Thread
from typing import Dict, Optional

import websockets
from websocket import WebSocket
from websockets.exceptions import ConnectionClosedOK

from local.things_api.data import ServiceInstance
from local.things_api.helpers import ServiceId
from local.things_api.messages import from_json, Message, Register


logging.basicConfig(level=logging.INFO)


class ServiceRegistry:

    def __init__(self):
        self.services: Dict[ServiceId, ServiceInstance] = {}
        self.sockets_by_id: Dict[ServiceId, WebSocket] = {}
        self.id_by_sockets: Dict[WebSocket, ServiceId] = {}

    def has_service(self, service_id: ServiceId) -> bool:
        return service_id in self.services

    def get_services(self):
        return [service.json for service in self.services.values()]

    def get_service(self, service_id: ServiceId) -> ServiceInstance:
        return self.services.get(service_id, None)

    def add_service(self, service_instance: ServiceInstance, socket: WebSocket):
        if service_instance.service_id in self.services:
            raise ValueError(f"already registered a service with id {service_instance.service_id}")
        self.services[service_instance.service_id] = service_instance
        self.sockets_by_id[service_instance.service_id] = socket
        self.id_by_sockets[socket] = service_instance.service_id

    def remove_service(self, service_id: ServiceId):
        self.services.pop(service_id)
        socket = self.sockets_by_id.pop(service_id)
        self.id_by_sockets.pop(socket)

    def update_service(self, service_id: ServiceId, service_instance: ServiceInstance) -> None:
        assert self.has_service(service_id)
        self.services[service_id] = service_instance


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
            while True:
                raw_message = await websocket.recv()
                message_json = json.loads(raw_message)
                message = from_json(message_json, websocket)
                await self._handle(message, websocket)
        except ConnectionClosedOK:
            service_id = self.registry.id_by_sockets[websocket]
            logging.info(f"Service {service_id} disconnected, removing it...")
            self.registry.remove_service(service_id)
        except Exception:
            raise

    @singledispatchmethod
    async def _handle(self, message: Message, websocket: WebSocket) -> None:
        """Handle the message."""

    @_handle.register
    async def _handle_register(self, register: Register, websocket: WebSocket) -> None:
        """Handle the register message."""
        self.registry.add_service(register.service_instance, websocket)
        logging.info(f"Registered service {register.service_instance.service_id}")

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

    async def get_health(self):
        return "Healthy"

    async def get_services(self):
        return self.registry.get_services(), 200

    def get_service(self, service_id: str):
        logging.info(f"Called 'get_service' with ID: {service_id}")
        service_id = ServiceId(service_id)
        result = self.registry.get_service(service_id)
        if result is None:
            return f'Service with id {service_id} not found', 404
        return result.json, 200


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
