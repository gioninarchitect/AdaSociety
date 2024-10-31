from ....agent.mdp.state import State
from ....agent.mdp.action import Action
from ....agent.mdp.reward import Reward
from gymnasium.spaces import Box, Discrete, Dict
import numpy as np

MAX_ITEM_NUM = 32767
WEIGHT = 'division_weight'

class ExplorationAgent:
    def __init__(self, _id, env_info, task_info):
        self.state = State(_id, env_info, task_info)
        self.reward = Reward(_id, env_info, task_info)
        self.action = Action(_id, env_info, task_info)
        self.group_id = None
        self.group_num = env_info['group_num']
        self.action_dim = 6 + 2 * self.state.resource_num + 2 * self.state.player_num + self.group_num
        self.observation_space = self.observation_space = Dict({
                'grid_observation': Box(
                    -MAX_ITEM_NUM,
                    MAX_ITEM_NUM,
                    (2+self.state.resource_num*2, self.state.map_size[0], self.state.map_size[1]),
                    dtype=np.int16
                ),
                'inventory': Box(0, MAX_ITEM_NUM, (self.state.resource_num,), dtype=np.int16),
                'communication': Box(0, 1, (self.state.player_num, self.state.communication_length), dtype=np.int8),
                'social_state': Box(0, 1, (self.state.player_num + self.group_num, self.state.player_num + self.group_num), dtype=np.int8),
                'time': Box(0, self.state.max_length, (1,), dtype=np.int16),
                'player_id': Box(0, 1, (self.state.player_num + self.group_num,), dtype=np.int8),
                'action_mask': Box(0,1, (self.action_dim,),dtype=np.int8)
            })
        self.action_space = Discrete(self.action_dim)
        self.social_graph_edges = None

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
        update_obs = {}
        shared_obs, sharing_player, sharing_block = self.state.sharing_obs(obs)
        update_obs = self.state.process_obs(shared_obs, sharing_player, sharing_block)
        update_obs['player_id'] = np.zeros((self.state.player_num + self.group_num), dtype=np.int8)
        update_obs['player_id'][self.state._id] = 1
        update_obs['action_mask'] = self.get_action_mask(update_obs['grid_observation'], update_obs['inventory'])
        self.social_graph_edges = obs['Social']['global']['edges']
        return update_obs
    
    def update_policy(
        self,
        policy,
    ):
        if isinstance(policy, (int, np.integer)):
            _action_id = policy
        elif len(policy) == 1:
            _action_id = int(policy[0])
        else:
            _action_id = np.argmax(policy)

        self.action.new()
        if _action_id < 5:
            self.action.move_action(_action_id)
        elif _action_id == 5:
            self.action.produce_action()
        elif 6 <= _action_id < 6 + self.state.resource_num:
            self.action.pick_action(_action_id - 6)
        elif 6 + self.state.resource_num <= _action_id < 6 + 2 * self.state.resource_num:
            self.action.dump_action(_action_id - 6 - self.state.resource_num)
        elif 6 + 2 * self.state.resource_num <= _action_id < 6 + 2 * self.state.resource_num + self.state.player_num:
            tempzero=np.zeros((self.state.communication_length,), dtype=np.float32)
            self.action.communication_action(_action_id - 6 - 2 * self.state.resource_num, tempzero)
        elif 6 + 2 * self.state.resource_num + self.state.player_num <= _action_id < 6 + 2 * self.state.resource_num + 2 * self.state.player_num:
            to_player_id = _action_id - 6 - 2 * self.state.resource_num - self.state.player_num
            if self.check_share_relation(to_player_id):
                self.action.remove_relation_action(to_player_id, 'sharing')
            else:
                self.action.add_relation_action(to_player_id, {'sharing': {'Map': True}})
        elif 6 + 2 * self.state.resource_num + 2 * self.state.player_num <= _action_id < 6 + 2 * self.state.resource_num + 2 * self.state.player_num + self.group_num:
            if self.group_id is not None:
                self.action.quit_group_action(self.group_id, WEIGHT)
                self.action.join_group_action(_action_id - 6 - 2 * self.state.resource_num - 2 * self.state.player_num, {WEIGHT: 1})
            else:
                self.action.join_group_action(_action_id - 6 - 2 * self.state.resource_num - 2 * self.state.player_num, {WEIGHT: 1})
            self.group_id = _action_id - 6 - 2 * self.state.resource_num - 2 * self.state.player_num

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

    def get_action_mask(self, grid_obs, inventory):
        action_mask = np.zeros(self.action_dim)
        player_layer = grid_obs[0]
        my_pos = np.where(player_layer == self.state._id + 1)
        my_pos = np.array([my_pos[0][0], my_pos[1][0]])
        event_here = grid_obs[2: 2 + self.state.resource_num, my_pos[0], my_pos[1]]
        resource_here = grid_obs[2 + self.state.resource_num: 2 + 2 * self.state.resource_num, my_pos[0], my_pos[1]]
        pick_mask = np.logical_and(resource_here > 0, inventory < self.state.my_resource_capacity).astype(np.int8)
        dump_mask = (inventory > 0).astype(np.int8)
        action_mask[:5] = 1
        if np.any(event_here) and (event_here + inventory <= self.state.my_resource_capacity).all():
            action_mask[5] = 1
        action_mask[6: 6 + self.state.resource_num] = pick_mask
        action_mask[6 + self.state.resource_num: 6 + 2 * self.state.resource_num] = dump_mask
        action_mask[-(2 * self.state.player_num + self.group_num):] = 1
        return action_mask
    
    def check_share_relation(self, to_player_id):
        for edge in self.social_graph_edges:
            if edge['from']['type'] == 'player' and edge['from']['id'] == self.state._id:
                if edge['to']['type'] == 'player' and edge['to']['id'] == to_player_id:
                    if 'sharing' in edge['attributes'].keys():
                        return edge['attributes']['sharing'].get('Map', False)
        return False