import dataclasses
from enum import Enum
from typing import Any, Dict

from digital_twins.Devices.utils import target_from_json
from local.things_api.helpers import ServiceId, TargetId
from stochastic_service_composition.services import Service, build_service_from_transitions
from stochastic_service_composition.target import Target
from stochastic_service_composition.types import MDPDynamics, TargetDynamics


class ServiceType(Enum):
    SERVICE = "service"
    TARGET = "target"


@dataclasses.dataclass(frozen=True)
class ServiceInstance:
    service_id: ServiceId
    service_spec: Service
    current_state: Any
    transition_function: MDPDynamics

    @classmethod
    def from_json(cls, obj: Dict) -> "ServiceInstance":
        """Get the service instance from JSON format."""
        service_id = ServiceId(obj["id"])
        service_type = ServiceType(obj["attributes"]["type"])
        assert service_type == ServiceType.SERVICE

        current_transition_function = obj["features"]["transition_function"]
        current_state = obj["features"]["current_state"]

        transitions = obj["attributes"]["transitions"]
        initial_state = obj["attributes"]["initial_state"]
        final_states = set(obj["attributes"]["final_states"])
        service = build_service_from_transitions(transitions, initial_state, final_states)
        return ServiceInstance(
            service_id,
            service,
            current_state,
            current_transition_function
        )

    @property
    def json(self) -> Dict:
        """Get the service instance in JSON format."""
        result = dict()

        result["id"] = str(self.service_id)
        result["features"] = dict(
            transition_function=self.transition_function,
            current_state=self.current_state
        )
        result["attributes"] = dict(
            type=ServiceType.SERVICE.value,
            transitions=self.transition_function,
            initial_state=self.service_spec.initial_state,
            final_states=sorted(self.service_spec.final_states)
        )
        return result


@dataclasses.dataclass(frozen=True)
class TargetInstance:
    target_id: TargetId
    target_spec: Target
    current_action: Any

    @classmethod
    def from_json(cls, obj: Dict) -> "TargetInstance":
        """Get the service instance from JSON format."""
        service_id = TargetId(obj["id"])
        service_type = ServiceType(obj["attributes"]["type"])
        assert service_type == ServiceType.TARGET

        current_state = obj["features"]["current_action"]

        target_spec = target_from_json(obj)
        return TargetInstance(
            service_id,
            target_spec,
            current_state,
        )

    @property
    def json(self) -> Dict:
        """Get the service instance in JSON format."""
        result = dict()

        result["id"] = str(self.target_id)
        result["attributes"] = dict(
            type=ServiceType.TARGET.value,
            transitions=_get_target_dynamics(self.target_spec),
            initial_state=self.target_spec.initial_state,
            final_states=sorted(self.target_spec.final_states)
        )
        result["features"] = dict(
            current_action=self.current_action
        )
        return result


def _get_target_dynamics(target: Target) -> TargetDynamics:
    result: TargetDynamics = {}

    for state, trans_by_action in target.transition_function.items():
        result[state] = {}
        for action, next_state in trans_by_action.items():
            prob = target.policy[state][action]
            reward = target.reward[state][action]
            result[state][action] = (next_state, prob, reward)
    return result


def target_to_json(target_id: TargetId, target: Target) -> Dict:
    result = dict()

    result["id"] = str(target_id)
    result["attributes"] = dict(
        type=ServiceType.TARGET.value,
        transitions=_get_target_dynamics(target),
        initial_state=target.initial_state,
        final_states=sorted(target.final_states)
    )

    return result
