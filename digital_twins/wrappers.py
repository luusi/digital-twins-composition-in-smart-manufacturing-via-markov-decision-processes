from abc import ABC, abstractmethod
import copy
from typing import Optional, Dict

from digital_twins.constants import DEFAULT_DEGRADATION_COST, DEFAULT_DEGRADATION_PROBABILITY, \
    DEFAULT_MAX_BROKEN_PROB
from stochastic_service_composition.services import Service
from stochastic_service_composition.types import State


class AbstractServiceWrapper(ABC):

    def __init__(self, service: Service):
        self._service = service
        self.reset()

    @abstractmethod
    def update(self, starting_state: State, action_name: str):
        """Update service."""

    def reset(self):
        self._current_transition_function = copy.deepcopy(self._service.transition_function)
        self._current_state = self._service.initial_state

    @property
    def service(self):
        return self._service

    @property
    def current_transition_function(self):
        return copy.deepcopy(self._current_transition_function)

    @property
    def current_state(self):
        return self._current_state

    @property
    def states(self):
        return self._service.states

    @property
    def actions(self):
        return self._service.actions

    @property
    def final_states(self):
        return self._service.final_states

    @property
    def initial_state(self):
        return self._service.initial_state

    @property
    def transition_function(self):
        """Make wrapper look like the underlying service, except for the property "transition function"."""
        return self.current_transition_function


def initialize_wrapper(service: Service, current_state: Optional[State] = None, current_transition_function: Optional[Dict] = None) -> AbstractServiceWrapper:
    """
    Instantiate abstract service wrapper according to service type.

    Try to wrap the service as "breakable" and, if failed, use normal service wrapper.
    """
    try:
        wrapper = BreakableServiceWrapper(service)
    except AssertionError:
        wrapper = NormalServiceWrapper(service)
    if current_state is not None:
        wrapper._current_state = current_state
    if current_transition_function is not None:
        wrapper._current_transition_function = current_transition_function
    return wrapper


class NormalServiceWrapper(AbstractServiceWrapper):

    def update(self, starting_state: State, action_name: str):
        """Do nothing."""


class BreakableServiceWrapper(AbstractServiceWrapper):

    AVAILABLE_STATE_NAME = "available"
    DONE_STATE_NAME = "done"
    BROKEN_STATE_NAME = "broken"

    def __init__(self, service: Service, degradation_cost: float = DEFAULT_DEGRADATION_COST, degradation_probability: float = DEFAULT_DEGRADATION_PROBABILITY,
                 max_broken_prob: float = DEFAULT_MAX_BROKEN_PROB):
        super().__init__(service)
        self.check_breakable_service(service)
        self._degradation_cost = degradation_cost
        self._degradation_probability = degradation_probability
        self._max_broken_probability = max_broken_prob

    @classmethod
    def check_breakable_service(cls, service) -> None:
        """Check that the wrapped service is of type "breakable"."""
        assert service.states == {cls.AVAILABLE_STATE_NAME, cls.DONE_STATE_NAME, cls.BROKEN_STATE_NAME}
        # check transitions from available
        transitions_from_available_state = service.transition_function[cls.AVAILABLE_STATE_NAME]
        assert len(transitions_from_available_state) == 1
        action, (next_state_dist, reward) = list(transitions_from_available_state.items())[0]
        assert set(next_state_dist.keys()) == {cls.DONE_STATE_NAME, cls.BROKEN_STATE_NAME}

        # check transitions from done
        transitions_from_done_state = service.transition_function[cls.DONE_STATE_NAME]
        assert len(transitions_from_done_state) == 1
        check_action, (next_state_dist, reward) = list(transitions_from_done_state.items())[0]
        assert check_action == f"check_{action}"
        assert set(next_state_dist.keys()) == {cls.AVAILABLE_STATE_NAME}

        # check transitions from broken
        transitions_from_broken_state = service.transition_function[cls.BROKEN_STATE_NAME]
        assert len(transitions_from_broken_state) == 1
        check_action, (next_state_dist, reward) = list(transitions_from_broken_state.items())[0]
        assert check_action == f"check_{action}"
        assert set(next_state_dist.keys()) == {cls.AVAILABLE_STATE_NAME}

    def update(self, starting_state: State, action_name: str):
        """Update the probability."""
        if starting_state == self.BROKEN_STATE_NAME:
            self.reset()
            return
        if starting_state == self.DONE_STATE_NAME:
            return

        transitions_from_available_state = self._current_transition_function[self.AVAILABLE_STATE_NAME]
        action = list(transitions_from_available_state.keys())[0]

        # update prob
        old_broken_prob = transitions_from_available_state[action][0][self.BROKEN_STATE_NAME]
        new_broken_prob = min(self._max_broken_probability, old_broken_prob + self._degradation_probability)
        transitions_from_available_state[action][0][self.BROKEN_STATE_NAME] = new_broken_prob
        transitions_from_available_state[action][0][self.DONE_STATE_NAME] = 1.0 - new_broken_prob

        # update cost
        old_cost = transitions_from_available_state[action][1]
        new_cost = old_cost - self._degradation_cost
        transitions_from_available_state[action][1] = new_cost
