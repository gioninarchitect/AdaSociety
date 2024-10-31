## ***Contract***

### Overview
The environment is divided into two stages: the contract formation stage for determining social connections and the physical interaction stage to interact with the physical component and co-players with determined social connections. The contract formation stage lasts for $cN$ time steps,where $c$ is a positive integer and $N$ is the number of agents, while the physical interaction stage has a duration of $T$. 

Before the contract formation stage $(0 \leq t < cN)$, an order ($i_1, i_2, ..., i_N$) is randomly sampled. At time $t$, agent $i_k$, where $k = t \mod N$, takes social action, selecting a group node $v_g \in V_g$ to connect. An agent can connect with only one group node. Agents within the same group are considered to have formed a contract to share rewards. In the physical interaction stage $(t \geq cN)$, all agents act synchronously within the physical component, and the rewards received are equally divided among the agents within the same group.

In summary, contract predefines connection semantics, where agents need to select partners while learning coordination with various ones.

### Game rule
- Initialize the environment with natural resources and corresponding events. Agents have no social connections and belong to no group.
- At the contract formation stage $(0 \leq t < cN)$, each time step, an agent can
    - social connect: an agent can connect or disconnect to a group node, representing the switches in groups.

- At the physical interaction stage $(t \geq cN)$, each time step, all agents can
    - move: up, down, left, right
    - pick / dump resources: pick up or dump natural or synthesized resources 
    - produce: synthesize resources on the corresponding event grid

- The contract game terminates when reaching the termination point of the environment.


### Implement Task Configurations in [`contract.json`](../../../config/task/contract.json)

We introduce the task configurations for **Contract** (**Contract-Easy**). Configuration for **Contract-Hard** is implemented in [`contract_hard.json`](../../../config/task/contract_hard.json) which is quite similar to [`contract.json`](../../../config/task/contract.json), only with an enlarged map, more resources/events/players/groups, and a different maximum running steps.

#### Agent Configuration

Configure the agent and environment handler for **Contract**.

```json
{
    "agent": "project.tasks.contract.agent.agent.ContractAgent",
    "env_handler": "project.agent.env_handler.EnvHandler",
}
```

#### Map Configuration

Initiate a 7 * 7 map without blocks.

```json
{
    "base_map": {
      "init_rule": "blank",
      "size": {
        "x": 7,
        "y": 7
      },
    },
}
```
- **init_rule**: The map initialization rule, with available values `blank`, `box`, or `map_file`. 
  - `blank` means there are no blocks. 
  - `box` means the map is surrounded by blocks. 
  - `map_file` means customizing the map shape in the map file.
- **size**: The map size, which must be set when `init_rule` is `blank` or `box`, includes both `x` and `y` dimensions.

#### Static Configuration

Define the length of communication as 1. In the initial state, agents do not have relations with each other. Four groups are initiated so that agents can connect or disconnect to groups in the contract formation stage. In the initial state, resources do not stack on one another.

```json
{
  "static": {
      "communication_length": 1,
      "social": {
          "relations": [],
          "groups": [
              {
                "name": "group_0",
                "players": {}
              },
              {
                "name": "group_1",
                "players": {}
              },
              {
                "name": "group_2",
                "players": {}
              },
              {
                "name": "group_3",
                "players": {}
              }
          ]
      },
      "stackable": false
    },
}
```

- **communication_length**: Communication length determines the maximum length of communication with other agent.
- **social**: Social attribute configuration, including relations and groups.
- **relations**: Relationships between players.
- **groups**: Player grouping configuration, with each group including a name and players.
- **stackable**: Determines whether resource stacking is allowed.

#### Random Configuration

Randomly generate 4 units of `wood` and 4 units of `stone` as resources, 41 `hammer_craft` events, and 4 players including 2 `carpenters` and 2 `miners`.

```json
{
    "random": {
      "resources": [
        {
          "name": "wood",
          "num": {
            "rule": "random",
            "min": 5,
            "max": 5
          },
          "repeat": 4
        },
        {
          "name": "stone",
          "num": {
            "rule": "random",
            "min": 5,
            "max": 5
          },
          "repeat": 4
        }
      ],
      "events": [
        {
          "name": "hammer_craft",
          "repeat": 41
        }
      ],
      "players": [
        {
          "job": "carpenter",
          "repeat": 2
        },
        {
            "job": "miner",
            "repeat": 2
          }
      ]
    },
}
```

- **repeat**: Number of repetitions for blocks/resources/events/players.
- **resources**: Configuration for randomly generated resources.
- **name**: Name of the resource/event.
- **num**: Configuration for the quantity of the resource, including the generation rule (rule) and the minimum and maximum values (min and max).
- **events**: Configuration for randomly generated events.
- **players**: Configuration for randomly generated players.
- **job**: Player’s profession, such as carpenter or miner.

#### Other Configuration

Define `splite_score_to_group` in the post-update process so that agents in the same group can share the reward according to `division_weight`. In **Contract**, `division_weight = 1`, agents in the same group share the reward equally. Define the maximum running step as 120. Define `negotiation_round = 5` so that contract formation stage will last for $5 \times (2+2) = 20$ time steps.

```json
{
    "post_updates":[
      {
        "function": "split_score_to_group",
        "kwargs": {
          "attribute": "division_weight"
        }
      }
    ],
    "max_length": 120,
    "contract": {
      "negotiation_round": 5
    }
}
```

- **post_updates**: Defines the game rules for the task. Function is selected from the post-processing functions in the environment and is located in the file. You can choose to define these post-processing functions yourself to form a new game. `kwargs` are the parameters required by the game.
- **max_length**: The max_length defines the maximum running step of the task.
- **negotiation_round**: Total number of rounds in the contract formation stage (i.e. $c$ in **Task Description & Challenges**). 

### Implement Agent in [`agent.py`](./agent/agent.py)

Based on the template given in [`agent.py`](../../agent/agent.py), we implement `ContractAgent`. We explain some key functions:
- `__init__`: init **Contract** agent with environment information and task specific information. Define the observation space and action space based on task description.

 - `update`: get observation, reward, and other information from environment and process with `update_obs` and `update_reward` functions.

- `update_obs`: translate the received observation into task-specific observation format.

- `update_policy`: translate policy into actions in **Contract** including move, produce, pick/dump resources, quit/join a group.

- `get_action_mask`: based on the grid-observation, agent's inventory, and current time step, generate an action mask vector, with all allowed actions as 1s and others as 0s. For instance, if the current time step falls into the contract formation stage, agents are only allowed to quit/join a group, and thus, the action mask is generated as `action_mask[-self.group_num:] = 1`.

- `get_turn_order`: randomly generate an order, in the contract formation stage, agents follow this order to take actions.
