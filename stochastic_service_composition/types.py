"""
This module contains the main type definitions.

In particular:
- State is the type of state; we require the
"""
from typing import Any, Dict, Hashable, Tuple

State = Hashable
Action = Any
Reward = float
Prob = float
TransitionFunction = Dict[State, Dict[Action, State]]
MDPDynamics = Dict[State, Dict[Action, Tuple[Dict[State, Prob], Reward]]]
TargetDynamics = Dict[State, Dict[Action, Tuple[State, Prob, Reward]]]
