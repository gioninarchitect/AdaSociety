from .mdp.state import State
from .mdp.action import Action
from .mdp.reward import Reward

class Agent:
    def __init__(self, _id, env_info, task_info):
        self.state = State(_id, env_info, task_info)
        self.action = Action(_id, env_info, task_info)
        self.reward = Reward(_id, env_info, task_info)
        self.observation_space = None
        self.action_space = None


    def update(
        self,
        obs,
        reward,
        truncated,
        terminated,
        info,
    ):
        self.obs = self.update_obs(obs)
        self.update_reward(obs, reward, truncated, terminated, info)
        self.truncated = truncated
        self.terminated = terminated
        self.info = info

    def update_obs(
        self,
        obs
    ):
        raise NotImplementedError
        
    def update_policy(
        self,
        policy,
    ):
        raise NotImplementedError
                
    def update_reward(
        self,
        obs,
        reward,
        truncated,
        terminated,
        info,
    ):
        raise NotImplementedError

    def get_state(self):
        return self.obs

    def get_reward(self):
        return self.reward.get_reward()

    def get_action(self):
        return self.action.get_action()