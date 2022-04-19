import dataclasses
import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Callable, Dict, Tuple
import json

import paho.mqtt.client as mqtt

import threading

from digital_twins.wrappers import initialize_wrapper
from stochastic_service_composition.services import Service
from stochastic_service_composition.types import State, Action
from stochastic_service_composition.target import Target

DEVICE_ID_PREFIX = "com.bosch.services"
TENANT_ID = "t0c7793b5e5034a44a0a40bc454099cba_hub"
HUB_ADAPTER_HOST = "mqtt.bosch-iot-hub.com"
CERTIFICATE_PATH_ID = "./iothub.crt"
DEVICE_PASSWORD_ID = "secret"
# Configuration of client ID and publish topic
PUBLISH_TOPIC = "telemetry/"
CLIENT = mqtt.Client


class BoschIoTDevice(ABC):
    """Abstract class for representing a Bosch IoT Thing."""

    def __init__(self, device_name: str,
                 certificate_path: str = CERTIFICATE_PATH_ID):
        """
        Initialize the Bosch IoT device.

        :param device_name: the device name.
        :param certificate_path: the certificate path.
        """
        self._device_name = device_name
        self._certificate_path = certificate_path
        self._is_running: bool = False
        self._terminated = threading.Event()
        self._client = CLIENT(self.client_id)

    def reset(self):
        if self.is_running:
            raise ValueError("cannot reset while running")

    @property
    def is_running(self):
        """Check whether the device is running."""
        return self._is_running

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_id(self):
        return f"{DEVICE_ID_PREFIX}:{self.device_name}"

    @property
    def tenant_id(self):
        return f"{TENANT_ID}"

    @property
    def hub_adapter_host(self):
        return f"{HUB_ADAPTER_HOST}"

    @property
    def certificate_path(self):
        return self._certificate_path

    @property
    def device_password(self):
        return f"{DEVICE_PASSWORD_ID}"

    @property
    def client_id(self):
        return self.device_id

    @property
    def auth_id(self):
        return f"{DEVICE_ID_PREFIX}_{self.device_name}"

    @property
    def ditto_topic(self):
        return f"{DEVICE_ID_PREFIX}/{self.device_name}"

    @property
    def publish_topic(self):
        return f"{PUBLISH_TOPIC}{self.tenant_id}/{self.device_id}"

    def on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response from the server."""
        if rc != 0:
            print("Connection to MQTT broker failed: " + str(rc))
            return
            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
        # BEGIN SAMPLE CODE
        client.subscribe("command///req/#")
        # END SAMPLE CODE
        print("Connected!")

    @abstractmethod
    def on_message(self, client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""

    def run(self):
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        self._client.tls_set(self.certificate_path)
        username = self.auth_id + "@" + self.tenant_id
        self._client.username_pw_set(username, self.device_password)
        self._client.connect(self.hub_adapter_host, 8883, 60)

        self._client.loop_start()

        self._terminated.wait()

    def stop(self):
        """Stop the running device."""
        if not self.is_running:
            raise ValueError("device already stopped")
        self._terminated.set()

    def print(self, *args, **kwargs):
        print(f"[{self.device_name}] ", *args, **kwargs)


class BoschIoTTarget(BoschIoTDevice):

    def __init__(self, device_name: str,
                 target: Target,
                 certificate_path: str = CERTIFICATE_PATH_ID):
        super().__init__(device_name, certificate_path)
        self._target = target
        self._current_state = self._target.initial_state

    def reset(self):
        super().reset()
        self._current_state = self._target.initial_state

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        action = self.sample_action_and_update_state()
        self.send_next_action(action)

    def on_message(self, client, userdata, msg):
        """
        Handle messages to target device.

        This method is called when the target
        receives the message "DONE" from the
        Orchestrator, meaning that it can continue
        the execution and sample the next action.
        """
        print(f"Message received: client={client}, userdata={userdata}, msg={msg}")
        print("Sampling next action!")
        print(f"Current state before executing command: {self._current_state}")
        action = self.sample_action_and_update_state()
        print(f"Current state after executing command: {self._current_state}")
        print(f"Sending action {action} to orchestrator")
        self.send_next_action(action)

    def sample_action_and_update_state(self):
        """Sample the next action and update the state."""
        transitions_from_state = self._target.transition_function[self._current_state]
        action_to_probability = self._target.policy[self._current_state]
        actions, probabilities = zip(*action_to_probability.items())
        sampled_action = random.choices(actions, probabilities)[0]
        next_state = transitions_from_state[sampled_action]
        self._current_state = next_state
        return sampled_action

    def send_next_action(self, value):
        payload = '{"topic": "' + self.ditto_topic + \
                  '/things/twin/commands/modify","headers": {"response-required": false},' + \
                  '"path": "/features/current_action/properties/value","value" : "' + value + '"}'
        print(f"Updating state: {payload}")
        self._client.publish(self.publish_topic, payload)


class BoschIotService(BoschIoTDevice):
    """A Bosch IoT device."""

    def __init__(self, device_name: str,
                 service: Service,
                 certificate_path: str = CERTIFICATE_PATH_ID):
        super().__init__(device_name, certificate_path)
        self._service = service
        self._current_state = self._service.initial_state

        # TODO: decide how to initialize concrete class of AbstractServiceWrapper
        self.wrapper = initialize_wrapper(self._service)

    def reset(self):
        super().reset()
        self._current_state = self._service.initial_state

    def on_message(self, client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        self.print(f"Message received: client={client}, userdata={userdata}, msg={msg}")
        cmd = json.loads(msg.payload.decode("utf-8"))
        self.print("JSON Command: ", cmd)
        cmd_name = cmd["topic"].split("/")[-1]
        if cmd_name == "errors":
            self.print("WARNING: got 'errors' command" )
            return
        if cmd_name == "Scheduled_maintenance":
            self.print("This is a scheduled maintenance")
            self.execute_maintenance(cmd_name)
            return
            #starting_state = self._service.initial_state
            #self.update_state("current_state", starting_state)
            #transition_function = self._service.transition_function
            #self.update_transition_function("transition_function", transition_function)

        self.print(f"Command: {cmd_name}")
        self.print(f"Current state: {self._current_state}")

        self.execute_command(cmd_name)
        # self.change_status(json.dumps("terminated"))
        self.print(f"Current state after executing command: {self._current_state}")

    def execute_command(self, name: Action):
        starting_state = self._current_state
        transitions_from_current_state = self._service.transition_function[starting_state]
        next_service_states, reward = transitions_from_current_state[name]
        states, probabilities = zip(*next_service_states.items())
        new_state = random.choices(states, probabilities)[0]
        self._current_state = new_state
        self.wrapper.update(starting_state, name)
        transition_function = self.wrapper.transition_function
        self.update_state("current_state", new_state)
        self.update_transition_function("transition_function", transition_function)

    def execute_maintenance(self, maintenance: str):
        starting_state = self._service.initial_state
        self.update_state("current_state", starting_state)
        transition_function = self._service.transition_function
        self.update_transition_function("transition_function", transition_function)

    def update_state(self, feature, value):
        payload = '{"topic": "' + self.ditto_topic + \
                  '/things/twin/commands/modify","headers": {"response-required": false},' + \
                  '"path": "/features/' + feature + '/properties/value","value" : "' + value + '"}'
        self.print(f"Updating state: {payload}")
        self._client.publish(self.publish_topic, payload)

    def update_transition_function(self, feature, transitions):
        payload = '{"topic": "' + self.ditto_topic + \
                  '/things/twin/commands/modify","headers": {"response-required": false},' + \
                  '"path": "/features/' + feature + '/properties/transitions","value" : ' + json.dumps(transitions) + '}'
        # just to check if it is a valid JSON object
        json.loads(payload)
        self.print(f"Updating transition function: {payload}")
        # TODO: add path to transition function
        self._client.publish(self.publish_topic, payload)

    def publish_output(self, output):
        payload = '{"topic": "' + self.ditto_topic + \
                  '/things/twin/commands/modify","headers": {"response-required": false},' + \
                  '"path": "/features/output/properties/value","value" : "' + output + '"}'
        self._client.publish(self.publish_topic, payload)

    def change_status(self, status):
        payload = '{"topic": "' + self.ditto_topic + \
                  '/things/twin/commands/modify","headers": {"response-required": false},' + \
                  '"path": "/features/status/properties/value","value" : "' + status + '"}'
        self._client.publish(self.publish_topic, payload)


class EventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"


@dataclasses.dataclass(frozen=True)
class Event:
    from_: str
    type: EventType
    feature: str

    @classmethod
    def from_message(cls, message_json: Dict) -> "Event":
        topic_string = message_json["topic"]
        topic_tokens = topic_string.split("/")
        service_id = f"{topic_tokens[0]}:{topic_tokens[1]}"
        event_type_string = topic_tokens[-1]

        path = message_json["path"]
        path_tokens = path.split("/")
        feature_name = path_tokens[2]
        return Event(service_id, EventType(event_type_string), feature_name)
