from pathlib import Path

from digital_twins.Devices.base import BoschIotService, BoschIoTTarget
from digital_twins.Devices.utils import service_from_json, target_from_json
from digital_twins.things_api import config_from_json, ThingsAPI


def run_device(device_name, path_to_json: Path = Path("config.json"), is_target: bool = False):
    certificate_path = "digital_twins/Devices/iothub.crt"
    thing_id = f"com.bosch.service:{device_name}"

    config_path = Path(path_to_json)
    config = config_from_json(config_path)
    api = ThingsAPI(config)
    if is_target:
        thing_target = target_from_json(api.get_thing(thing_id)[0])
        device = BoschIoTTarget(device_name, thing_target, certificate_path=certificate_path)
    else:
        thing_service = service_from_json(api.get_thing(thing_id)[0])
        device = BoschIotService(device_name, thing_service.service, certificate_path=certificate_path)

    device.run()
