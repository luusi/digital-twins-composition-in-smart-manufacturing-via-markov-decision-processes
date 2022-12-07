import dataclasses
from copy import deepcopy
from enum import Enum
from typing import Any, Dict

from local.things_api.helpers import ServiceId
from stochastic_service_composition.services import Service, build_service_from_transitions
from stochastic_service_composition.types import MDPDynamics


class ServiceType(Enum):
    SERVICE = "service"


@dataclasses.dataclass(frozen=True)
class ServiceInstance:
    service_id: ServiceId
    service_type: ServiceType
    service_spec: Service
    current_state: Any
    transition_function: MDPDynamics

    @classmethod
    def from_json(cls, obj: Dict) -> "ServiceInstance":
        """Get the service instance from JSON format."""
        service_id = ServiceId(obj["id"])
        service_type = ServiceType(obj["attributes"]["type"])

        current_transition_function = obj["features"]["transition_function"]
        current_state = obj["features"]["current_state"]

        transitions = obj["attributes"]["transitions"]
        initial_state = obj["attributes"]["initial_state"]
        final_states = obj["attributes"]["final_states"]
        service = build_service_from_transitions(transitions, initial_state, final_states)
        return ServiceInstance(
            service_id,
            service_type,
            service,
            current_state,
            current_transition_function
        )

    @property
    def to_json(self) -> Dict:
        """Get the service instance in JSON format."""
        result = dict()

        result["id"] = str(self.service_id)
        result["features"] = dict(
            transition_function=self.transition_function,
            current_state=self.current_state
        )
        result["attributes"] = dict(
            type=self.service_type.SERVICE.value,
            transitions=self.transition_function,
            initial_state=self.service_spec.initial_state,
            final_states=sorted(self.service_spec.final_states)
        )
        return result
