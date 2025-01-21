import numpy as np
import networkx as nx

MAX_ITEM_NUM = 32767

class State:
    def __init__(self, _id, env_info, task_info):
        self._id = env_info['_id']
        self.map_size = env_info['map_size']
        self.resource_name = env_info['resource_name']
        self.resource_num = len(self.resource_name)
        self._resource2id = dict(zip(self.resource_name, range(self.resource_num)))
        self.my_resource_capacity = np.zeros((self.resource_num), dtype=np.int16)
        for resource, capacity in env_info['inventory_capacity'].items():
            self.my_resource_capacity[self._resource2id[resource]] = capacity
        self.event_list = env_info['events']
        self.player_num = env_info['player_num']
        self.obs_range = env_info['obs_range']
        self.max_length = env_info['max_length']
        self.communication_length = task_info.static.get('communication_length', 0)
        self.obs_height = self.obs_range[0]*2 + 1
        self.obs_width = self.obs_range[1]*2 + 1
        self._node2id = self.get_node_id(env_info.get('nodes', []))

        # self.obs_dict = {self._id: self.observation_space.sample()}

    def update_my_pos(self, pos):
        self._my_pos = np.array(pos)

    def _relative_pos(self, pos, ref_point):
        no_mod_pos = pos - self._my_pos + ref_point
        return no_mod_pos % np.array(self.map_size)

    def player_toarray(self, player_list, ref_point=None, obs_size=None):
        if obs_size is None:
            obs_size = np.array([self.obs_height, self.obs_width])
        if ref_point is None:
            ref_point = np.array([obs_size[0]//2, obs_size[1]//2])

        player_layer = np.zeros((1, obs_size[0], obs_size[1]), dtype=np.int16)
        player_layer[0, ref_point[0], ref_point[1]] = self._id + 1
        for player in player_list:
            x, y = self._relative_pos(player['position'], ref_point)
            if 0 <= x < obs_size[0] and 0 <= y < obs_size[1]:
                player_layer[0, x, y] = player['id'] + 1
        return player_layer
    
    def block_list_toarray(self, position_list, block_list, ref_point=None, obs_size=None):
        if obs_size is None:
            obs_size = np.array([self.obs_height, self.obs_width])
        if ref_point is None:
            ref_point = np.array([obs_size[0]//2, obs_size[1]//2])

        block_layer = np.zeros((len(position_list), self.map_size[0], self.map_size[1]), dtype=np.int16)
        for i, pos in enumerate(position_list):
            x, y = pos - self._my_pos + np.array([self.map_size[0]//2, self.map_size[1]//2])
            obs_x, obs_y = block_list[i].shape
            rows = np.arange(x - obs_x // 2, x + (obs_x + 1) // 2) % self.map_size[0]
            cols = np.arange(y - obs_y // 2, y + (obs_y + 1) // 2) % self.map_size[1]
            mesh = np.meshgrid(rows, cols)
            block_layer[i, mesh[0].T, mesh[1].T] = block_list[i]

        block_layer = np.any(block_layer > 0, axis=0).astype(np.int16)
        rows = np.arange(self.map_size[0]//2 - obs_size[0] // 2, ref_point[0] + (obs_size[0] + 1) // 2) % self.map_size[0]
        cols = np.arange(self.map_size[1]//2 - obs_size[1] // 2, ref_point[1] + (obs_size[1] + 1) // 2) % self.map_size[1]
        return block_layer[rows][:, cols]

    def event_toarray(self, event_list, ref_point=None, obs_size=None):
        if obs_size is None:
            obs_size = np.array([self.obs_height, self.obs_width])
        if ref_point is None:
            ref_point = np.array([obs_size[0]//2, obs_size[1]//2])

        event_layer = np.zeros((self.resource_num, obs_size[0], obs_size[1]), dtype=np.int16)
        for event in event_list:
            x, y = self._relative_pos(event['position'], ref_point)
            name = event['name']
            if 0 <= x < obs_size[0] and 0 <= y < obs_size[1]:
                for input_resource_name, input_resource_amount in self.event_list[name]['in'].items():
                    event_layer[self._resource2id[input_resource_name], x, y] = - input_resource_amount
                for output_resource_name, output_resource_amount in self.event_list[name]['out'].items():
                    event_layer[self._resource2id[output_resource_name], x, y] = output_resource_amount
        return event_layer

    def resource_toarray(self, resource_list, ref_point=None, obs_size=None):
        if obs_size is None:
            obs_size = np.array([self.obs_height, self.obs_width])
        if ref_point is None:
            ref_point = np.array([obs_size[0]//2, obs_size[1]//2])

        resource_layer = np.zeros((self.resource_num, obs_size[0], obs_size[1]), dtype=np.int16)
        for resource in resource_list:
            x, y = self._relative_pos(resource['position'], ref_point)
            if 0 <= x < obs_size[0] and 0 <= y < obs_size[1]:
                resource_layer[self._resource2id[resource['name']], x, y] += resource['amount']
        return resource_layer

    def inventory_toarray(self, inventory_list):
        inventory = np.zeros((self.resource_num, ), dtype=np.int16)
        for resource in inventory_list:
            inventory[self._resource2id[resource['name']]] += resource['amount']
        return inventory

    def words_toarray(self, communication_list):
        words_array = np.zeros((self.player_num, self.communication_length), dtype = np.int8)
        for comm in communication_list:
            if 'words' in comm.keys():
                from_id = comm['from']
                content = comm['words']
                words_array[from_id] = content
        return words_array

    def get_node_id(self, node_list):
        node2id = {}
        for i, node in enumerate(node_list):
            n_type = node['type']
            name = f"{n_type}_{node[n_type]['id']}"
            node2id[name] = i
        return node2id

    def social_state2adj(self, edge_list, node_list=None):
        if node_list is not None:
            self._node2id = self.get_node_id(node_list)
        node_num = len(self._node2id)
        adj_matrix = np.zeros((node_num, node_num), dtype=np.int8)
        for edge in edge_list:
            from_node = edge['from']
            from_name = f'{from_node["type"]}_{from_node["id"]}'
            from_id = self._node2id[from_name]
            to_node = edge['to']
            to_name = f'{to_node["type"]}_{to_node["id"]}'
            to_id = self._node2id[to_name]
            adj_matrix[from_id, to_id] = 1
        return adj_matrix.T

    def social_state2nx(self, edge_list):
        G = nx.DiGraph()
        for edge in edge_list:
            from_node = edge['from']
            from_name = f'{from_node["type"]}_{from_node["id"]}'
            to_node = edge['to']
            to_name = f'{to_node["type"]}_{to_node["id"]}'
            G.add_edge(from_name, to_name, **edge['attributes'])
        return G

    def process_obs(self, obs, shared_player=None, shared_block=None):
        '''
        # Original format of the observation
        obs[player.name] = {
            'grid_observation': self.get_subwindow(player.obs_range[0], player.obs_range[1], self.agents_place[i]),
            'inventory': player.inventory,
            'communication': self.Communication.board[:, i],
            'social_state': self.social_state.adj_matrix(DEFAULT_ATTRIBUTE, None),
            'time': np.array([self.steps]),
        }
        '''
        update_obs = {}
        self.update_my_pos(obs['Player']['position'])
        player_list = obs['Map']['players']
        block_list = np.array(obs['Map']['block_grids'])[np.newaxis, :, :]
        if shared_block.size > 0:
            block_list = np.concatenate((block_list,shared_block))
        event_list = obs['Map']['events']
        resource_list = obs['Map']['resources']
        position_list = [obs['Player']['position']]
        if shared_player is not None:
            for player_id in shared_player:
                # get position with id and player_list
                for ply in player_list:
                    if ply['id'] == player_id:
                        position_list.append(ply['position'])
        player_layer = self.player_toarray(player_list, obs_size=self.map_size)
        block_layer = self.block_list_toarray(position_list, block_list, obs_size=self.map_size)[np.newaxis, :, :]
        event_layer = self.event_toarray(event_list, obs_size=self.map_size)
        resource_layer = self.resource_toarray(resource_list, obs_size=self.map_size)
        update_obs['grid_observation'] = np.concatenate((player_layer, block_layer, event_layer, resource_layer),axis = 0)
        update_obs['inventory'] = self.inventory_toarray(obs['Player']['inventory'])
        update_obs['communication'] = self.words_toarray(obs['Social']['communications'])
        update_obs['social_state'] = self.social_state2adj(obs['Social']['global']['edges'])
        update_obs['time'] = np.array([obs['step_id']])
        return update_obs

    # If considering observation sharing, call this function before process_obs
    def sharing_obs(self, obs):
        shared_block = []
        shared_player = []
        for player_id in obs['Social']['sharings']:
            shared_map_info = obs['Social']['sharings'][player_id]['Map']  
            for res in shared_map_info['resources']:
                if res not in obs['Map']['resources']:
                    obs['Map']['resources'].append(res)
            for eve in shared_map_info['events']:
                if eve not in obs['Map']['events']:
                    obs['Map']['events'].append(eve)
            for ply in shared_map_info['players']:
                if ply not in obs['Map']['players']:
                    obs['Map']['players'].append(ply)
            shared_block.append(shared_map_info['block_grids'])
            shared_player.append(player_id)
        return obs, shared_player, np.asarray(shared_block)
