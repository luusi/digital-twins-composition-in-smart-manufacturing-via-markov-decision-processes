"""This module implements the algorithm to compute the system-target MDP."""
from collections import deque
from typing import Deque, Dict, List, Set, Tuple

from mdp_dp_rl.processes.mdp import MDP

from stochastic_service_composition.services import Service, build_system_service
from stochastic_service_composition.target import Target
from stochastic_service_composition.types import Action, State, MDPDynamics

COMPOSITION_MDP_INITIAL_STATE = 0
COMPOSITION_MDP_INITIAL_ACTION = "initial"
COMPOSITION_MDP_UNDEFINED_ACTION = "undefined"
DEFAULT_GAMMA = 0.9


def composition_mdp(
    target: Target, *services: Service, gamma: float = DEFAULT_GAMMA
) -> MDP:
    """
    Compute the composition MDP.

    :param target: the target service.
    :param services: the community of services.
    :param gamma: the discount factor.
    :return: the composition MDP.
    """
    system_service = build_system_service(*services)

    initial_state = COMPOSITION_MDP_INITIAL_STATE
    # one action per service (1..n) + the initial action (0)
    actions: Set[Action] = set(range(len(services)))
    initial_action = COMPOSITION_MDP_INITIAL_ACTION
    actions.add(initial_action)

    # add an 'undefined' action for sink states
    actions.add(COMPOSITION_MDP_UNDEFINED_ACTION)

    transition_function: MDPDynamics = {}

    visited = set()
    to_be_visited = set()
    queue: Deque = deque()

    # add initial transitions
    transition_function[initial_state] = {}
    initial_transition_dist = {}
    symbols_from_initial_state = target.policy[target.initial_state].keys()
    for symbol in symbols_from_initial_state:
        next_state = (system_service.initial_state, target.initial_state, symbol)
        next_prob = target.policy[target.initial_state][symbol]
        initial_transition_dist[next_state] = next_prob
        queue.append(next_state)
        to_be_visited.add(next_state)
    transition_function[initial_state][initial_action] = (initial_transition_dist, 0.0)  # type: ignore

    while len(queue) > 0:
        current_state = queue.popleft()
        to_be_visited.remove(current_state)
        visited.add(current_state)
        current_system_state, current_target_state, current_symbol = current_state

        transition_function[current_state] = {}
        # index system symbols (action, service_id) by symbol
        system_symbols: List[Tuple[Action, int]] = list(
            system_service.transition_function[current_system_state].keys()
        )
        system_symbols_by_symbols: Dict[Action, Set[int]] = {}
        for action, service_id in system_symbols:
            system_symbols_by_symbols.setdefault(action, set()).add(service_id)

        for i in system_symbols_by_symbols.get(current_symbol, set()):
            next_transitions = {}
            # TODO check if it is needed
            if current_symbol not in target.transition_function[current_target_state]:
                continue
            next_reward = (
                target.reward[current_target_state][current_symbol]
                if (current_symbol, i)
                in system_service.transition_function[current_system_state]
                else 0
            )
            next_target_state = target.transition_function[current_target_state][
                current_symbol
            ]
            next_system_states, next_system_reward = system_service.transition_function[
                current_system_state
            ][(current_symbol, i)]
            for next_symbol, next_prob in target.policy[next_target_state].items():
                for next_system_state, next_system_prob in next_system_states.items():
                    next_state = (next_system_state, next_target_state, next_symbol)
                    if next_prob * next_system_prob == 0.0:
                        continue
                    next_transitions[next_state] = next_prob * next_system_prob
                    if next_state not in visited and next_state not in to_be_visited:
                        to_be_visited.add(next_state)
                        queue.append(next_state)
            transition_function[current_state][i] = (  # type: ignore
                next_transitions,  # type: ignore
                next_reward + next_system_reward,
            )

        # states without outgoing transitions are sink states.
        # add loop transitions with
        # - 'undefined' action
        # - probability 1
        # - reward 0
        if len(transition_function[current_state]) == 0:
            transition_function.setdefault(current_state, {})
            transition_function[current_state][COMPOSITION_MDP_UNDEFINED_ACTION] = (
                {current_state: 1.0},
                0.0,
            )  # type: ignore

    return MDP(transition_function, gamma)
