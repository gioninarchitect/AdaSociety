from gymnasium.spaces import Discrete, Box, Dict
import numpy as np

import networkx as nx

MAX_ITEM_NUM = 32767

class State:
    def __init__(self, _id, env_info, task_info):
        self._id = env_info['_id']
        self.map_size = env_info['map_size']
        self.all_events = env_info['events']
        self.resource_name = env_info['resource_name']
        self.resource_num = len(self.resource_name)
        self._resource2id = dict(zip(self.resource_name, range(self.resource_num)))
        self.player_num = env_info['player_num']
        self.obs_range = env_info['obs_range']
        self.my_resource_capacity = np.zeros((self.resource_num), dtype=np.int16)
        for resource, capacity in env_info['inventory_capacity'].items():
            self.my_resource_capacity[self._resource2id[resource]] = capacity
        self.group_num = env_info['group_num']
        self.terminated_point = env_info['max_length']
        self.negotiation_steps = task_info.negotiation['negotiation_steps']
        self.claim_proposal_interval = task_info.negotiation['claim_proposal_interval']
        self.action_num = 6 + 2 * self.resource_num + self.player_num + 2 + self.claim_proposal_interval
        self.physical_action_num = 6 + 2 * self.resource_num
        self.negotiation_action_num = self.player_num + 2 + self.claim_proposal_interval
        self.obs_height = self.obs_range[0]*2 + 1
        self.obs_width = self.obs_range[1]*2 + 1
        self.ref_point = [self.obs_range[0], self.obs_range[1]]

        self.observation_space = Dict({
            'grid_observation': Box(
                -MAX_ITEM_NUM,
                MAX_ITEM_NUM,
                (2+self.resource_num*2, self.obs_height, self.obs_width),
                dtype=np.int16
            ),
            'inventory': Box(0, MAX_ITEM_NUM, (self.resource_num,), dtype=np.int16),
            # 'communication': Box(0, 1, (self.player_num, self.communication_length), dtype=np.int8),
            'proposal': Box(0, 1, (self.player_num,), dtype=np.float16),
            'final_split': Box(0, 1, (self.player_num, ), dtype=np.float16),
            'available_player': Box(0, 1, (self.player_num, ), dtype=np.int8),
            'social_state': Box(0, 1, (self.player_num, self.player_num), dtype=np.int8),
            'time': Box(0, self.terminated_point, (1,), dtype=np.int16),
            'player_id': Box(0, 1, (self.player_num,), dtype=np.int8),
            'action_mask': Box(0,1, (self.action_num,),dtype=np.int8)
        })

        self.obs_dict = self.observation_space.sample()

    def update(self, obs):
        self._my_pos = obs['Player']['position']
        ''' grid_observation '''
        ### player layer ###
        player_dict = obs['Map']['players']
        player_layer = np.zeros((1, self.obs_height, self.obs_width), dtype=np.int16)
        for player in player_dict:
            x, y = self._relative_pos(player['position'])
            player_layer[0, x, y] = player['id'] + 1
        player_layer[0, self.ref_point[0], self.ref_point[1]] = self._id + 1

        ### block layer ###
        block_layer = np.zeros((1, self.obs_height, self.obs_width), dtype=np.int16)
        block_layer[0] = obs['Map']['block_grids']

        ### event layer ###
        event_dict = obs['Map']['events']
        event_layer = np.zeros((self.resource_num, self.obs_height, self.obs_width), dtype=np.int16)
        for event in event_dict:
            event_name = event['name']
            event_class = self.all_events[event_name]
            event_relative_pos = self._relative_pos(event['position'])
            for input_resource_name, input_resource_amount in event_class['in'].items():
                event_layer[
                        self._resource2id[input_resource_name], 
                        event_relative_pos[0],
                        event_relative_pos[1]
                    ] = - input_resource_amount
            for output_resource_name, output_resource_amount in event_class['out'].items():
                event_layer[
                        self._resource2id[output_resource_name],
                        event_relative_pos[0],
                        event_relative_pos[1]
                    ] = output_resource_amount

        ### resource layer ###
        resource_dict = obs['Map']['resources']
        resource_layer = np.zeros((self.resource_num, self.obs_height, self.obs_width), dtype=np.int16)
        for resource in resource_dict:
            resource_relative_pos = self._relative_pos(resource['position'])
            resource_layer[
                    self._resource2id[resource['name']], 
                    resource_relative_pos[0],
                    resource_relative_pos[1]
                  ] = resource['amount']

        self.obs_dict['grid_observation'] = np.concatenate((player_layer, block_layer, event_layer, resource_layer))

        ''' inventory '''
        inventory = np.zeros((self.resource_num, ), dtype=np.int16)
        for resource in obs['Player']['inventory']:
            inventory[self._resource2id[resource['name']]] += resource['amount']
        self.obs_dict['inventory'] = inventory

        ''' social_state '''
        social_graph = obs['Social']['social_graph']
        self.obs_dict['social_state'] = self._get_player_adjacency_matrix(social_graph)

        ''' time '''
        self.obs_dict['time'].fill(0)
        self.obs_dict['time'][0] = obs['step_id']

        ''' player_id '''
        self.obs_dict['player_id'].fill(0)
        self.obs_dict['player_id'][self._id] = 1

        ''' action_mask '''
        action_mask = self._get_action_mask(obs['Social']['social_graph'], obs['step_id'], self.obs_dict['grid_observation'], self.obs_dict['inventory'])
        # print(f"action mask: {action_mask}")
        self.obs_dict['action_mask'] = action_mask

        ''' negotiation info '''
        ### available player ###
        available_players = np.zeros(self.player_num, dtype=np.int8)
        invitable_players = self._find_invitable_players(social_graph, self._id)
        for invitable_players_id in invitable_players:
            available_players[invitable_players_id] = 1
        self.obs_dict['available_player'] = available_players

        ### proposal ###
        proposal = np.zeros((self.player_num, ), dtype=np.float16)
        for communication in obs['Social']['communications']:
            if 'score' in communication['Request'] and communication['Request']['scores'] is not None:
                score = communication['Request']['scores']
                proposal[communication['from']] = score
                proposal[self._id] = 1 - score
                break
        self.obs_dict['proposal'] = proposal

        ### final split ###
        final_split = self._find_final_split(social_graph)
        # print(f"final split: {final_split}")
        self.obs_dict['final_split'] = final_split
        return self.obs_dict

    def _relative_pos(self, pos):
        return (np.array(pos) - np.array(self._my_pos) + np.array(self.ref_point)) % np.array(self.map_size)
    
    
    def _get_player_adjacency_matrix(self, social_graph):
        adjacency_matrix = np.zeros((self.player_num, self.player_num), dtype=np.int16)
        player_groups = {}
        for player in social_graph.nodes:
            if social_graph.nodes[player]['type'] == 'player':
                player_id = social_graph.nodes[player]['id']
                belong_group = player.groups
                player_groups[player_id] = belong_group
        for i in range(self.player_num):
            for j in range(i + 1, self.player_num):
                if player_groups[i] == player_groups[j] and len(player_groups[i]) > 0:
                    adjacency_matrix[i][j] = 1
                    adjacency_matrix[j][i] = 1
        return adjacency_matrix
    
    # don't delete, llm needs.
    def social_state2nx(self, edge_list):
        G = nx.DiGraph()
        for edge in edge_list:
            from_node = edge['from']
            from_name = f'{from_node["type"]}_{from_node["id"]}'
            to_node = edge['to']
            to_name = f'{to_node["type"]}_{to_node["id"]}'
            G.add_edge(from_name, to_name, **edge['attributes'])
        return G
    
    def inventory_toarray(self, inventory_list):
        inventory = np.zeros((self.resource_num, ), dtype=np.int16)
        for resource in inventory_list:
            inventory[self._resource2id[resource['name']]] += resource['amount']
        return inventory
    
    def _get_action_mask(self, social_graph, time, grid_obs, inventory):
        # edge_list = self.origin_obs['Social']['global']['edges']
        action_mask = np.zeros((self.action_num), dtype=np.int8)
            
        if time <= self.negotiation_steps:
            invitable_players = self._find_invitable_players(social_graph, self._id)
            for invitable_players_id in invitable_players:
                action_mask[self.physical_action_num+invitable_players_id] = 1
            for u, v, edge in social_graph.edges(data=True):
                u_data = social_graph.nodes[u]
                v_data = social_graph.nodes[v]
                if u_data['type'] == 'player' and v_data['type'] == 'player' and u_data['id'] == self._id:
                    if 'parity' in edge: # bargaining
                        action_mask.fill(0)
                        if time % 2 == edge['parity']: # take turn
                            if 'proposal' not in edge and 'proposal' not in social_graph[v][u]: # must make a new proposal
                                action_mask[self.physical_action_num+self.player_num + 2 : ] = 1
                            else: # can choose accept/end/reject(new proposal)
                                action_mask[self.physical_action_num+self.player_num:] = 1
                        else: # not turn
                            action_mask[4] = 1 # no_act
        else:
            player_layer = grid_obs[0]
            my_pos = np.where(player_layer == self._id + 1)
            my_pos = np.array([my_pos[0][0], my_pos[1][0]])
            event_here = grid_obs[2: 2 + self.resource_num, my_pos[0], my_pos[1]]
            resource_here = grid_obs[2 + self.resource_num: 2 + 2 * self.resource_num, my_pos[0], my_pos[1]]
            pick_mask = np.logical_and(resource_here > 0, inventory < self.my_resource_capacity).astype(np.int8)
            dump_mask = (inventory > 0).astype(np.int8)
            action_mask[:5] = 1
            if np.any(event_here) and (event_here + inventory <= self.my_resource_capacity).all():
                action_mask[5] = 1
            action_mask[6: 6 + self.resource_num] = pick_mask
            action_mask[6 + self.resource_num: 6 + 2 * self.resource_num] = dump_mask
        
        if np.sum(action_mask) == 0:
            action_mask[4] = 1
        return action_mask
                        
    def _find_invitable_players(self, graph, player_id):
        invitable_players = []
        target_player = None
        for node, data in graph.nodes(data=True):
            if data.get('id') == player_id and data.get('type') == 'player':
                target_player = node
                break
        if target_player is None:
            raise ValueError(f"Player with id {player_id} not found in the graph.")
        target_groups = set()
        for neighbor in graph.predecessors(target_player):
            if graph.nodes[neighbor].get('type') == 'group':
                target_groups.add(neighbor)

        for node, data in graph.nodes(data=True):
            if data.get('type') == 'player' and node != target_player:
                shared_group = False
                for neighbor in graph.predecessors(node):
                    if neighbor in target_groups:
                        shared_group = True
                        break
                if shared_group:
                    continue

                has_parity_edge = False
                for u, v, edge_data in graph.edges(node, data=True):
                    if 'parity' in edge_data:
                        has_parity_edge = True
                        break
                if has_parity_edge:
                    continue
                invitable_players.append(data['id'])
        return invitable_players           

    def _find_final_split(self, graph):
        final_split = np.ones((self.player_num, ), dtype=np.float16)
        for node in graph.nodes:
            if graph.nodes[node]['type'] == 'player':
                for group, _, edge_data in graph.in_edges(node, data=True):
                    if graph.nodes[group]['type'] == 'group':
                        player_id = graph.nodes[node]['id']
                        final_split[player_id] = edge_data['score']
        return final_split