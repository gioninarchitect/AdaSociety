class Reward:
    def __init__(self, _id, env_info, task_info):
        self._id = _id
        
    def set_reward(self, reward):
        self.reward = reward
        
    def shape_reward(
        self,
        obs,
        reward,
        terminated,
        truncated,
        info,
    ):
        pass
        
    def get_reward(self):
        return self.reward