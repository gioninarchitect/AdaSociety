import numpy as np
from .mdp.state import State
from .mdp.action import Action
from .mdp.reward import Reward
from gymnasium.spaces import Discrete

class NegotiationAgent:
    def __init__(self, _id, env_info, task_info):
        self._id = env_info['_id']
        self.claim_proposal_interval = task_info.negotiation['claim_proposal_interval']
        self.resource_name = env_info['resource_name']
        self.resource_num = len(self.resource_name)
        self.player_num = env_info['player_num']
        env_info['negotiation_length'] = self.player_num + 2 + self.claim_proposal_interval
        self.state = State(_id, env_info, task_info)
        self.action = Action(_id, env_info, task_info)
        self.reward = Reward(_id, env_info)
        self.observation_space = self.state.observation_space
        self.action_num = 6 + 2 * self.resource_num + self.player_num + 2 + self.claim_proposal_interval
        self.action_space = Discrete(self.action_num)
        
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
        # self.info = info

    def update_obs(
        self,
        obs,
    ):
        self.origin_obs = obs
        return self.state.update(obs)

    def update_policy(
        self,
        policy  
    ):
        """
        self.action.update(policy)
        """
        action_index = policy
        self.action.new()
        actions = [
            (lambda x: 0 <= x < 5, self.action.move_action),
            (lambda x: x == 5, self.action.produce_action),
            (lambda x: 6 <= x < 6 + self.resource_num, self.action.pick_action),
            (lambda x: 6 + self.resource_num <= x < 6 + 2 * self.resource_num, self.action.dump_action),
            (lambda x: 6 + 2 * self.resource_num <= x < 6 + 2 * self.resource_num + self.player_num, self.action.request_matching_action),
            (lambda x: 6 + 2 * self.resource_num + self.player_num <= x, self.action.bargain_action),
        ]
        action_type = None
        for condition, action_func in actions:
            if condition(action_index):
                if action_func == self.action.bargain_action:
                    bargaining_player_id = self._get_bargaining_player()
                    opponene_proposal = self._get_opponent_proposal(opponent_player_id=bargaining_player_id)
                    action_type = action_func(action_index, bargaining_player_id, opponene_proposal)
                else:
                    action_type = action_func(action_index)
                break
        self.action_type = action_type

    def update_reward(
        self,
        obs,
        reward,
        truncated,
        terminated,
        info,
    ):
        self.reward.set_reward(reward)

    def get_state(self):
        return self.obs
        # return self.state.get_state()

    def get_reward(self):
        return self.reward.get_reward()

    def get_action(self):
        return self.action.get_action()
    
    def _get_bargaining_player(self):
        graph = self.origin_obs['Social']['social_graph']
        for u, v, edge in graph.edges(data=True):
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            if u_data['type'] == 'player' and v_data['type'] == 'player' and u_data['id'] == self._id:
                if 'parity' in edge:
                    return v_data['id']
                
    def _get_opponent_proposal(self, opponent_player_id):
        graph = self.origin_obs['Social']['social_graph']
        for u, v, edge in graph.edges(data=True):
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            if u_data['type'] == 'player' and v_data['type'] == 'player':
                if u_data['id'] == self._id and v_data['id'] == opponent_player_id:
                    opponent_proposal = graph[v][u].get('proposal')
                    return opponent_proposal
        return None
   
