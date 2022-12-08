import argparse
import asyncio
import logging

from local.things_api.client_wrapper import ClientWrapper


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
    result = await client.get_health()
    assert result.status_code == 200

    # get all services
    result = await client.get_services()
    print(result)


if __name__ == "__main__":
    arguments = parser.parse_args()
    result = asyncio.get_event_loop().run_until_complete(main(arguments.host, arguments.port))
