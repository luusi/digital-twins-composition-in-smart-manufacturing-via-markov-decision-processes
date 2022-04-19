import dataclasses
import json
import logging
import urllib.parse
from pathlib import Path
from typing import Dict

import requests

from digital_twins.constants import HEADERS, ACCESS_BOSCH_IOT_URL

logger = logging.getLogger(__name__)

SUFFIX_SEARCH_THINGS = "search/things"



@dataclasses.dataclass(frozen=True)
class APIConfig:
    uri: str
    namespace: str
    client_id: str
    client_secret: str
    scope: str


def config_from_json(filepath: Path) -> APIConfig:
    """Load APIConfig from JSON."""
    with filepath.open() as file:
        data = json.load(file)
    return APIConfig(
        data["uri"],
        data["namespace"],
        data["client_id"],
        data["client_secret"],
        data["scope"],
    )


class ThingsAPI:
    """Handle Bosch IoT APIs."""

    def __init__(self, config: APIConfig):
        """Initialize the class."""
        self.config = config

        self.token = self.get_token()

    @property
    def payload(self) -> Dict:
        return {
            'grant_type': 'client_credentials',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'scope': self.config.scope
        }

    def get_token(self):
        """Get access token from Bosch IoT."""
        payload = self.payload
        response = requests.post(f"{ACCESS_BOSCH_IOT_URL}/token", headers=HEADERS, data=payload)
        token = json.loads(response.content)["access_token"]
        logger.debug(f"Token loaded successfully: {token}")
        return token


    @property
    def _authorization_header(self):
        return {
            'accept': 'application/json',
            'Authorization': 'Bearer ' + self.token,
        }

    @property
    def _header(self):
        return {
            'accept': '*/*',
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json',
        }

    def get_thing(self, thing_id: str):
        headers = self._authorization_header
        params = (
            ('ids', thing_id),
        )
        url = f'{self.config.uri}/things'
        logger.debug(f"Calling GET on {url} with params={params}")
        response = requests.get(url, headers=headers, params=params)
        return json.loads(response.content)

    def search_things(self, namespace: str, filter: str):
        headers = self._authorization_header
        url = f'{self.config.uri}/search/things?' + filter
        response = requests.get(url, headers=headers)
        return json.loads(response.content)["items"]

    def search_services(self, namespace: str):
        return self.search_things(namespace, "filter=eq(attributes/type,'service')")

    def search_targets(self, namespace: str):
        return self.search_things(namespace, "filter=eq(attributes/type,'target')")

    def send_message_to_thing(self, thing_id: str, message_subject: str, body: Dict, timeout: int = 0):
        headers = self._header
        params = (
            ('timeout', str(timeout)),
        )
        url = f'{self.config.uri}/things/'
        thing_id = urllib.parse.quote(thing_id, safe='')
        response = requests.post(url + thing_id
                                 + '/inbox/messages/' + message_subject, headers=headers, params=params, json=body)

        #if not 200 <= response.status_code < 300:
            #raise Exception(f"error when sending a message: {response.content}")

    def receive_message_from_thing(self, thing_id: str, message_subject: str, body: Dict, timeout: int = 10):
        headers = self._header
        params = (
            ('timeout', str(timeout)),
        )
        url = f'{self.config.uri}/search/things'
        thing_id = urllib.parse.quote(thing_id, safe='')
        response = requests.post(url + thing_id
                                 + '/outbox/messages/' + message_subject, headers=headers, params=params, json=body)
        #if not 200 <= response.status_code < 300:
            #raise Exception(f"error when receiving message from thing: {response.content}")

    def change_property(self, thing_id: str, feature_id: str, property_path: str, body: Dict):
        headers = self._header
        thing_id = urllib.parse.quote(thing_id, safe='')
        property_path = urllib.parse.quote(property_path, safe='')
        url = f'{self.config.uri}/things'
        response = requests.put(url +
                                thing_id +
                                '/features/' + feature_id + '/properties/' + property_path,
                                headers=headers, json=body)

        #if not 200 <= response.status_code < 300:
            #raise Exception(f"error when changing property: {response.content}")
