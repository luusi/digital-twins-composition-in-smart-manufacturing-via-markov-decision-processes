# Stochastic Service Composition

Implementation of Digital Twins Composition in Smart Manufacturing via Markov Decision Processes.

The following sections are:
- Preliminaries
- Instructions to reproduce the experiments


## Preliminaries

We assume the review uses a UNIX-like machine and that has Python 3.8 installed.

- Set up the virtual environment. 
First, install [Pipenv](https://pipenv-fork.readthedocs.io/en/latest/).
Then:
```
pipenv install --dev
```
                    
- this command is to start a shell within the Python virtual environment (to be done whenever a new terminal is opened):
```
pipenv shell
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

- Generate Python client from OpenAPI v3.0 specification:
```
./scripts/generate-openapi-client.sh
```

## Instructions to reproduce the experiments

Each of the following commands must be run on a separate terminal with the virtual environment activated.

- Run the HTTP server that acts as service repository and communication middleware:
```
cd local/things_api
python app.py
```

- Run all the services and the target service:
```
cd local
python ./launch_devices.py
```

- Run the orchestrator
```
cd local
python main.py
```

### Transition Function Evaluation 

- The transition function changes: as the use of the machine increases, its state of wear increases.

- Every machine starts from a low broken probability (0.05) and a low cost to perform a certain action (-1); at each iteration the broken probability increases by 0.05 and the cost increases by 1.

- We show an output of the painting service transition function before and after the service performs _painting_ action.
```
Transition function for service painting_service has changed! 
Old: {'available': {'painting': [{'done': 0.95, 'broken': 0.05}, -1]}, 'broken': {'check_painting': [{'available': 1}, -10]}, 'done': {'check_painting': [{'available': 1}, 0]}},

New: {'available': {'painting': [{'done': 0.9, 'broken': 0.1}, -2.0]}, 'broken': {'check_painting': [{'available': 1}, -10]}, 'done': {'check_painting': [{'available': 1}, 0]}}
```

### Policy Evaluation

- Since at each iteration the transition function change due to increased wear of the machines, also the optimal policy is recalculated.

- We have two services that perform painting action: the machine one and the human one.

- At the beginning painting machine is chosen because it is not yet worn. 

- In the early iterations, although the broken probability and the cost are increasing, they are not so important to make the optimal policy change. For the orchestrator will be more convenient choose the machine service over the human (see previous output). 
  
- The human painting service has no possibility to break but has high cost of performing the action (-5). 

- At a certain point broken probability of painting machine became 0.2 and cost of performing the action -4, so the optimal policy change and the orchestrator choose human service because is more convenient than machine one.
```
Transition function for service painting_service has changed!
Old: {'available': {'painting': [{'done': 0.85, 'broken': 0.15000000000000002}, -3.0]}, 'broken': {'check_painting': [{'available': 1}, -10]}, 'done': {'check_painting': [{'available': 1}, 0]}},
New: {'available': {'painting': [{'done': 0.8, 'broken': 0.2}, -4.0]}, 'broken': {'check_painting': [{'available': 1}, -10]}, 'done': {'check_painting': [{'available': 1}, 0]}}
 ```
- We show the output of the main regarding the change in the calculation of new policy (for reasons of space we omit the other states):
```
old_policy: in state ((
  'available',
  'available',
  'available',
  'available',
  'available',
  'available',
  'available',
  'available',
  'available'),
 's9',
 'painting'), take action '5'.

new_policy: in state ((
  'available',
  'available',
  'available',
  'available',
  'available',
  'available',
  'available',
  'available',
  'available'),
 's9',
 'painting'), take action '4'.
```
- We observe that the old policy chose for ```painting``` action the service 5 i.e., the painting service, in the calculation of the new policy instead is used service 4 i.e., the human painting service.

- **Note that:** the example that we show in the ceramics production case study happens with the current parameters, all the users who wanted to simulate other case studies could get different results.

## Scheduled maintenance

- Periodically, a scheduled maintenance is implemented for every service. This permits to repair a machine that is broken or simply reset a machine.

- The transition function is restored to the moment when the machine shows no signs of wear.

- We show an output of a scheduled maintenance of a service:
```
Restoring transition function for service 'first_baking_service'
Updating transition function: '{'available': {'first_baking': [{'done': 0.95, 'broken': 0.05}, -1]}, 'broken': {'check_first_baking': [{'available': 1}, -10]}, 'done': {'check_first_baking': [{'available': 1}, 0]}}'
```
- In the standard output of the `main.py` process, after `Sending msg for scheduled maintenance`, if the `painting_service`
  was enough degradated, you will see an `Optimal Policy has changed!` message because its broken probability and cost
  returned at its original values.


Note that it could also happen that the scheduled maintenance does not change the optimal policy because the
`painting_service` became broken in a previous call of the service and, after transitioning in the `broken` state,
it was already repaired in the following `check` action, and therefore the maintenance step becomes redundant.

