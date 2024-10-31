## ***Exploration***

### Overview
In this scenario, all built-in resources and events are included. Physical actions and social actions are available at every step. All agents share a common value preference, where 1) resources near the end of the synthesis tree are assigned high value, and 2) synthetic resources are valued higher than natural resources. Agents start with a few resources and events within a simple environment initially. As the agents explore the synthesis tree, their behaviors trigger the mechanisms to depict changes in the physical environment. 

Due to partial observation, time limitations, and the challenges associated with exploring new resources, agents may manipulate the social state to encourage interest binding, information sharing, and division of labor, which helps to maximize rewards. Besides, more resources and events are unlocked gradually, increasing the complexity of the exploration. Dependency between different resources and events evaluates the agents’ abilities to make deep explorations in the environment actively.

### Game rule
- Initialize the environment with natural resources and corresponding events. Agents have no social connections and belong to no group.
- At each time step, agents can 
    - move: up, down, left, right
    - pick / dump resources: pick up or dump natural or synthesized resources 
    - produce: synthesize resources on the corresponding event grid
    - communicate: send messages to another agent
    - social connect: agents connect or disconnect to a group node, representing the switches in groups.
    - connect player: agents connect or disconnect to another agent, representing the and social relationship updates.
- As the agents synthesize more resources, the environment contains more resources to pick up /dump. Also, if agents construct complex social relations, the reward and information will be shared in groups.
- The exploration game terminates when reaching the termination point of the environment.

### Implement Task Configurations in [`exploration.json`](../../../config/task/exploration.json)

#### Agent Configuration

Configure the agent and environment handler for **Exploration**.

```json
{
    "agent": "project.tasks.exploration.agent.agent.ExplorationAgent",
    "env_handler": "project.agent.env_handler.EnvHandler",
}
```

#### Map Configuration

Initiate a 20 * 20 map without blocks.

```json
{
    "base_map": {
      "init_rule": "blank",
      "size": {
        "x": 20,
        "y": 20
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

Define the length of communication as 3. In the initial state, agents do not have relations with each other. Eight groups are initiated. In the initial state, resources do not stack on one another.

```json
{
  "static": {
      "communication_length": 3,
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
            },
            {
                "name": "group_4",
                "players": {}
            },
            {
                "name": "group_5",
                "players": {}
            },
            {
                "name": "group_6",
                "players": {}
            },
            {
                "name": "group_7",
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

Randomly generate 25 `blocks`, `resources` (including 10 units of `wood`, 10 units of `stone`, 10 units of `coal`, ...), `events` (including 40 `hammercraft`, 40 `torchcraft`, 30 `steelmaking`, ...), and 8 `explorer` agents.

```json
{
  "random": {
    "blocks": [
      {
        "repeat": 25
      }
    ],
    "resources": [
      {
        "name": "wood",
        "num": {
          "rule": "random",
          "min": 20,
          "max": 20
        },
        "repeat": 10
      },
      {
        "name": "stone",
        "num": {
          "rule": "random",
          "min": 20,
          "max": 20
        },
        "repeat": 10
      },
      {
        "name": "coal",
        "num": {
          "rule": "random",
          "min": 10,
          "max": 10
        },
        "repeat": 10
      },
      {
        "name": "iron",
        "num": {
          "rule": "random",
          "min": 8,
          "max": 8
        },
        "repeat": 10
      },
      {
        "name": "gem_mine",
        "num": {
          "rule": "random",
          "min": 4,
          "max": 4
        },
        "repeat": 5
      },
      {
        "name": "clay",
        "num": {
          "rule": "random",
          "min": 8,
          "max": 8
        },
        "repeat": 10
      }
    ],
    "events": [
      {
        "name": "hammer_craft",
        "repeat": 40
      },
      {
          "name": "torch_craft",
          "repeat": 40
      },
      {
          "name": "steelmaking",
          "repeat": 30
      },
      {
          "name": "potting",
          "repeat": 30
      },
      {
          "name": "shovel_craft",
          "repeat": 20
      },
      {
          "name": "pickaxe_craft",
          "repeat": 20
      },
      {
        "name": "cutter_craft",
        "repeat": 20
      },
      {
        "name": "gem_craft",
        "repeat": 10
      },
      {
        "name": "totem_making",
        "repeat": 10
      }
    ],
    "players": [
      {
        "job": "explorer",
        "repeat": 8,
        "fov": 2
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
- **fov**: Field of view.

#### Other Configuration

In the pre-update process, the environment will clear the `communication` attribute in agents' relations. In the post-update process, agents in the same group can share the reward according to `division_weight`. Define the maximum running step as 500.

```json
{
  "max_length": 500,
  "pre_updates":[
    {
      "function": "clear_temporary_relation",
      "kwargs": {
        "attr": "communication"
      }
    }
  ],
  "post_updates":[
    {
      "function": "split_score_to_group",
      "kwargs": {
        "attribute": "division_weight"
      }
    }
  ]
}
```
- **post_updates**: Defines the game rules for the task. Function is selected from the post-processing functions in the environment and is located in the file. You can choose to define these post-processing functions yourself to form a new game. `kwargs` are the parameters required by the game. 
- **pre_updates**: Similar to `post_update`, defines the game rule before the actions are executed in each step. 
- **max_length**: The `max_length` defines the maximum running step of the task.

### Implement Agent in [`agent.py`](./agent/agent.py)

Based on the template given in [`agent.py`](../../agent/agent.py), we implement `ExplorationAgent`. We explain some key functions:
- `__init__`: init **Exploration** agent with environment information and task specific information. Define the observation space and action space based on task description.

 - `update`: get observation, reward, and other information from the environment and process with `update_obs` and `update_reward` functions.

- `update_obs`: translate the received observation into task-specific observation format.

- `update_policy`: translate policy into actions in **Exploration** including move, produce, pick/dump resources, communication, connect/disconnect to another agent, quit/join a group.

- `get_action_mask`: based on the grid-observation and the agent's inventory, generate an action mask vector, with all allowed actions as 1s and others as 0s. 

- `check_share_relation`: check whether two agents have a relation with the `sharing` attribute in the social graph. 
