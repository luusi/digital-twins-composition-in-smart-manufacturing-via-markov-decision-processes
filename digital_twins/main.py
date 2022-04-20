import argparse
import asyncio
import copy
import json
import time
import urllib.parse
from typing import Dict

import websockets
import logging
from pathlib import Path

from mdp_dp_rl.processes.mdp import MDP

from digital_twins.Devices.base import Event, EventType
from digital_twins.Devices.utils import service_from_json, target_from_json
from digital_twins.target_simulator import TargetSimulator
from digital_twins.things_api import config_from_json, ThingsAPI
from digital_twins.wrappers import AbstractServiceWrapper
from stochastic_service_composition.composition import composition_mdp
from stochastic_service_composition.services import Service
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
parser.add_argument("--config", type=str, default="config.json", help="Path to configuration file (in JSON format).")
parser.add_argument("--timeout", type=int, default=0, help="Timeout to wait message sent correctly.")


async def main(config: str, timeout: int):

    """Run the main."""
    services = []
    service_ids = []
    configuration = config_from_json(Path(config))
    api = ThingsAPI(configuration)
    data = api.search_services("")
    for element in data:
        service = service_from_json(element, reset=True)
        services.append(service)

        service_ids.append(element["thingId"])

    data = api.search_targets("")
    assert len(data) == 1
    target: Target = target_from_json(data[0])
    target_thing_id = data[0]["thingId"]
    print("Found services: ")
    for service_id, service_name in enumerate(service_ids):
        print(f"- {service_id}: {service_name}")

    print("Opening websocket endpoint...")
    ws_uri = "wss://things.eu-1.bosch-iot-suite.com/ws/2"
    async with websockets.connect(ws_uri, extra_headers=websockets.http.Headers({
                                      'Authorization': 'Bearer ' + api.get_token()
                                  })) as websocket:
        print("Collecting problem data...")

        system_state = [service.initial_state for service in services]
        target_simulator = TargetSimulator(target)
        iteration = 0

        event_cmd = "START-SEND-EVENTS"
        print("EVENT_CMD: ", event_cmd)
        event_cmd = urllib.parse.quote(event_cmd, safe='')
        await websocket.send(event_cmd)
        print("Listening to events originating")
        message_receive = await websocket.recv()
        print("Message received: ", message_receive)
        if message_receive != "START-SEND-EVENTS:ACK":
            raise Exception("Ack not received")

        old_policy = None
        while True:

            mdp: MDP = composition_mdp(target, *services)
            orchestrator_policy = mdp.get_optimal_policy()
            # detect when policy changes
            if old_policy is None:
                old_policy = orchestrator_policy
            if old_policy.policy_data != orchestrator_policy.policy_data:
                print(f"Optimal Policy has changed!\nold_policy = {old_policy}\nnew_policy={orchestrator_policy}")
            old_policy = orchestrator_policy

            # waiting for target action
            print("Waiting for messages from target...")
            target_message = await websocket.recv()
            target_message_json = json.loads(target_message)
            event = Event.from_message(target_message_json)
            if event.from_ != target_thing_id or event.type != EventType.MODIFIED or event.feature != "current_action":
                # print(f"Skipping, not a message from the target: {target_message_json}")
                continue
            print(f"Received message: {target_message_json}")
            print(f"Event parsed: {event}")

            target_action = target_message_json["value"]
            current_target_state = target_simulator.current_state
            target_simulator.update_state(target_action)
            print(f"Iteration: {iteration}, target action: {target_action}")
            current_state = (tuple(system_state), current_target_state, target_action)

            orchestrator_choice = orchestrator_policy.get_action_for_state(current_state)
            if orchestrator_choice == "undefined":
                print(f"Execution failed: no service can execute {target_action} in system state {system_state}")
                break
            # send_action_to_service
            service_index = orchestrator_choice
            chosen_thing_id = service_ids[service_index]
            print("Sending message to thing: ", chosen_thing_id, target_action, timeout)
            response = api.send_message_to_thing(chosen_thing_id, target_action, {}, timeout)
            print(f"Got response: {response}")
            print("Waiting for update from websocket...")
            message_receive = await websocket.recv()
            service_message_json = json.loads(message_receive)
            service_event = Event.from_message(service_message_json)
            # wait until we don't receive the right message from the chosen thing
            while service_event.from_ != chosen_thing_id or service_event.type != EventType.MODIFIED or service_event.feature != "current_state":
                message_receive = await websocket.recv()
                service_message_json = json.loads(message_receive)
                service_event = Event.from_message(service_message_json)
            print(f"Update after change: {service_message_json}")
            next_service_state = service_message_json["value"]
            # compute the next system state
            system_state[service_index] = next_service_state

            # send "DONE" to target
            response = api.send_message_to_thing(target_thing_id, "done", {}, timeout)
            iteration += 1

            print("Download new transition function from chosen service")
            data = api.get_thing(chosen_thing_id)[0]
            old_transition_function = services[service_index].current_transition_function
            new_service = service_from_json(data, reset=False)
            services[service_index] = new_service
            if old_transition_function != new_service.current_transition_function:
                print(f"Transition function has changed!\nOld: {old_transition_function}\nNew: {new_service.transition_function}")

            # execute the target loop ~four times before starting the maintenance
            if iteration % (14 * 4) == 0:
                print("Sending msg for scheduled maintenance")
                for element in service_ids:
                    api.send_message_to_thing(element, "Scheduled_maintenance", {}, timeout)
                # reset current state and transition function
                for s in services:
                    s.reset()
                # reset system state (but not target state)
                system_state = [service.initial_state for service in services]

if __name__ == "__main__":
    arguments = parser.parse_args()
    result = asyncio.get_event_loop().run_until_complete(main(arguments.config, arguments.timeout))
