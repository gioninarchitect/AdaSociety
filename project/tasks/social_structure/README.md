## ***Social Structure***

### Overview
 In this mini-task ***Social Structure***, there are 8 players interacting with the physical environment, such as moving, collecting resources, and synthesize tools. These players have a given social structure, which defining the contracts (**sharing observations or sharing rewards**) between players. We designed and tested 6 scenarios: 5 with static structure and 1 with dynamic structure. Each scenarios lasts 200-step actions, while actions do not change social structures. 


### Implement Task Configurations in [`social_structure_(structure_name).json`](../../../config/task)

In this section, we introduce the task configurations for **Social Structure - Dynamic** as an example. Configurations for other structures, which maintains static structures, are implemented in [`social_structure_(structure_name).json`](../../../config/task), which are simpler to [`social_structure_dynamic.json`](../../../config/task/social_structure_dynamic.json). All these scenarios have identical configuration but the *social* parameter.

#### Agent Configuration

Configure the agent and environment handler for contract.

```json
{
    "agent": "project.tasks.social_structure.agent.agent.SocialStructureAgent",
  	"env_handler": "project.agent.env_handler.EnvHandler",
}
```

#### Map Configuration

Initiate a 15 * 15 map without blocks.

```json
{
    "base_map": {
      "init_rule": "blank",
      "size": {
        "x": 15,
        "y": 15
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

Static configuration presentation the pre-defined information in the task. The definitions of the variables are provided below:

- **communication_length**: Communication length determines the maximum length of communication with other agent.
- **social**: Initial social attribute configuration, including relations and groups.
- **social_schedule**:  A dictionary where time serves as the key and a social structure as the value. It indicates how the social structure of the environment will evolve over time, transitioning to the specified structure at the designated moments.  
- **relations**: Relationships between players.
- **groups**: Player grouping configuration, with each group including a name and players.
- **stackable**: Determines whether initial resource stacking is allowed.

In this mini-task, we assume the length of communication is 1 and resources do not stack from one to another. We test 6 scenarios of different social structures, include 5 static structures and 1 dynamic structures. These structures are initialized in the variable *"social"*:
-	**Isolation**: There are only players nodes without any edges and group nodes. 
-	**Connection**: There are players nodes with edges between players but no group nodes. 
-	**Independent Group**: There are not only players nodes with edges between players but also group nodes and edges from players to group nodes. Each player can only join one group and players within one group share the reward equally.
-	**Overlapping Group**: There are not only players nodes with edges between players but also group nodes and edges from players to group nodes. Each player can join multiple groups and players within one group share the reward equally. Note that players split their rewards depending on the number of groups they joined for sharing.
-	**Inequality**: There are not only players nodes with edges between players but also group nodes and edges from players to group nodes. Each player can join multiple groups and players within one group share the reward depending on the weights of the edges. Note that players split their rewards depending on the number of groups they joined for sharing.
-   **Dynamic Structure**: In this scenario, we defined *social_schedule* for the dynamics of the social structure. Specifically, the testing scenario is: Inequality (Step 0-30) $\rightarrow$ Independent Group (Step 30-60) $\rightarrow$ Overlapping Group (Step 60-200). The mechanism of observation and reward sharing changes as the social structure changes. 
The json data for the *dynamic* scenario is shown follows:

```json
{
  "static": {
    "social": {
      "relations": [
        {
          "name": "share_obs",
          "attributes": {"sharing": {"Map": true} },
          "players": [
            {"from": 0, "to": 1},
            {"from": 0, "to": 4},
            {"from": 0, "to": 5},
            {"from": 1, "to": 0},
            {"from": 1, "to": 4},
            {"from": 1, "to": 5},
            {"from": 2, "to": 3},
            {"from": 2, "to": 6},
            {"from": 2, "to": 7},
            {"from": 3, "to": 2},
            {"from": 3, "to": 6},
            {"from": 3, "to": 7},
            {"from": 4, "to": 0},
            {"from": 4, "to": 1},
            {"from": 4, "to": 5},
            {"from": 5, "to": 0},
            {"from": 5, "to": 1},
            {"from": 5, "to": 4},
            {"from": 6, "to": 2},
            {"from": 6, "to": 3},
            {"from": 6, "to": 7},
            {"from": 7, "to": 2},
            {"from": 7, "to": 3},
            {"from": 7, "to": 6}
          ]
        }
      ],
      "groups": [
        {
          "name": "group_0",
          "players": {
            "ids": [0, 1, 4, 5],
            "attributes": {"division_weight": [0.85, 0.05, 0.05, 0.05]}
          }
        },
        {
          "name": "group_1",
          "players": {
            "ids": [2, 3, 6, 7],
            "attributes": {"division_weight": [0.05, 0.05, 0.85, 0.05]}
          }
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
    "social_schedule": {
      "30": {
        "relations": [
          {
            "name": "share_obs",
            "attributes": {"sharing": {"Map": true} },
            "players": [
              {"from": 0, "to": 1},
              {"from": 0, "to": 2},
              {"from": 0, "to": 3},
              {"from": 0, "to": 4},
              {"from": 0, "to": 5},
              {"from": 0, "to": 6},
              {"from": 0, "to": 7},
              {"from": 1, "to": 0},
              {"from": 1, "to": 2},
              {"from": 1, "to": 3},
              {"from": 1, "to": 4},
              {"from": 1, "to": 5},
              {"from": 1, "to": 6},
              {"from": 1, "to": 7},
              {"from": 2, "to": 0},
              {"from": 2, "to": 1},
              {"from": 2, "to": 3},
              {"from": 2, "to": 4},
              {"from": 2, "to": 5},
              {"from": 2, "to": 6},
              {"from": 2, "to": 7},
              {"from": 3, "to": 0},
              {"from": 3, "to": 1},
              {"from": 3, "to": 2},
              {"from": 3, "to": 4},
              {"from": 3, "to": 5},
              {"from": 3, "to": 6},
              {"from": 3, "to": 7},
              {"from": 4, "to": 0},
              {"from": 4, "to": 1},
              {"from": 4, "to": 2},
              {"from": 4, "to": 3},
              {"from": 4, "to": 5},
              {"from": 4, "to": 6},
              {"from": 4, "to": 7},
              {"from": 5, "to": 0},
              {"from": 5, "to": 1},
              {"from": 5, "to": 2},
              {"from": 5, "to": 3},
              {"from": 5, "to": 4},
              {"from": 5, "to": 6},
              {"from": 5, "to": 7},
              {"from": 6, "to": 0},
              {"from": 6, "to": 1},
              {"from": 6, "to": 2},
              {"from": 6, "to": 3},
              {"from": 6, "to": 4},
              {"from": 6, "to": 5},
              {"from": 6, "to": 7},
              {"from": 7, "to": 0},
              {"from": 7, "to": 1},
              {"from": 7, "to": 2},
              {"from": 7, "to": 3},
              {"from": 7, "to": 4},
              {"from": 7, "to": 5},
              {"from": 7, "to": 6}
            ]
          }
        ],
        "groups": [
          {
            "name": "group_0",
            "players": {
              "ids": [0, 1, 4, 5],
              "attributes": {"division_weight": [1, 1, 1, 1]}
            }
          },
          {
            "name": "group_1",
            "players": {
              "ids": [2, 3, 6, 7],
              "attributes": {"division_weight": [1, 1, 1, 1]}
            }
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
      "60": {
        "relations": [
          {
            "name": "share_obs",
            "attributes": {"sharing": {"Map": true} },
            "players": [
              {"from": 0, "to": 1},
              {"from": 0, "to": 2},
              {"from": 0, "to": 3},
              {"from": 0, "to": 4},
              {"from": 0, "to": 5},
              {"from": 1, "to": 0},
              {"from": 1, "to": 2},
              {"from": 1, "to": 3},
              {"from": 1, "to": 4},
              {"from": 1, "to": 5},
              {"from": 2, "to": 0},
              {"from": 2, "to": 1},
              {"from": 2, "to": 3},
              {"from": 2, "to": 6},
              {"from": 2, "to": 7},
              {"from": 3, "to": 0},
              {"from": 3, "to": 1},
              {"from": 3, "to": 2},
              {"from": 3, "to": 6},
              {"from": 3, "to": 7},
              {"from": 4, "to": 0},
              {"from": 4, "to": 1},
              {"from": 4, "to": 5},
              {"from": 4, "to": 6},
              {"from": 4, "to": 7},
              {"from": 5, "to": 0},
              {"from": 5, "to": 1},
              {"from": 5, "to": 4},
              {"from": 5, "to": 6},
              {"from": 5, "to": 7},
              {"from": 6, "to": 2},
              {"from": 6, "to": 3},
              {"from": 6, "to": 4},
              {"from": 6, "to": 5},
              {"from": 6, "to": 7},
              {"from": 7, "to": 2},
              {"from": 7, "to": 3},
              {"from": 7, "to": 4},
              {"from": 7, "to": 5},
              {"from": 7, "to": 6}
            ]
          }
        ],
        "groups": [
          {
            "name": "group_0",
            "players": {
              "ids": [0, 1, 4, 5],
              "attributes": {"division_weight": [1, 1, 1, 1]}
            }
          },
          {
            "name": "group_1",
            "players": {
              "ids": [2, 3, 6, 7],
              "attributes": {"division_weight": [1, 1, 1, 1]}
            }
          },
          {
            "name": "group_3",
            "players": {
              "ids": [0, 1, 2, 3],
              "attributes": {"division_weight": [1, 1, 1, 1]}
            }
          },
          {
            "name": "group_4",
            "players": {
              "ids": [4, 5, 6, 7],
              "attributes": {"division_weight": [1, 1, 1, 1]}
            }
          }
        ]
      }
    },
    "stackable": false
  },
}
```

#### Random Configuration

The random configuration include the environment information that are random generalized every time when user running the game. The information are related to *Blocks*, *Resources*, *Events*, and *Players*. The configuration parameters are as follows:

- **repeat**: Number of repetitions for blocks/resources/events/players.
- **resources**: Configuration for randomly generated resources.
- **name**: Name of the resource/event.
- **num**: Configuration for the quantity of the resource, including the generation rule (rule) and the minimum and maximum values (min and max).
- **events**: Configuration for randomly generated events.
- **players**: Configuration for randomly generated players.
- **job**: Player’s profession, such as carpenter or miner.

This mini-task ***Social Structure*** includes 6 types of resources, including *Wood*, *Stone*, *Coal*, *Iron*, *Hammer*, and *Torch*, and 2 types of events, including *HammerCraft* and *TorchCraft*. There are 8 players, including 4 carpenters and 4 miners. The json data for the ramdom generation is shown below:

```json
{
    "random": {
      "blocks": [
      {
        "repeat": 0
      }
    ],
    "resources": [
      {
        "name": "wood",
        "num": {
          "rule": "random",
          "min": 3,
          "max": 3
        },
        "repeat": 20
      },
      {
        "name": "stone", 
        "num": {
          "rule": "random",
          "min": 2,
          "max": 2
        },
        "repeat": 20
      },
      {
          "name": "coal",
          "num": {
            "rule": "random",
            "min": 5,
            "max": 5
          },
          "repeat": 4
      },
      {
          "name": "iron",
          "num": {
            "rule": "random",
            "min": 2,
            "max": 2
          },
          "repeat": 5
      }
    ],
    "events": [
      {
        "name": "hammer_craft",
        "repeat": 96
      },
      {
        "name": "torch_craft",
        "repeat": 8
      }
    ],
    "players": [
      {
        "job": "carpenter_hard",
        "repeat": 4
      },
      {
        "job": "miner_hard",
        "repeat": 4
      }
    ]
    },
}
```


#### Other Configuration

Define `splite_score_to_group` in the post-update process so that agents in the same group can share the reward according to `division_weight`. 

Define the maximum running step as 200. 

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
    "max_length": 200
}
```

- **post_updates**: Defines the game rules for the task. Function is selected from the post-processing functions in the environment and is located in the file. You can choose to define these post-processing functions yourself to form a new game. `kwargs` are the parameters required by the game.
- **max_length**: The max_length defines the maximum running step of the task.

### Implement Agent in [`agent.py`](./agent/agent.py)

Based on the template given in [`agent.py`](../../agent/agent.py), we implement `SocialStructureAgent`. We explain some key functions:
- `__init__`: init an agent with environment information and task specific information. Define the observation space and action space based on task description.

 - `update`: get observation, reward, and other information from environment and process with `update_obs` and `update_reward` functions.

- `update_obs`: translate the received observation and shared observation (if there is) into task-specific observation format.

- `update_policy`: translate policy into actions in **Social Structure** including move, produce, pick/dump resources.

- `get_action_mask`: based on the grid-observation, agent's inventory, and current time step, generate an action mask vector, with all allowed actions as 1s and others as 0s. For instance, the action to dump a type of resource is masked, if there is no such resource in the inventory.

