import argparse
import asyncio
import logging
from typing import List

from mdp_dp_rl.processes.mdp import MDP

from digital_twins.target_simulator import TargetSimulator
from local.things_api.client_wrapper import ClientWrapper
from local.things_api.data import ServiceInstance, TargetInstance
from stochastic_service_composition.composition import composition_mdp


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
    services: List[ServiceInstance] = await client.get_services()
    logger.info(f"Got {len(services)} available services")

    # get targets
    all_targets: List[TargetInstance] = await client.get_targets()
    logger.info(f"Got {len(all_targets)} target services")
    assert len(all_targets) == 1
    target = all_targets[0]
    target_id = target.target_id

    # start main loop
    old_policy = None
    target_simulator = TargetSimulator(target.target_spec)
    system_state = [service.service_spec.initial_state for service in services]
    iteration = 0
    while True:

        mdp: MDP = composition_mdp(target.target_spec, *[service.service_spec for service in services])
        orchestrator_policy = mdp.get_optimal_policy()
        # detect when policy changes
        if old_policy is None:
            old_policy = orchestrator_policy
        if old_policy.policy_data != orchestrator_policy.policy_data:
            logger.info(f"Optimal Policy has changed!\nold_policy = {old_policy}\nnew_policy={orchestrator_policy}")
        old_policy = orchestrator_policy

        # waiting for target action
        logger.info("Waiting for messages from target...")
        target_action = await client.get_target_request(target_id)
        current_target_state = target_simulator.current_state
        target_simulator.update_state(target_action)
        logger.info(f"Iteration: {iteration}, target action: {target_action}")
        current_state = (tuple(system_state), current_target_state, target_action)
        print(current_state)

        await asyncio.sleep(1.0)
        iteration += 1


if __name__ == "__main__":
    arguments = parser.parse_args()
    result = asyncio.get_event_loop().run_until_complete(main(arguments.host, arguments.port))
