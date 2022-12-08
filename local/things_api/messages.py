from functools import singledispatch
from typing import Dict

from digital_twins.Devices.utils import target_from_json
from local.things_api.data import ServiceInstance, target_to_json
from local.things_api.helpers import TargetId
from stochastic_service_composition.target import Target


class Message:

    TYPE: str


class Register(Message):

    TYPE = "register"

    def __init__(self, service_instance: ServiceInstance) -> None:
        self.service_instance = service_instance


class Update(Message):

    TYPE = "update"

    def __init__(self, service_instance: ServiceInstance) -> None:
        self.service_instance = service_instance


class RegisterTarget(Message):

    TYPE = "register_target"

    def __init__(self, target_id: TargetId, target: Target) -> None:
        self.target_id = target_id
        self.target = target


def from_json(obj: Dict) -> Message:

    message_type = obj["type"]
    payload = obj["payload"]

    match message_type:
        case Register.TYPE:
            service_instance = ServiceInstance.from_json(payload)
            return Register(service_instance)
        case Update.TYPE:
            service_instance = ServiceInstance.from_json(payload)
            return Update(service_instance)
        case RegisterTarget.TYPE:
            target_id = TargetId(payload["id"])
            target = target_from_json(payload)
            return RegisterTarget(target_id, target)

    raise ValueError(f"message type {message_type} not expected")


@singledispatch
def to_json(message: Message):
    raise NotImplementedError


@to_json.register
def register_to_json(message: Register):
    return dict(
        type=message.TYPE,
        payload=message.service_instance.json
    )


@to_json.register
def update_to_json(message: Update):
    return dict(
        type=message.TYPE,
        payload=message.service_instance.json
    )


@to_json.register
def register_target_to_json(message: RegisterTarget):
    target_payload = target_to_json(message.target_id, message.target)
    return dict(
        type=message.TYPE,
        payload=target_payload
    )
