
from stochastic_service_composition.target import Target
import random


class TargetSimulator:
    """Simulate a target."""

    def __init__(self, target: Target):
        """Initialize the simulator."""
        self.target = target

        self._current_state = self.target.initial_state

    @property
    def current_state(self):
        return self._current_state

    def reset(self):
        """Reset the target to its initial state."""
        self._current_state = self.target.initial_state

    def update_state(self, action) -> None:
        """Update the state given an action."""
        transitions_from_state = self.target.transition_function[self._current_state]
        next_state = transitions_from_state[action]
        self._current_state = next_state

    def sample_action(self) -> str:
        """Sample the next action and update the state."""
        action_to_probability = self.target.policy[self._current_state]
        actions, probabilities = zip(*action_to_probability.items())
        sampled_action = random.choices(actions, probabilities)[0]
        return sampled_action
