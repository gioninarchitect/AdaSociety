# from ...env.fake_env import MultiAgentEnvironment
from ...env.environment import Environment
from ...agent.env_handler import EnvHandler
from ray.rllib.env.multi_agent_env import MultiAgentEnv
from gymnasium.spaces import Box


class LLMEnvWrapper(MultiAgentEnv):
    def __init__(self) -> None:
        self.env = Environment('./config/main.json')
        self.env_handler = EnvHandler()
        
    def reset(self, *, seed=None, options=None):
        obs, info = self.env.reset()
        return obs, info
    
    def step(self, actions):
        obs, reward, terminated, truncated, info = self.env.step(actions)
        return obs, reward, terminated, truncated, info