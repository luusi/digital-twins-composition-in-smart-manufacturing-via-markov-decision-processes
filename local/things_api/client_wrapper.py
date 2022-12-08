"""Wrapper class to auto-generated OpenAPI client functions."""
import json
from typing import List

from websocket import WebSocket

from local.things_api.client import Client
from local.things_api.client.api.health.app_server_api_get_health import asyncio_detailed as get_health
from local.things_api.client.api.services.app_server_api_get_services import asyncio_detailed as get_services
from local.things_api.client.api.services.app_server_api_get_target_request import \
    asyncio_detailed as get_target_request
from local.things_api.client.api.services.app_server_api_get_targets import asyncio_detailed as get_targets
from local.things_api.client.api.services.app_server_api_execute_service_action import asyncio_detailed as execute_service_action
from local.things_api.client.api.services.app_server_api_get_service import asyncio_detailed as get_service
from local.things_api.client.api.services.app_server_api_do_maintenance import asyncio_detailed as do_maintenance
from local.things_api.client.models import Service
from local.things_api.data import ServiceInstance, TargetInstance
from local.things_api.helpers import TargetId, ServiceId
from local.things_api.messages import Message, from_json, to_json

TIMEOUT = 60.0


class ClientWrapper:

    def __init__(self, host: str, port: int, timeout: float = TIMEOUT) -> None:
        """Initialize the client wrapper"""
        self._host = host
        self._port = port
        self._timeout = timeout

        self._client = Client(self.base_url, timeout=timeout, verify_ssl=False)

    @property
    def base_url(self) -> str:
        """Initialize the base URL."""
        return f"http://{self._host}:{self._port}"

    async def get_health(self):
        """Get the /health of the service."""
        response = await get_health(client=self._client)
        return response

    async def get_services(self) -> List[ServiceInstance]:
        """Get all the services."""
        response = await get_services(client=self._client)
        result: List[Service] = response.parsed
        to_our_model = [ServiceInstance.from_json(service.to_dict()) for service in result]
        return to_our_model

    async def get_service(self, service_id: ServiceId) -> ServiceInstance:
        """Get all the services."""
        response = await get_service(service_id, client=self._client)
        return ServiceInstance.from_json(response.parsed.to_dict())

    async def get_targets(self) -> List[TargetInstance]:
        """Get all the services."""
        response = await get_targets(client=self._client)
        result = json.loads(response.content)
        to_our_model = [TargetInstance.from_json(target) for target in result]
        return to_our_model

    async def get_target_request(self, target_id: TargetId) -> str:
        """Get next target action."""
        response = await get_target_request(str(target_id), client=self._client)
        return response.parsed

    async def execute_service_action(self, service_id: ServiceId, action: str) -> None:
        """Get next target action."""
        response = await execute_service_action(service_id, json_body=action, client=self._client)
        return response.parsed

    async def do_maintenance(self) -> None:
        """Get next target action."""
        response = await do_maintenance(client=self._client)
        return response.parsed


class WebSocketWrapper:

    @classmethod
    async def send_message(cls, websocket: WebSocket, message: Message):
        json_message = to_json(message)
        raw_message = json.dumps(json_message)
        await websocket.send(raw_message)

    @classmethod
    async def recv_message(cls, websocket: WebSocket) -> Message:
        raw_message = await websocket.recv()
        json_message = json.loads(raw_message)
        return from_json(json_message)
