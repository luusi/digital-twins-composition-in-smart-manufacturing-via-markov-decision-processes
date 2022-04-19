"""This module contains rendering functionalities."""
from typing import Callable, Dict

from graphviz import Digraph
from mdp_dp_rl.processes.mdp import MDP

from stochastic_service_composition.composition import COMPOSITION_MDP_INITIAL_STATE
from stochastic_service_composition.services import Service
from stochastic_service_composition.target import Target
from stochastic_service_composition.types import Action, State


def service_to_graphviz(
    service: Service,
    state2str: Callable[[State], str] = lambda x: str(x),
    action2str: Callable[[Action], str] = lambda x: str(x),
) -> Digraph:
    """
    Transform a service into a graphviz.Digraph object.

    :param service: the service object
    :param state2str: a callable that transforms states into strings
    :param action2str: a callable that transforms actions into strings
    :return: the graphviz.Digraph object
    """
    graph = Digraph(format="svg")
    graph.node("fake", style="invisible")
    graph.attr(rankdir="LR")

    for state in service.states:
        shape = "doublecircle" if state in service.final_states else "circle"
        if state == service.initial_state:
            graph.node(state2str(state), root="true", shape=shape)
        else:
            graph.node(state2str(state), shape=shape)
    graph.edge("fake", state2str(service.initial_state), style="bold")

    for start, outgoing in service.transition_function.items():
        for action, (next_states, reward) in outgoing.items():
            for state, prob in next_states.items():
                label = f"{action2str(action)}, {prob}, {reward}"
                graph.edge(
                    state2str(start),
                    state2str(state),
                    label=label,
                )

    return graph


def target_to_graphviz(
    target: Target,
    state2str: Callable[[State], str] = lambda x: str(x),
    action2str: Callable[[Action], str] = lambda x: str(x),
) -> Digraph:
    """
    Transform a target into a graphviz.Digraph object.

    :param target: the target object
    :param state2str: a callable that transforms states into strings
    :param action2str: a callable that transforms actions into strings
    :return: the graphviz.Digraph object
    """
    graph = Digraph(format="svg")
    graph.node("fake", style="invisible")
    graph.attr(rankdir="LR")

    for state in target.states:
        shape = "doublecircle" if state in target.final_states else "circle"
        if state == target.initial_state:
            graph.node(state2str(state), root="true", shape=shape)
        else:
            graph.node(state2str(state), shape=shape)
    graph.edge("fake", state2str(target.initial_state), style="bold")

    for start, outgoing in target.transition_function.items():
        action_distribution: Dict[Action, float] = target.policy.get(start, {})
        for action, end in outgoing.items():
            action_probability = action_distribution.get(action, 0.0)
            reward = target.reward.get(start, {}).get(action, 0.0)
            label = f"{action2str(action)},{reward},{action_probability}"
            graph.edge(
                state2str(start),
                state2str(end),
                label=label,
            )

    return graph


def mdp_to_graphviz(
    mdp: MDP,
    state2str: Callable[[State], str] = lambda x: str(x),
    action2str: Callable[[Action], str] = lambda x: str(x),
) -> Digraph:
    """
    Translate a composition-MDP instance into a Digraph.

    :param mdp: the composition-MDP object, obtained from composition.composition_mdp
    :param state2str: a callable that transforms states into strings
    :param action2str: a callable that transforms actions into strings
    :return: the graphviz.Digraph object
    """
    graph = Digraph(format="svg")
    graph.node("fake", style="invisible")
    graph.attr(rankdir="LR")

    for state in mdp.all_states:
        shape = "doubleoctagon" if state in mdp.get_terminal_states() else "box"
        if state == COMPOSITION_MDP_INITIAL_STATE:
            graph.node(state2str(state), root="true", shape=shape)
        else:
            graph.node(state2str(state), shape=shape)
    graph.edge("fake", state2str(COMPOSITION_MDP_INITIAL_STATE), style="bold")

    for start, outgoing in mdp.transitions.items():
        for action, next_states in outgoing.items():
            reward = mdp.rewards.get(start, {}).get(action, 0.0)
            for end, prob in next_states.items():
                label = f"{action2str(action)},{reward},{prob}"
                graph.edge(
                    state2str(start),
                    state2str(end),
                    label=label,
                )

    return graph
