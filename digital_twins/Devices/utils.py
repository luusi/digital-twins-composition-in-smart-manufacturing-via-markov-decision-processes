from typing import Dict

from digital_twins.wrappers import AbstractServiceWrapper, initialize_wrapper
from stochastic_service_composition.services import Service, build_service_from_transitions
from stochastic_service_composition.target import Target, build_target_from_transitions


def service_from_json(data: Dict, reset: bool = True) -> AbstractServiceWrapper:
    """Load a service from its JSON description."""
    features = data["features"]
    attributes = data["attributes"]
    # TODO: change with the one below
    #transitions = features["transition_function"]["properties"]["transitions"]
    transitions = attributes["transitions"]
    initial_state = attributes["initial_state"]
    final_states = set(attributes["final_states"])

    service = build_service_from_transitions(transitions, initial_state, final_states)
    service_wrapper = initialize_wrapper(service)
    if not reset:
        current_transitions = features["transition_function"]["properties"]["transitions"]
        current_state = features["current_state"]["properties"]["value"]
        service_wrapper._current_transition_function = current_transitions
        service_wrapper._current_state = current_state
    return service_wrapper


def target_from_json(data: Dict) -> Target:
    attributes = data["attributes"]
    transitions = attributes["transitions"]
    initial_state = attributes["initial_state"]
    final_states = set(attributes["final_states"])
    return build_target_from_transitions(transitions, initial_state, final_states)
