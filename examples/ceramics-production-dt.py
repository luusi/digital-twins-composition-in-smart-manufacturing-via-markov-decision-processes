from mdp_dp_rl.algorithms.dp.dp_analytic import DPAnalytic

from docs.notebooks.utils import print_policy_data, print_value_function, print_q_value_function
from stochastic_service_composition.composition import composition_mdp
from stochastic_service_composition.services import Service, build_service_from_transitions
from stochastic_service_composition.target import build_target_from_transitions

DEFAULT_REWARD = -1.0
DEFAULT_BROKEN_REWARD = -10.0
DEFAULT_BROKEN_PROB = 0.05


def target_service():
    """Build the target service."""
    transition_function = {
        "s0": {"provisioning": ("s1", 1.0, 0), },
        "s1": {"moulding": ("s2", 1.0, 0), },
        "s2": {"check_moulding": ("s3", 1.0, 0), },
        "s3": {"drying": ("s4", 1.0, 0), },
        "s4": {"check_drying": ("s5", 1.0, 0), },
        "s5": {"first_baking": ("s6", 1.0, 0), },
        "s6": {"check_first_baking": ("s7", 1.0, 0), },
        "s7": {"enamelling": ("s8", 1.0, 0), },
        "s8": {"check_enamelling": ("s9", 1.0, 0), },
        "s9": {"painting": ("s10", 1.0, 0), },
        "s10": {"check_painting": ("s11", 1.0, 0), },
        "s11": {"second_baking": ("s12", 1.0, 0), },
        "s12": {"check_second_baking": ("s13", 1.0, 0), },
        "s13": {"shipping": ("s0", 1.0, 0.0), },

    }

    initial_state = "s0"
    final_states = {"s0"}

    return build_target_from_transitions(
        transition_function, initial_state, final_states
    )


def provisioning_service(action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the provisioning device."""
    transitions = {
        "available": {
            "provisioning": ({"available": 1.0}, action_reward),
        },
    }
    final_states = {"available"}
    initial_state = "available"
    return build_service_from_transitions(transitions, initial_state, final_states)  # type: ignore


def _build_device_service(action_name: str, broken_prob: float, broken_reward: float, action_reward: float):
    assert 0.0 <= broken_prob <= 1.0
    success_prob = 1.0 - broken_prob
    transitions = {
        "available": {
          action_name: ({"done": success_prob, "broken": broken_prob}, action_reward),
        },
        "broken": {
            f"check_{action_name}": ({"available": 1.0}, broken_reward),
        },
        "done": {
            f"check_{action_name}": ({"available": 1.0}, 0.0),
        }
    }
    final_states = {"available"}
    initial_state = "available"
    return build_service_from_transitions(transitions, initial_state, final_states)  # type: ignore


def moulding_service(broken_prob: float = DEFAULT_BROKEN_PROB, broken_reward: float = DEFAULT_BROKEN_REWARD, action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the moulding device."""
    return _build_device_service("moulding", broken_prob=broken_prob, broken_reward=broken_reward, action_reward=action_reward)


def drying_service(broken_prob: float = DEFAULT_BROKEN_PROB, broken_reward: float = DEFAULT_BROKEN_REWARD, action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the drying device."""
    return _build_device_service("drying", broken_prob=broken_prob, broken_reward=broken_reward, action_reward=action_reward)


def first_baking_service(broken_prob: float = DEFAULT_BROKEN_PROB, broken_reward: float = DEFAULT_BROKEN_REWARD, action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the first baking device."""
    return _build_device_service("first_baking", broken_prob=broken_prob, broken_reward=broken_reward, action_reward=action_reward)


def enamelling_service(broken_prob: float = DEFAULT_BROKEN_PROB, broken_reward: float = DEFAULT_BROKEN_REWARD, action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the enamelling device."""
    return _build_device_service("enamelling", broken_prob=broken_prob, broken_reward=broken_reward, action_reward=action_reward)


def painting_service(broken_prob: float = DEFAULT_BROKEN_PROB, broken_reward: float = DEFAULT_BROKEN_REWARD, action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the painting device."""
    return _build_device_service("painting", broken_prob=broken_prob, broken_reward=broken_reward, action_reward=action_reward)


def painting_human_service(action_reward: float =-5.0) -> Service:
    """Build the painting device."""
    return _build_device_service("painting", broken_prob=0.0, broken_reward=0.0, action_reward=action_reward)


def second_baking_service(broken_prob: float = DEFAULT_BROKEN_PROB, broken_reward: float = DEFAULT_BROKEN_REWARD, action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the second_baking device."""
    return _build_device_service("second_baking", broken_prob=broken_prob, broken_reward=broken_reward, action_reward=action_reward)


def shipping_service(action_reward: float = DEFAULT_REWARD) -> Service:
    """Build the shipping device."""
    transitions = {
        "available": {
            "shipping": ({"available": 1.0}, action_reward),
        },
    }
    final_states = {"available"}
    initial_state = "available"
    return build_service_from_transitions(transitions, initial_state, final_states)  # type: ignore


if __name__ == '__main__':
    gamma = 0.9
    target = target_service()

    services = [
        provisioning_service(),
        moulding_service(),
        drying_service(),
        first_baking_service(),
        enamelling_service(),
        painting_service(broken_prob=0.5),
        painting_human_service(),
        second_baking_service(),
        shipping_service()
    ]

    mdp = composition_mdp(target, *services, gamma=gamma)

    opn = DPAnalytic(mdp, 1e-4)
    opt_policy = opn.get_optimal_policy_vi()
    value_function = opn.get_value_func_dict(opt_policy)
    q_value_function = opn.get_act_value_func_dict(opt_policy)

    # remove '0' state to sort output
    opt_policy.policy_data.pop(0, None)
    value_function.pop(0, None)
    q_value_function.pop(0, None)

    # print_policy_data(opt_policy)
    # print()
    # print_value_function(value_function)
    # print()
    print_q_value_function(q_value_function)

