import logging
from pathlib import Path

from digital_twins.Devices.base import BoschIotService
from digital_twins.Devices.utils import service_from_json
from digital_twins.things_api import ThingsAPI, config_from_json

logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    device_name = "door_device"
    certificate_path = "digital_twins/temp/iothub.crt"
    thing_id = f"com.bosch.services:{device_name}"

    config = config_from_json(Path("digital_twins/config.json"))
    api = ThingsAPI(config)
    thing_service = service_from_json(api.get_thing(thing_id)[0])
    device = BoschIotService(device_name, thing_service.service, certificate_path=certificate_path)
    device.run()
