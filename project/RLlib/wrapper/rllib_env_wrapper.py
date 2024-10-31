from ...env.environment import Environment
from ray.rllib.env.multi_agent_env import MultiAgentEnv
from gymnasium.spaces import Box
from pydoc import locate

class RllibEnvWrapper(MultiAgentEnv):
    def __init__(self, config) -> None:
        self.env = Environment(config['env_dir'])
        EnvHandler = locate(self.env.config_loader.task['env_handler'])
        self.env_handler = EnvHandler(config['env_dir'])
        self.get_spaces()

    def reset(self, *, seed=None, options=None):
        obs, info = self.env.reset()
        self.env_handler.on_reset(obs, info)
        obs_dict, _, _, _, info_dict = self.env_handler.on_update(obs, {}, {}, {}, info)
        return obs_dict, info_dict

    def step(self, actions):
        actions = self.env_handler.on_predict(actions)
        obs, reward, terminated, truncated, info = self.env.step(actions)
        obs, reward, terminated, truncated, info = self.env_handler.on_update(obs, reward, terminated, truncated, info)
        return obs, reward, terminated, truncated, info

    def get_spaces(self):
        dummy_env = Environment()
        obs, info = dummy_env.reset()
        self.env_handler.on_reset(obs, info)
        self.observation_space = {
            _id: agent.observation_space for _id, agent in self.env_handler.agent_dict.items()
        }
        self.action_space = {
            _id: agent.action_space for _id, agent in self.env_handler.agent_dict.items()
        }

def get_spaces_and_model_config(dummy_env: MultiAgentEnv, args):
    observation_space = dummy_env.observation_space
    action_space = dummy_env.action_space
    model_config_dict = {}
    for player, Dict_space in observation_space.items():
        model_config_dict[player] = {}
        dict_space = dict(Dict_space)
        for name, space in dict_space.items():
            assert isinstance(space, Box), 'space should be a gymnasium.Box'
            model_config_dict[player][name + '_shape'] = space.shape
        model_config_dict[player]['lstm_state_size'] = args.lstm_state_size
        model_config_dict[player]['select_group'] = args.select_group
        model_config_dict[player]['group_num'] = len(dummy_env.env.config_loader.config.task.static.social.groups)
        model_config_dict[player]['player_num'] = len(observation_space)
    return model_config_dict, observation_space, action_space