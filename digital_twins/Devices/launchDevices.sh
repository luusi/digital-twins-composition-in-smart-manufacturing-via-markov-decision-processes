#!/bin/bash
export PYTHONPATH="."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

python3 ${SCRIPT_DIR}/bathroom_heating_device.py & disown
python3 ${SCRIPT_DIR}/bathtub_device.py & disown
python3 ${SCRIPT_DIR}/door_device.py & disown
python3 ${SCRIPT_DIR}/kitchen_exhaust_fan_device.py & disown
python3 ${SCRIPT_DIR}/user_behaviour.py & disown
