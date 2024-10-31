
# JSON Configuration File Documentation

This document provides a detailed explanation of the JSON files used for environment configuration. These JSON files are used to define the configuration of directories, tasks, jobs, resources, events and agents.

## Table of Contents

1. [Directory Configuration](#directory-configuration)
2. [Task Configuration](#task-configuration)
3. [Job Configuration](#job-configuration)
4. [Resource Configuration](#resource-configuration)
5. [Event Configuration](#event-configuration)

---

## Directory Configuration

The Directory Configuration specifies the required configuration paths for various elements of AdaSociety. Below is an example configuration for [main.json](./main.json):

```json
{
  "task": "./config/task/contact.json",
  "render": "./config/gui/render.json",
  "job": "./config/common/job.json",
  "resource": "./config/common/resource.json",
  "event": "./config/common/event.json",
  "__COMMENT__": "Enjoy AdaSociety!"
}
```

- **task**: Specifies the path to the task configuration file.
- **render**: Specifies the path to the rendering configuration file.
- **job**: Specifies the path to the job configuration file.
- **resource**: Specifies the path to the resource configuration file.
- **event**: Specifies the path to the event configuration file.

## **Task Configuration**

The following explains each part of the JSON file used for task configuration. This configuration file defines task settings such as maps, random content generation, and static attributes.

#### **Basic Map Configuration**

The basic map configuration specifies the initialization rules and the size or file path of the map.

```json
{
  "base_map": {
    "__COMMENT__": "Available rules: blank / box / map_file",
    "init_rule": "blank",
    "__COMMENT__": "`size` must be set if `init_rule` is either `blank` or `box`",
    "size": {
      "x": 7,
      "y": 7
    },
    "__COMMENT__": "`file_path` must be set if `init_rule` is `map_file`",
    "file_path": "./config/map/lost_temple.map"
  }
}
```

- **init_rule**: The map initialization rule, with available values `blank`, `box`, or `map_file`. 
  - `blank` means there are no blocks. 
  - `box` means the map is surrounded by blocks.
  - `map_file` means customizing the map shape in the map file.
- **size**: The map size, which must be set when init_rule is blank or box, includes both x and y dimensions.
- **file_path**: The map file path, which must be set when init_rule is map_file.

#### **Static Configuration**

The function of static configuration is to initialize the values of certain variables in the environment. During the running of the game, the values of these variables will change due to agents' actions.

```json
{
  "static": {
    "social": {
      "relations": [
        {
          "name": "Facetime",
          "players": [
            {
              "from": 2,
              "to": 3
            },
            {
              "from": 3,
              "to": 2
            }
          ],
          "attributes": {
            "vision_sharing": true
          }
        },
        {
          "name": "Partnership",
          "players": [
            {
              "from": 0,
              "to": 1
            }
          ],
          "requests": {
            "score_ratio": 0.3
          },
          "offers": {
            "score_ratio": 0.7
          }
        }
      ],
      "groups": [
        {
          "name": "group_0",
          "players": {"miner_0"}
        },
        {
          "name": "group_1",
          "players": {}
        },
        {
          "name": "group_2",
          "players": {"miner_1"}
        },
        {
          "name": "group_3",
          "players": {}
        }
      ],
    },
    "social_schedule": {
      "30": {
        "relations": [
          {
            "name": "share_obs",
            "attributes": {"sharing": {"Map": true} },
            "players": [
              {"from": 0, "to": 1},
              {"from": 1, "to": 0},
              {"from": 2, "to": 0},
              {"from": 3, "to": 0},
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
          }
        ]
      },
      "60": {
        "relations": [
          {
            "name": "share_obs",
            "attributes": {"sharing": {"Map": true} },
            "players": [
              {"from": 1, "to": 2},
              {"from": 1, "to": 3},
              {"from": 7, "to": 2},
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
    "blocks": [],
    "resources": [
      {
        "name": ["wood", "stone"],
        "positions": [
          [10, 10],
          [10, 10],
          [2, 2],
          [29, 2],
          [2, 30],
          [30, 30]
        ],
        "num": 50
      },
      {
        "name": "coal",
        "positions": [
          [10, 10],
          [13, 14],
          [13, 15],
          [13, 16],
          [13, 17],
          [14, 13]
        ],
        "num": 10
      }
    ],
    "events": [
      {
        "name": "hammer_craft",
        "positions": [
          [14, 14],
          [14, 17],
          [17, 14],
          [17, 17]
        ]
      },
      {
        "name": "torch_craft",
        "positions": [
          [16, 15],
          [15, 16],
          [16, 16],
          [15, 15]
        ]
      }
    ],
    "players": [
      {
        "job": "carpenter",
        "positions": [
          [10, 12]
        ]
      }
    ],
    "stackable": false
  }
}
```

- **social**: Social attribute configuration, including relations and groups.
  - **relations**: Relationships between players.
  - **groups**: Player grouping configuration, with each group including a name and players.
- **social_schedule**: The social_schedule specifies the changes in the social graph during the execution of *Adasociety* according to certain rules. Both relations and group information can be customized here.
- **resources**: Static resources, initialized on the map with pre-defined positions and numbers.
- **events**: Static events, initialized on the map with pre-defined event types and positions.
- **players**: The jobs and positions of the static players are pre-defined.
- **stackable**: Determines whether resource stacking is allowed.

#### **Random Configuration**

The random configuration section defines randomly generated content in the environment, such as `blocks`, `resources`, `events`, and `players`.

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
          "__COMMENT__": "static / loop / random",
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
  }
}
```

- **blocks**: Configuration for randomly generated blocks.
- **repeat**: Number of repetitions for blocks/resources/events/players.
- **resources**: Configuration for randomly generated resources.
  - **name**: Name of the resource/event.
  - **num**: Configuration for the quantity of the resource, including the generation rule (rule) and the minimum and maximum values (min and max).
- **events**: Configuration for randomly generated events.
- **players**: Configuration for randomly generated players.
  - **job**: Player’s profession, such as carpenter or miner.

#### **Other Configuration**

Other configurations besides the above.

```json
{
  "max_length": 120,
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
  ],
  
}
```

- **max_length**: The maximum running step of the task.
- **post_update**: Defines the game rules for the task. The `function` is selected from the post-processing functions in the environment and is located in the file. You can choose to define these post-processing functions yourself to form a new game. `Kwargs` are the parameters required by the game. Taking the minigame contract as an example, the "split_score_to_group" function is added with the parameter "division_weight". Its function is that the group allocates rewards to the agents in the group. The allocation rules are decided according to the value of "division_weight".
- **pre_updates**: Similar to `post_update`, defines the game rule before the actions are executed in each step. 

## Common configuration
### Job Configuration

The job configuration file defines the field of view for different professions and the initial and maximum capacity of their inventory. Below is an example configuration of [job.json](./common/job.json):

```json
{
  "carpenter": {
    "fov": 3,
    "inventory": {
      "size": 200,
      "init": [],
      "max": {
        "wood": 100,
        "stone": 100,
        "hammer": 1
      },
      "score": {
        "wood": 1,
        "stone": 1,
        "hammer": 5
      }
    }
  },
  "miner": {
    "fov": 2,
    "inventory": {
      "size": 100,
      "init": [
        {
          "name": "hammer",
          "num": 1
        }
      ],
      "max": {
        "hammer": 100
      },
      "score": {
        "hammer": 10
      }
    }
  }
}
```

- **fov**: Defines the field of view.
- **inventory**: Configuration of the inventory.
  - **size**: Total capacity of the inventory.
  - **init**: Initial list of items.
  - **max**: Maximum capacity for each item.
- **score**: Score for each item.

### **Resource Configuration**

The resource configuration file defines the types of various resources and their objective scores. Below is an example configuration of [resource.json](./common/resource.json):

```json
{
  "wood": {
    "type": "natural",
    "score": 1
  },
  "stone": {
    "type": "natural",
    "score": 1
  },
  "hammer": {
    "type": "synthetic",
    "score": 5
  },
  "coal": {
    "type": "natural",
    "requirements": {"hammer": 1},
    "score": 2
  }
}
```

- **type**: The type of resource (natural or synthetic).
- **score**: The score of the resource.
- **requirements**: The prerequisites for acquiring the resource (optional).

### **Event Configuration**

The event configuration file defines various events in the game and their input and output resources. Below is an example configuration of [event.json](./common/event.json):

```json
{
  "hammer_craft": {
    "in": {"wood": 1, "stone": 1},
    "out": {"hammer": 1}
  },
  "torch_craft": {
    "in": {"wood": 1, "coal": 1},
    "out": {"torch": 1},
    "requirements": {"coal": 1}
  }
}
```

- **in**: The input resources and their quantities required for the event.
- **out**: The output resources and their quantities generated by the event.
- **requirements**: Additional conditions required to trigger the event (optional).
