"""Utils for notebooks."""
import functools
import tempfile
from pathlib import Path

from IPython.lib.display import FileLink
from graphviz import Digraph
from IPython.core.display import HTML, SVG, display, Image
from mdp_dp_rl.algorithms.dp.dp_analytic import DPAnalytic
from mdp_dp_rl.processes.det_policy import DetPolicy
from mdp_dp_rl.processes.mdp import MDP
from mdp_dp_rl.processes.policy import Policy
from mdp_dp_rl.utils.standard_typevars import VFDictType, QFDictType

from stochastic_service_composition.rendering import service_to_graphviz, target_to_graphviz, mdp_to_graphviz
from stochastic_service_composition.services import Service
from stochastic_service_composition.target import Target

_image_classes = {
    "png": Image,
    "svg": SVG
}
_default_format = "png"


def display_svgs(*filenames, format: str="png"):
    assert format in _image_classes, f"format '{format}' not supported"
    image_class = _image_classes[format]
    images = [image_class(f) for f in filenames]
    for image in images:
        display(image)


def render_service(service: Service, format=_default_format):
    digraph = service_to_graphviz(service)

    render_digraph(digraph, format)


def render_target(target: Target, format=_default_format):
    digraph = target_to_graphviz(target)
    render_digraph(digraph, format)


def render_composition_mdp(mdp: MDP, format=_default_format):
    digraph = mdp_to_graphviz(mdp)
    render_digraph(digraph)


def render_digraph(digraph: Digraph, format=_default_format):
    tmp_dir = tempfile.mkdtemp()
    tmp_filepath = str(Path(tmp_dir, "output"))
    digraph.render(tmp_filepath, format=format)
    display_svgs(tmp_filepath + f".{format}", format=format)


@functools.singledispatch
def print_policy_data(policy: Policy):
    for state, action_probs in policy.policy_data.items():
        print(f"State={state}:")
        for action, prob in action_probs.items():
            print(f"\tAction={action} with prob={prob}")


@print_policy_data.register(DetPolicy)
def print_policy_data(policy: DetPolicy):
    print("Policy:")
    for state, action_probs in sorted(policy.policy_data.items()):
        unique_action = list(action_probs)[0]
        print(f"State={state},\tAction={unique_action}")


def print_value_function(value_function: VFDictType):
    print("Value function:")
    for state, value in sorted(value_function.items()):
        print(f"State={state},\tvalue={value}")


def print_q_value_function(q_value_function: QFDictType):
    print("Q-value function:")
    for state, action_value in sorted(q_value_function.items()):
        print(f"State={state}:")
        for action, value in sorted(action_value.items()):
            print(f"\tAction={action},\tValue={value}")
        print()
