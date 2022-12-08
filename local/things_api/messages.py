from functools import singledispatch
from typing import Dict

from local.things_api.data import ServiceInstance


class Message:

    TYPE: str

class Register(Message):

    TYPE = "register"

    def __init__(self, service_instance: ServiceInstance) -> None:
        self.service_instance = service_instance


def from_json(obj: Dict, sender: str) -> Message:

    message_type = obj["type"]
    payload = obj["payload"]

    match message_type:
        case Register.TYPE:
            service_instance = ServiceInstance.from_json(payload)
            return Register(service_instance)

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
