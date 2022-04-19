"""This module contains the tests for the target.py module."""
from graphviz import Digraph

from stochastic_service_composition.rendering import target_to_graphviz
from stochastic_service_composition.target import Target


class TestInitialization:
    """Test class to test initialization and getters of the target class."""

    @classmethod
    def setup(cls):
        cls.states = {"s0", "s1"}
        cls.actions = {"a", "b"}
        cls.final_states = {"s1"}
        cls.initial_state = "s0"
        cls.transition_function = {
            "s0": {"a": "s1"},
            "s1": {"b": "s0"},
        }
        cls.policy = {"s0": {"a": 1.0}, "s1": {"b": 1.0}}
        cls.reward = {"s0": {"a": 1}, "s1": {"b": 0}}
        cls.target = Target(
            cls.states,
            cls.actions,
            cls.final_states,
            cls.initial_state,
            cls.transition_function,
            cls.policy,
            cls.reward,
        )

    def test_states(self):
        """Test the getter 'states'."""
        return self.target.states == self.states

    def test_actions(self):
        """Test the getter 'actions'."""
        return self.target.actions == self.actions

    def test_final_states(self):
        """Test the getter 'final_states'."""
        return self.target.final_states == self.final_states

    def test_initial_state(self):
        """Test the getter 'initial_state'."""
        return self.target.initial_state == self.initial_state

    def test_transition_function(self):
        """Test the getter 'dynamics_function'."""
        return self.target.transition_function == self.transition_function

    def test_policy(self):
        """Test the getter 'policy'."""
        return self.target.policy == self.policy

    def test_reward(self):
        """Test the getter 'reward'."""
        return self.target.reward == self.reward


def test_initialization_from_transitions(target_service):
    """
    Test initialization from transitions.

    The test will trigger initialization from the fixture.
    """


def test_rendering(target_service):
    """Test the transformation to Digraph."""
    current_service = target_service
    result = target_to_graphviz(current_service)
    assert isinstance(result, Digraph)
