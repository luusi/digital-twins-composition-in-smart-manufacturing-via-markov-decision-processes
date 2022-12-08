import argparse
import asyncio
import logging
from typing import List, Tuple

from local.things_api.client_wrapper import ClientWrapper
from local.things_api.data import ServiceInstance
from local.things_api.helpers import TargetId
from stochastic_service_composition.target import Target


def setup_logger():
    """Set up the logger."""
    logger = logging.getLogger("digital_twins")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logger()

parser = argparse.ArgumentParser("main")
parser.add_argument("--host", type=str, default="localhost", help="IP address of the HTTP IoT service.")
parser.add_argument("--port", type=int, default=8080, help="IP address of the HTTP IoT service.")


async def main(host: str, port: int) -> None:
    client = ClientWrapper(host, port)

    # check health
    response = await client.get_health()
    assert response.status_code == 200

    # get all services
    all_services: List[ServiceInstance] = await client.get_services()
    logger.info(f"Got {len(all_services)} available services")

    # get targets
    all_targets: List[Tuple[TargetId, Target]] = await client.get_targets()
    logger.info(f"Got {len(all_targets)} target services")


if __name__ == "__main__":
    arguments = parser.parse_args()
    result = asyncio.get_event_loop().run_until_complete(main(arguments.host, arguments.port))
