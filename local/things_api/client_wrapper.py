"""Wrapper class to auto-generated OpenAPI client functions."""
from typing import List

from local.things_api.client import Client
from local.things_api.client.api.health.app_server_api_get_health import asyncio_detailed as get_health
from local.things_api.client.api.services.app_server_api_get_services import asyncio_detailed as get_services
from local.things_api.client.models import Service
from local.things_api.data import ServiceInstance

TIMEOUT = 10.0


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
