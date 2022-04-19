import inspect
import multiprocessing
import os
from functools import partial
from pathlib import Path

from digital_twins.run_device import run_device

CURRENT_DIRECTORY = Path(os.path.dirname(inspect.getfile(inspect.currentframe())))

DEVICES = [
    "provisioning_service",
    "drying_service",
    "enamelling_service",
    "moulding_service",
    "first_baking_service",
    "painting_human_service",
    "painting_service",
    "second_baking_service",
    "shipping_service",
]

TARGET = "target"

if __name__ == "__main__":
    pool = multiprocessing.Pool(len(DEVICES) + 1)

    run_device_config = partial(run_device, path_to_json=CURRENT_DIRECTORY / ".." / "config.json")
    target_result = pool.apply_async(run_device_config, args=[TARGET], kwds=dict(is_target=True))
    results = pool.map(run_device_config, DEVICES)

    try:
        for result in results:
            result.get()
        target_result.get()
    except Exception:
        print("Interrupted.")
        pool.terminate()
