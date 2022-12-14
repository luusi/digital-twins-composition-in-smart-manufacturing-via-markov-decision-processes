import inspect
import os
import subprocess
import sys
from pathlib import Path
from typing import List

CURRENT_DIRECTORY = Path(os.path.dirname(inspect.getfile(inspect.currentframe())))

DEVICES = [
    "provisioning_service.json",
    "drying_service.json",
    "enamelling_service.json",
    "moulding_service.json",
    "first_baking_service.json",
    "painting_human_service.json",
    "painting_service.json",
    "second_baking_service.json",
    "shipping_service.json",
]


TARGET = "target.json"


if __name__ == "__main__":

    config_dir = Path("things_api", "services")
    processes: List[subprocess.Popen] = []
    for configuration in DEVICES + [TARGET]:
        configuration_path = config_dir / configuration
        script_name = "run-service.py" if configuration in DEVICES else "run-target.py"
        process = subprocess.Popen([sys.executable, script_name, "--spec", str(configuration_path)])
        processes.append(process)

    for process in processes:
        process.wait()
