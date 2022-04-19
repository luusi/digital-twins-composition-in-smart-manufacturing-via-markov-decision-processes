"""This module contains the tests for the target.py module."""
from graphviz import Digraph
from mdp_dp_rl.processes.mdp import MDP

from stochastic_service_composition.composition import composition_mdp
from stochastic_service_composition.rendering import mdp_to_graphviz
from stochastic_service_composition.services import (
    build_service_from_transitions,
    build_deterministic_service_from_transitions,
)
from stochastic_service_composition.target import build_target_from_transitions


def test_composition(
    target_service,
    bathroom_heating_device,
    bathtub_device,
    kitchen_door_device,
    bathroom_door_device,
    kitchen_exhaust_fan_device,
    user_behaviour,
):
    """Test a composition example."""
    services = [
        bathroom_heating_device,
        bathtub_device,
        kitchen_door_device,
        bathroom_door_device,
        kitchen_exhaust_fan_device,
        user_behaviour,
    ]
    mdp = composition_mdp(target_service, *services)
    assert isinstance(mdp, MDP)
    mdp_graphviz = mdp_to_graphviz(mdp)
    assert isinstance(mdp_graphviz, Digraph)


def test_composition_with_sink_states():
    """Test a composition with sink states."""
    login_service = build_deterministic_service_from_transitions(
        {
            "s0": {"login": "s1"},
            "s1": {
                "logout": "s0",
                "country": "error",
                "currency": "error",
                "stock": "error",
            },
            "error": {},
        },
        "s0",
        {"s0"},
    )

    form_service = build_deterministic_service_from_transitions(
        {
            "s0": {"login": "error", "logout": "error", "country": "s1"},
            "s1": {"currency": "s0", "stock": "s0"},
            "error": {},
        },
        "s0",
        {"s0"},
    )

    target = build_target_from_transitions(
        {
            "s0": {"login": ("s1", 1.0, 0.0)},
            "s1": {"country": ("s2", 1.0, 0.0)},
            "s2": {"stock": ("s3", 1.0, 0.0)},
            "s3": {"logout": ("s0", 1.0, 1.0)},
        },
        "s0",
        {"s0"},
    )

    mdp = composition_mdp(target, login_service, form_service)
    assert isinstance(mdp, MDP)
    mdp_graphviz = mdp_to_graphviz(mdp)
    assert isinstance(mdp_graphviz, Digraph)


def test_garden_bots_system_composition(
    garden_bots_system_target, bcleaner_service, bmulti_service, bplucker_service
):
    """Test the garden bots system composition."""
    mdp = composition_mdp(
        garden_bots_system_target, bcleaner_service, bmulti_service, bplucker_service
    )
    assert isinstance(mdp, MDP)
    mdp_graphviz = mdp_to_graphviz(mdp)
    assert isinstance(mdp_graphviz, Digraph)
