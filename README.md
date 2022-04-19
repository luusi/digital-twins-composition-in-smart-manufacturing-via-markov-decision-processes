# Stochastic Service Composition

Implementation of Digital Twins Composition in Smart Manufacturing via Markov Decision Processes.
## Preliminaries

- Set up the virtual environment. 
First, install [Pipenv](https://pipenv-fork.readthedocs.io/en/latest/).
Then:
```
pipenv install --dev
```

- Install the Python package in development mode:
```
pip install -e .
# alternatively:
# python setup.py develop 
```

- To use rendering functionalities, you will also need to install Graphviz. 
  At [this page](https://www.graphviz.org/download/) you will
  find the releases for all the supported platform.

## Digital Twins

The folder `digital_twins` contains the integration of the 
stochastic service composition with the Bosch IoT Things platform.

To run the examples, go to the terminal and set:
```
export PYTHONPATH=".:$PYTHONPATH"
```

Then, run:
```
python digital_twins/main.py --config digital_twins/config.json
```
## Experiments
- To modify characteristics of the Digital Twins go to the page https://bosch-iot-suite.com/.

- Login with the following credentials:

  email: reviewer.dt.research@gmail.com

  password: Reviewer12!

- Then, click on ```Go to the Developer Console```, ```Things``` where there are the list of Digital Twins to edit.

## Run code
- To establish the connection with the Bosch IoT Things platform, first launch the ```main.py``` file in ```stochastic-service-composition/digital_twins/```. The orchestrator downloads target and services specification, build the composition MDP, and calculates the optimal policy. It connects to the MQTT client and waits for the event from the target service.

- Then, run ```launch_devices.py``` file in ```stochastic-service-composition/digital_twins/Devices/```. The Digital Twins devices are launched and is released the action from the target service and it is sent to the orchestrator.

- The communication between the orchestrator and devices starts and the orchestrator, once receive the action from the target service, dispatches it to the correct service that can perform it.

## Policy Evaluation

## Tests

To run tests: `tox`

To run only the code tests: `tox -e py3.7`

To run only the linters: 
- `tox -e flake8`
- `tox -e mypy`
- `tox -e black-check`
- `tox -e isort-check`

Please look at the `tox.ini` file for the full list of supported commands. 

## License

`stochastic_service_composition` is released under the MIT license.

Copyright 2021 Luciana Silo
