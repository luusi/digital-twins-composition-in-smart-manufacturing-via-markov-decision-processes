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
- To modify characteristics of the Digital Twins and do tests go to the page https://bosch-iot-suite.com/.

- Login with the following credentials:

  email: reviewer.dt.research@gmail.com

  password: Reviewer12!

- Then, click on ```Go to the Developer Console```, ```Things``` where there is the list of Digital Twins to edit, select the specific Things to modify, click on the ```JSON``` button and finally on the ```Edit``` button.

- **Note that:** the target Digital Twin cannot be modified, because it is linear and represents the step to follow in order to produce ceramics.

- Services Digital Twins can be modified, except the services that can't break (i.e., ```provisioning_service```, ```painting_human_service``` and ```shipping_service```). Both ```attributes``` and ```features``` contain the transition function, but since the ```attributes``` field contains the transition function when the machine is not yet used, cannot be edited. 

- In ```feautures``` ```transition_function``` properties can be modified, in particular the values of probabilities and costs in order to see how the system behaves with different parameters, for example, high probability to break and high cost to perform an action and vice versa.
## How run the code

- To establish the connection with the Bosch IoT Things platform, first launch the ```main.py``` file in ```stochastic-service-composition/digital_twins/```. Here, the orchestrator process is defined: it downloads target and services specification that are loaded in the system, builds the composition MDP, and calculates the optimal policy. It connects to the MQTT client and waits for the event from the target service.

- Then, run ```launch_devices.py``` file in ```stochastic-service-composition/digital_twins/Devices/```. The Digital Twins devices are launched and the action from the target service is released and sent to the orchestrator.

- The communication between the orchestrator and devices starts and the orchestrator, once receives the action from the target service, dispatches it to the correct service that can perform it.

## Transition Function Evaluation 

- The transition function changes: as the use of the machine increases, its state of wear increases.

- Every machine starts from a low broken probability (0.05) and a low cost to perform a certain action (-1); at each iteration the broken probability increases by 0.05 and the cost increases by -1.

- We show an output of the painting service transition function before and after the service performs _painting_ action.
```
Old: {'available': {'painting': [{'done': 0.9, 'broken': 0.1}, -2.0]},
'broken': {'check_painting': [{'available': 1}, -10]},
'done': {'check_painting': [{'available': 1}, 0]}}

New: {'available': {'painting': [{'done': 0.85, 'broken': 0.15000000000000002}, -3.0]},
'broken': {'check_painting': [{'available': 1}, -10]},
'done': {'check_painting': [{'available': 1}, 0]}}
``` 

## Policy Evaluation

- Since at each iteration the transition function change due to increased wear of the machines, also the optimal policy is recalculated.

- We have two services that perform painting action: the machine one and the human one.

- At the beginning painting machine is chosen because it is not yet worn. 

- In the early iterations, although the broken probability and the cost are increasing, they are not so important to make the optimal policy change. For the orchestrator will be more convenient choose the machine service over the human (see previous output). 
  
- The human painting service has no possibility to break but has high cost of performing the action (-5). 

- At a certain point broken probability of painting machine became 0.2 and cost of performing the action -4, so the optimal policy change and the orchestrator choose human service because is more convenient than machine one.
  ``` 
  Old: {'available': {'painting': [{'done': 0.85, 'broken': 0.15000000000000002}, -3.0]},
  'broken': {'check_painting': [{'available': 1}, -10]},
  'done': {'check_painting': [{'available': 1}, 0]}}
  
  New: {'available': {'painting': [{'done': 0.8, 'broken': 0.2}, -4.0]},
  'broken': {'check_painting': [{'available': 1}, -10]},
  'done': {'check_painting': [{'available': 1}, 0]}}

- We show the output of the main regarding the change in the calculation of new policy (for reasons of space we omit the other states):

  ```
  old_policy= 's9',
  'painting'
  ): 5,
  ((
  'available',
  'available',
  'available',
  'available',
  'done',
  'available',
  'available',
  'available',
  'available'
  ),
  
  new_policy= 's9',
  'painting'
  ): 4,
  ((
  'available',
  'available',
  'available',
  'available',
  'done',
  'available',
  'available',
  'available',
  'available'
  ),

- We observe that the old policy chose for ```painting``` action the service 5 i.e., the painting service, in the calculation of the new policy instead is used service 4 i.e., the human painting service.

- **Note that:** the example that we show in the ceramics production case study happens with the current parameters, all the users who wanted to simulate other case studies could get different results.

## Scheduled maintenance

- Periodically, a scheduled maintenance is implemented for every service. This permits to repair a machine that is broken or simply reset a machine.

- The transition function is restored to the moment when the machine shows no signs of wear.

- We show an output of a scheduled maintenance of a service:
```
Updating transition function: {"topic": "com.bosch.services/second_baking_service/things/twin/commands/modify","headers": {"response-required": false},"path":
 "/features/transition_function/properties/transitions", "value" : {"available": {"second_baking": [{"done": 0.95, "broken": 0.05}, -1]}, "broken": {"check_second_baking": [{"available
": 1}, -10]}, "done": {"check_second_baking": [{"available": 1}, 0]}}}
```

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
