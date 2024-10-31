# from .agent import Agent
from ..utils.config_loader import ConfigLoader 
from pydoc import locate

class EnvHandler:
    def __init__(self, config_name='./config/main.json'):
        self.config_loader = ConfigLoader(config_name)
        self.AgentClass = locate(self.config_loader.task['agent'])
        self.agent_dict: dict[str, self.AgentClass] = {}

    def on_reset(
        self,
        observations,
        infos,
    ):
        for _id, obs in observations.items():
            self.agent_dict[_id] = self.AgentClass(
                _id=_id,
                env_info=infos[_id],
                task_info=self.config_loader.config.task,
            )

    def on_update(
        self,
        observations,
        rewards={},
        terminateds={},
        truncateds={},
        infos={},
    ):
        state_dict = {}
        for _id, obs in observations.items():
            reward = rewards.get(_id, 0)
            terminated = terminateds.get(_id, False)
            truncated = truncateds.get(_id, False)
            info = infos.get(_id)
            agent = self.agent_dict[_id]
            agent.update(
                obs,
                reward,
                truncated,
                terminated,
                info,   
            )
            state_dict[_id] = agent.get_state()
        reward_dict = rewards
        terminated_dict = terminateds
        truncated_dict = truncateds
        info_dict = infos
        return state_dict, reward_dict, terminated_dict, truncated_dict, {}

    def on_predict(self, policy_dict):
        action_dict = {}
        for _id, policy in policy_dict.items():
            agent = self.agent_dict[_id]
            agent.update_policy(policy)
            action_dict[_id] = agent.get_action()
        return action_dict

    def on_close(self):
        return