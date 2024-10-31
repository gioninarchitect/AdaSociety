# *Negotiation*
## Overview
In the *Negotiation* mini-game, agents can reach reward distribution agreements by sending cooperation requests and bargaining with other co-players. These agreements then determine the distribution of benefits from subsequent actions such as resource gathering and tool synthesis.
## Game Rule
The game is divided into two sequential phases: the negotiation phase and the physical phase.
### Negotiation phase
During the negotiation phase, agents can choose a target player to send a cooperation request to. If two players simultaneously send requests to each other, they will enter the bargaining phase. In this phase, both parties take turns to act, with three types of actions available: making a new proposal, accepting the opponent’s proposal, or ending the current bargaining round. If either party chooses to accept or end, both of them then exit the bargaining process and can continue seeking cooperation with other players. The negotiation phase lasts for  `negotiation_steps`, which can be customized in [negotiation.json](../../../config/task/negotiation.json).
- **Observation space:** In **Negotiation** mini-task, the observation information returned by the environment to each agent is processed in [state.py](../negotiation/agent/mdp/state.py), resulting in the following fields of information:
    - **grid_observation**: Map information, including player positions, resources, and events on the map.
    - **inventory**: resources' names and amounts in the player's inventory.
    - **proposal**: The opponent's proposal regarding reward distribution, such as the opponent requesting to receive 60% of the share.
    - **final_split**: The distribution agreement that has already been reached in the current environment.
    - **available_player**: Players who can receive matching requests.
    - **social_state**: The current social connections between all players.
    - **time**: The current timestep.
    - **player_id**: The player's id.
    - **action_mask**: The current available actions can be taken by the player.

- **Action space:** During the negotiation phase, agents can only choose `request_matching_action` and `bargain_action` defined in [action.py](../negotiation/agent/mdp/action.py). Here are the discriptions of them:
    - `request_matching_action`: Choose another player to send a matching request. When both platters send requests to each other at the same timestep, they enter the bargaining phase.
    - `bargain_action`: There are three types of bargaining actions:
        - **accept_proposal**: Accept the other's proposal at the last step.
        - **end_bargaining**: End this bargaining.
        - **propose**: Make a new proposal. A reward distribution scheme needs to be specified, where `score` is a float between 0 and 1, representing the proportion of the reward that one wants to receive.
    The above two types of actions will lead to changes in the attributes of edges between players in the social graph. For example, the `request_matching_action` will create an edge pointing to the other player with a key of *matching_request_step* and a value of the current step. The implementation details of other actions can be found in [player.py](../../env/player.py). These attribute changes are evaluated and further processed during the environment's post-processing phase, after all players have taken their actions.

- **Post update:** The post update for **Negotiation** is set in [negotiation.json](../../../config/task/negotiation.json):

```json
    "post_updates":[
        {
            "function": "matching_edge",
            "kwargs":{
            "condition_attr": "matching_request_step",
            "result_attr1": {
                "parity": 0
            },
            "result_attr2": {
                "parity": 1
            }
            }
        },
        {
            "function": "merge_relation_to_group",
            "kwargs":{
            "condition_attr": "accept",
            "result_attr": "score"
            }
        },
        {
            "function": "normalization",
            "kwargs":{
            "attr": "score"
            }
        },
        {
            "function": "clear_temporary_relation",
            "kwargs":{
            "attr": "matching_request_step"
            }
        },
        {
            "function": "split_score_to_group",
            "kwargs": {
            "attribute": "score"
            }
        }
    ]
```
Here is an introduction to each function:
- **matching_edge**: The determination of whether both parties sent requests to each other simultaneously is based on whether their `matching_request_step` values are equal. If a match is successful, a directed edge is created between them with a `parity` of 0 and 1, respectively. This parity is based on the odd or even nature of the current step and will determine the order of actions during their subsequent bargaining.
- **merge_relation_to_group**: If a player chooses to accept the opponent's proposal, the function will create a group node that connects both players. The `score` on the edge between the group and the player represents the proportion of the reward that the player can receive from the group. If a player is already in a group, the function will perform a group merge operation and determine the reward distribution scheme according to the calculations outlined in the paper.
- **normalization**: This function ensures that the sum of the score values on the edges from a group to all its players equals 1.
- **clear_temporary_relation**: Since the matching operation is only effective for the current step, it is important to clear `matching_request_step` after each round to avoid redundant information.
- **split_score_to_group**: Each group allocates score to each player according to the reward distribution scheme agreed upon in the negotiation.

### Physical phase
During the physical phase, all players act simultaneously within the physical environment, and the rewards for each step are distributed according to the agreements reached during the negotiation phase. The physical phase lasts for `max_length` - `negotiation_steps`.
- **Action space:** During the physical phase, agents can choose from the following actions defined in [action.py](../negotiation/agent/mdp/action.py):
    - `move_action`: Move up, down, left, right or stay.
    - `produce_action`: The produce action on an Event.
    - `pick_action`: Pick up resources in the map.
    - `dump_action`: Dump resources in the inventory.

## Implement Agent in [`agent.py`](./agent/agent.py)
Based on the template given in [`agent.py`](../../agent/agent.py), we implement `NegotiationAgent`. We explain some key functions:
- `__init__`: Init **Negotiation** agent with environment information and task specific information. Define the observation space and action space based on task description.

- `update`: Get observation, reward, and other information from the environment and process with `update_obs` and `update_reward` functions.

- `update_obs`: Translate the received observation into task-specific observation format.

- `update_policy`: Translate policy into actions.

There is an another important function `_get_action_mask` in [mdp/state.py](../negotiation/agent/mdp/state.py) that determines the actions an agent can take in the current step based on the current map information, inventory, and social status. Here are the rules:

- `negotiation phase`: This phase is further divided into a matching phase and a bargaining phase, with each phase allowing only the corresponding actions to be taken:
    - `request_matching_action`: When inviting other players, two conditions must be met: first, you cannot invite players who are already engaged in any bargaining process, as this would cause conflicts when bargaining with multiple players simultaneously. Second, you cannot renegotiate with players who have already formed an agreement.
    - `bargain_action`: The first action taken by both parties in a bargaining process must be to `propose`. After that, when it’s a player's turn to act, they are free to choose between `accept`, `end`, or `propose`, while the other party must choose `no_act` for that turn.

- `physical phase`: In the physical phase, agents are not allowed to take actions that violate environmental rules. For example, an agent cannot use the `pick` action at a location with no resources, is not permitted to `dump` items that are not in their inventory, and cannot use the `produce` action if the items in their inventory do not meet the requirements.