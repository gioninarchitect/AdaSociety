## Agent and Environment Handler Implementation

In most cases, all you need to do is to implement your own `env_handler.py` and `agent.py`.

### env_handler

You can just use [`env_handler.py`](./env_handler.py) in your task, unless you would like to customize some global logic (e.g. initialize agents with special configures, add some statistic metrics, etc.). Interfaces as callback functions are listed below:

 - `on_reset`: called by the environment after `obs, info = env.reset()`, use`obs` and `info` as inputs for agents initialization;
 - `on_update`: called by the environment after taking step `obs, reward, truncated, terminated, info = env.step(action_dict)`, then each agent processes its own input from raw data to a MDP state , those states are send to trainer (e.g. RLLib) after that;
 - `on_predict`: called by the trainer after the trainer get the policy, then each agent should sample an action from the policy and return the actions to the environment;
 - `on_close`: called by the environment, some statistic functional code can be added here if you like.

### agent

You need process the observation and action of each player in the corresponding agent. A template is given in [`agent.py`](./agent.py), there are some suggested interfaces:
 - `update`: transform observations and potentially other inputs into a suitable format for learning or inference, such as a `numpy.ndarray` or `torch.tensor`; customize the reward mechanism by implementing your own reward function (the default reward, as introduced in the [main document](../../README.md),  is provided by the environment);
 - `get_state`: get the state array;
 - `get_reward`: get the reward;
 - `update_policy`: translate policy into an action or a list of actions (each action is a tuple of an action name and kwargs);
 - `get_action`: get the updated action.

Of course you can also write your own `env_handler.py` and `agent.py` and customize interfaces functions in `agent.py` in any way you like.
