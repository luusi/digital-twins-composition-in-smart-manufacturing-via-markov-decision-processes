import urllib

import requests

from digital_twins.Devices.base import BoschIotService
from digital_twins.Devices.utils import service_from_json
from digital_twins.things_api import ThingsAPI, config_from_json
from pathlib import Path

import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    certificate_path = "digital_twins/temp/iothub.crt"
    device_name = "door_device"
    thing_id = f"com.bosch.services:{device_name}"
    subject = "open_door_bathroom"
    body = {}
    timeout = 10

    config = config_from_json(Path("digital_twins/config.json"))
    api = ThingsAPI(config)
    response = api.send_message_to_thing(thing_id, subject, body, timeout)
    # response = api.receive_message_from_thing(thing_id)
    # print(response)