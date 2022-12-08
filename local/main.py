import argparse
import asyncio
import json
import logging
from typing import List

from mdp_dp_rl.processes.mdp import MDP

from digital_twins.target_simulator import TargetSimulator
from local.things_api.client_wrapper import ClientWrapper
from local.things_api.data import ServiceInstance, TargetInstance
from local.things_api.helpers import setup_logger
from stochastic_service_composition.composition import composition_mdp


logger = setup_logger("orchestrator")

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

        mdp: MDP = composition_mdp(target.target_spec, *[service.current_service_spec for service in services])
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
        logger.info(f"Current state: {current_state}")

        orchestrator_choice = orchestrator_policy.get_action_for_state(current_state)
        if orchestrator_choice == "undefined":
            logger.error(f"Execution failed: no service can execute {target_action} in system state {system_state}")
            break
        # send_action_to_service
        service_index = orchestrator_choice
        service_id = services[service_index].service_id
        logger.info(f"Sending message to thing: {service_id}, {target_action}")
        await client.execute_service_action(service_id, target_action)
        logger.info(f"Action has been executed")
        new_service_instance = await client.get_service(service_id)
        if services[service_index].transition_function != new_service_instance.transition_function:
            logger.info(f"Transition function for service {new_service_instance.service_id} has changed! Old: {services[service_index].transition_function}, New: {new_service_instance.transition_function}")
        services[service_index] = new_service_instance
        system_state[service_index] = new_service_instance.current_state
        logger.info(f"Next service state: {new_service_instance.current_state}")
        old_transition_function = services[service_index].transition_function
        if old_transition_function != new_service_instance.transition_function:
            logger.info(f"Transition function has changed!\nOld: {old_transition_function}\nNew: {new_service_instance.transition_function}")

        # execute the target loop ~four times before starting the maintenance
        if iteration % (14 * 4) == 0:
            logger.info("Sending msg for scheduled maintenance")
            await client.do_maintenance()
            # reset current state and transition function
            for s in services:
                logger.info(f"Restoring transition function for service '{s.service_id}'")
                s.transition_function = s.service_spec.transition_function
            # TODO: should reset it?
            # # reset system state (but not target state)
            # system_state = [service.initial_state for service in services]

        logger.info("Sleeping one second...")
        await asyncio.sleep(1.0)
        iteration += 1


if __name__ == "__main__":
    arguments = parser.parse_args()
    result = asyncio.get_event_loop().run_until_complete(main(arguments.host, arguments.port))
