import random
import networkx as nx
import numpy as np
import json
from ..utils.json_encoder import NumpyEncoder


class Game:
    def __init__(
        self,
        world_map,
        resources,
        events,
        players,
        social,
        social_schedule,
        negotiation_steps,
        pre_updates,
        post_updates,
        max_length
    ):
        # Map
        self.world_map = world_map
        # Resource
        self.resource_dict = {}
        self.resources = resources
        for resource in resources:
            self.lay_resource(resource)
        # Players {'player_id': Player(), ...}
        self.players = players
        self.player_dict = {player._id: player for player in players}
        self.player_name2id = {player.name: player._id for player in players}
        self.update_position_dict()
        for player in self.players:
            player.join_game(self)
        self.player_num = len(self.players)
        # Social
        self.social = social
        self.social_schedule = social_schedule
        self.milestones = sorted([int(key) for key in social_schedule.keys()])
        self.negotiation_steps = negotiation_steps
        # Events
        self.events = events
        self.event_dict = {event.position: event for event in events}

        self.steps = 0
        self.episodes = 0
        self.max_length = max_length
        # Observations
        self._obs = self._get_obs()
        # Rewards
        self.rewards = self._get_rewards()
        # Terminateds
        self.terminated = False

        self._pre_update_funcs = {
            'symmetrize_relation': self._post_symmetrize_relation,
            'matching_edge': self._post_update_matching_edge,
            'relation_to_group': self._post_update_relation_to_group,
            'merge_relation_to_group': self._post_update_merge_relation_to_group,
            'relation_switch': self._post_update_relation_switch,
            'merge_group':self._post_merge_group,
            'normalization':self._post_normalization,
            'clear_temporary_relation':self._post_clear_temporary_relation,
            'split_score_to_group': self._post_update_split_score_to_group,
        }

        self._post_update_funcs = {
            'symmetrize_relation': self._post_symmetrize_relation,
            'matching_edge': self._post_update_matching_edge,
            'relation_to_group': self._post_update_relation_to_group,
            'merge_relation_to_group': self._post_update_merge_relation_to_group,
            'relation_switch': self._post_update_relation_switch,
            'merge_group':self._post_merge_group,
            'normalization':self._post_normalization,
            'clear_temporary_relation':self._post_clear_temporary_relation,
            'split_score_to_group': self._post_update_split_score_to_group,
        }
        self.social_pre_update = self.load_func(pre_updates, self._pre_update_funcs)
        self.social_post_update = self.load_func(post_updates, self._post_update_funcs)

    @property
    def observations(self):
        return self._obs
    
    def pre_update(self):
        for player in self.players:
            player.pre_update()
        self.social_pre_update()

    def update(self, action_dict):
        # Events
        for event in self.event_dict.values():
            event.update()
        # Players: update
        for player_name, action in action_dict.items():
            player_id = self.player_name2id[player_name]
            player = self.player_dict[player_id]
            player.update(action)
        # Collision
        self.collision_check()
        self.update_position_dict()

    def post_update(self):
        # Players: post update
        for player in self.players:
            player.post_update()
        self.update_position_dict()
        # Time
        self.steps += 1
        # Social
        self.social_post_update()
        self.check_social_schedule()
        # Observation
        self._obs = self._get_obs()
        # Rewards
        self.rewards = self._get_rewards()
        # print(f"Reward: {self.rewards}")
        # Terminateds
        self.terminateds = self._get_terminateds()

    def bubble_up_resource(self, position, resource_name):
        resource = self.resource_dict.get(position)
        if resource:
            top_resource = resource
            if resource.name == resource_name:
                return resource
            next_resource = resource.stacked_resource
            while next_resource:
                if next_resource.name == resource_name:
                    resource.stacked_resource = next_resource.stacked_resource
                    next_resource.stacked_resource = top_resource
                    self.resource_dict[position] = next_resource
                    return next_resource
                resource = next_resource
                next_resource = resource.stacked_resource
        return None

    def provide_resource(self, position, require_num=1):
        resource = self.resource_dict.get(position)
        if resource:
            obtained_resource = resource.provide(require_num)
            
            if not resource.is_available:
                if resource.stacked_resource:
                    self.resource_dict[position] = resource.stacked_resource
                else:
                    del self.resource_dict[position]
            return obtained_resource
        return None

    def lay_resource(self, resource):
        if resource.position in self.resource_dict:
            resource.stacked_resource = self.resource_dict[resource.position]
        self.resource_dict[resource.position] = resource

    def get_event(self, position):
        return self.event_dict.get(position, None)

    def grid_map(self, position, fov):
        x, y = position
        h, v = fov
        return self.world_map.grids(x - h, x + h + 1, y - v, y + v + 1)

    def collision_check(self):
        blocked_positions = set()
        collided_position_dict = {}
        for player in self.players:
            pos = player.next_scolled_position
            # Map blocks
            if self.world_map.is_block(pos):
                player.undo_action()
                pos = player.next_scolled_position
            # Player collision
            if player.is_moved:
                if pos in blocked_positions:
                    player.undo_action()
                    pos = player.next_scolled_position
                    blocked_positions.add(pos)
                    self.__undo_collided_players(pos, blocked_positions, collided_position_dict)
                else:
                    if pos in collided_position_dict:
                        collided_position_dict[pos].append(player)
                    else:
                        collided_position_dict[pos] = [player]
            else:
                blocked_positions.add(pos)
                self.__undo_collided_players(pos, blocked_positions, collided_position_dict)
        for collided_position in list(collided_position_dict):
            players = collided_position_dict.get(collided_position)
            if players:
                random.shuffle(players)
                collided_position_dict[collided_position] = [players.pop()]
                for player in players:
                    player.undo_action()
                    pos = player.next_scolled_position
                    blocked_positions.add(pos)
                    self.__undo_collided_players(pos, blocked_positions, collided_position_dict)

    def update_position_dict(self):
        self.player_position = {player.position: player for player in self.players}
        
    def _post_update_matching_edge(self, condition_attr, result_attr1, result_attr2):
        graph = self.social.social_graph
        matched_list = []
        for u, v, attr in graph.edges(data=True):
            if condition_attr in attr:
                if graph.has_edge(v,u) and graph[v][u].get(condition_attr) is not None:
                    edge1_condition = graph[u][v].get(condition_attr)
                    edge2_condition = graph[v][u].get(condition_attr)
                    if edge1_condition == edge2_condition:
                        graph.edges[u, v].pop(condition_attr)
                        graph.edges[v, u].pop(condition_attr)
                        self.social.add_relation(u, v, **result_attr1)
                        self.social.add_relation(v, u, **result_attr2)
                        matched_list.append((u,v))
        return matched_list

    def _post_merge_group(self, group1, group2):
        social_graph = self.social
        common_members = set(social_graph.successors(group1)) & set(social_graph.successors(group2))

        for member in common_members:
            attrs_group1 = social_graph[group1][member]
            attrs_group2 = social_graph[group2][member]
            if attrs_group1 != attrs_group2:
                print(f"Cannot merge {group1} and {group2}. Conflict on member {member}.")
                return False

        for member in social_graph.successors(group2):
            if not social_graph.has_edge(group1, member):
                self.social.join_group(member, group1, **social_graph[group2][member])
        self.social.remove_group(group2)
        # print(f"{group1} and {group2} successfully merged.")
        return True

    def _post_update_relation_to_group(self, condition_attr, result_attr):
        edges_to_remove = []
        for u, v, data in self.social.social_graph.edges(data=True):
            if data.get('attribute') == condition_attr:
                edges_to_remove.append((u, v))

        subgraph = self.social.social_graph.edge_subgraph(edges_to_remove).copy()
        scc_list = list(nx.strongly_connected_components(subgraph))
        scc_subgraphs = [subgraph.subgraph(scc).copy() for scc in scc_list]

        for subgraph in scc_subgraphs:
            edges_to_remove = list(subgraph.edges())
            self.social.social_graph.remove_edges_from(edges_to_remove)
            group_node = self.social.create_group()
            nodes_in_edges = set([u for u, v in edges_to_remove] + [v for u, v in edges_to_remove])
            for node in nodes_in_edges:
                self.social.join_group(node, group_node, **{result_attr: self.social.social_graph[node][group_node][condition_attr]})

    def _post_update_merge_relation_to_group(self, condition_attr, result_attr):
        for node in self.players:
            node_data = self.social.social_graph.nodes[node]
            for _, other, edge_attr in list(self.social.social_graph.out_edges(node, data=True)):
                other_data = self.social.social_graph.nodes[other]
                if edge_attr.get(condition_attr) and other_data.get('type') == 'player':
                    if self.social.social_graph.has_edge(other, node) and \
                        self.social.social_graph[other][node].get(condition_attr):
                            result_attr_value1 = edge_attr.get(condition_attr)
                            result_attr_value2 = self.social.social_graph[other][node].get(condition_attr)
                            self.social.remove_relation(node, other, condition_attr)
                            self.social.remove_relation(other, node, condition_attr)
                            if not node.groups and not other.groups:
                                group = self.social.create_group()
                                self.social.join_group(node, group, **{result_attr: result_attr_value1})
                                self.social.join_group(other, group, **{result_attr: result_attr_value2})
                            elif not node.groups:
                                for group in other.groups:
                                    if self.social.social_graph[group][other].get(result_attr):
                                        self.social.join_group(node, group, **{result_attr: result_attr_value1})
                            elif not other.groups:
                                for group in node.groups:
                                    if self.social.social_graph[group][node].get(result_attr):
                                        self.social.join_group(other, group, **{result_attr: result_attr_value2})
                            else: # merge group
                                for other_group in other.groups.copy():
                                    for member in list(self.social.social_graph.successors(other_group)):
                                        for node_group in node.groups:
                                            if not self.social.social_graph.has_edge(node_group, member):
                                                self.social.join_group(member, node_group, **self.social.social_graph[other_group][member])
                                                self.social.quit_group(member, other_group)
                                    if other_group != node_group:
                                        self.social.remove_group(other_group)
    def _post_update_relation_switch(self, condition_attr, target_attr):
        social_graph = self.social.social_graph
        
        edges_to_modify = []
        for A, B, edge_data in social_graph.edges(data=True):
            if condition_attr in edge_data:
                if social_graph.has_edge(B, A) and target_attr in social_graph[B][A]:
                    edges_to_modify.append((A, B, edge_data[condition_attr]))
        
        for A, B, value in edges_to_modify:
            for attr in social_graph[A][B]:
                self.social.remove_relation(A, B, attr)
            self.social.add_relation(A, B, **{target_attr: value})
            
    def _post_symmetrize_relation(self, attr):
        social_graph = self.social.social_graph
        edges_to_add = []

        for u, v, data in social_graph.edges(data=True):
            if attr in data:
                if not social_graph.has_edge(v, u):
                    edges_to_add.append((v, u, data[attr]))
                else:
                    if attr not in social_graph[v][u]:
                        social_graph[v][u][attr] = data[attr]
        for v, u, value in edges_to_add:
            self.social.add_relation(v, u, **{attr: value})
            
    def _post_normalization(self, attr):
        social_graph = self.social.social_graph

        for group_node in social_graph.nodes:
            if social_graph.nodes[group_node].get('type') == 'group':
                total_attr_value = 0.0
                edges = []
                for neighbor in social_graph.successors(group_node):
                    if social_graph.nodes[neighbor].get('type') == 'player':
                        if attr in social_graph[group_node][neighbor]:
                            total_attr_value += social_graph[group_node][neighbor][attr]
                            edges.append((group_node, neighbor))

                if total_attr_value > 0:
                    for group_node, player_node in edges:
                        social_graph[group_node][player_node][attr] /= total_attr_value
                        self.social.update_edge_dict(group_node, player_node)

    def _post_clear_temporary_relation(self, attr):
        social_graph = self.social.social_graph
        edge_list = []
        for u, v, edge_data in social_graph.edges(data=True):
            if attr in edge_data and social_graph.nodes[u]['type'] == 'player' and social_graph.nodes[v]['type'] == 'player':
                edge_list.append((u, v, attr))
        for u, v, attr in edge_list:        
            self.social.remove_relation(u, v, attr)

    def load_func(self, func_args, func_dict):
        _func_name_list = []
        _kwargs_list = []
        for func in func_args:
            if isinstance(func, str):
                _func_name = func
                kwargs = {}
            elif isinstance(func, dict):
                _func_name = func['function']
                kwargs = func.get('kwargs', {})
            else:
                _func_name, kwargs = func

            _func_name_list.append(_func_name)
            _kwargs_list.append(kwargs)

        def function():
            for func, kwargs in zip(_func_name_list, _kwargs_list):
                func_dict[func](**kwargs)

        return function

    def check_social_schedule(self):
        if self.milestones:
            milestone = -100
            while self.milestones and self.steps >= self.milestones[0]:
                milestone = self.milestones.pop(0)
            if milestone == self.steps:
                self.social.clear_graph()
                graph_info = self.social_schedule[str(milestone)]
                self.social.load_graph(graph_info)

    def __undo_collided_players(self, collided_position, blocked_positions, collided_position_dict):
        players = collided_position_dict.pop(collided_position, [])
        for player in players:
            player.undo_action()
            pos = player.next_scolled_position
            blocked_positions.add(pos)
            self.__undo_collided_players(pos, blocked_positions, collided_position_dict)

    def _post_update_split_score_to_group(self, attribute):
        shared_groups = set()
        for player in self.players:
            group_set = player.group_dict.get(attribute, {})
            # if a player has joined multiple groups with required attribute, his score is divided equally to each group
            if group_set:
                base_score = player.reward / len(group_set)
                for group in group_set:
                    player.provide_score(base_score)
                    group.earn_score(base_score)
                    shared_groups.add(group)
        for group in shared_groups:
            group.split_score(self.social.social_graph, attribute)
        for player in self.players:
            player.settle_score()

    def get_state(self):
        state = {'episode_id': 0, 'step_id': 0, 'Map': {}, 'Player': {}, 'Social': {}}
        state['episode_id'] = self.episodes
        state['step_id'] = self.steps
        
        '''Map Info'''
        state['Map']['block_grids'] = self.world_map.observation.T
        state['Map']['resources'] = self._get_all_resource()
        state['Map']['events'] = [event.get_dict_info() for event in self.events]
        
        '''Player Info'''
        state['Player'] = [
            {**player.get_dict_info(), 'inventory': player.get_inventory()} 
            for player in self.players
        ]
        
        '''Social Info'''
        state['Social']['global'] = self._get_social_global()
        state['Social']['communications'] = self._get_all_communication()
        return state

    def _get_obs(self):
        obs = {}
        social_global = self._get_social_global()
        groups = self._get_social_groups()
        for player in self.players:
            _obs = {'episode_id': 0, 'step_id': 0, 'Map': {}, 'Player': {}, 'Social': {}}
            _obs['episode_id'] = self.episodes
            _obs['step_id'] = self.steps

            '''Map Info'''
            _obs['Map']['block_grids'] = self.grid_map(position=player.position, fov=player.fov).T
            _obs['Map']['resources'] = self._get_visible_resource(player)
            _obs['Map']['events'] = self._get_visible_event(player)
            _obs['Map']['players'] = self._get_visible_player(player)

            '''Player Info'''
            _obs['Player'] = player.get_dict_info()
            _obs['Player']['inventory'] = player.get_inventory()
            
            '''Social Info'''
            _obs['Social']['global'] = social_global
            _obs['Social']['communications'] = self._get_single_communication(player)
            # _obs['Social']['groups'] = groups
            # _obs['Social']['social_graph'] = self.social.social_graph
            obs[player.name] = _obs

        # generate a json file for social global and add it into a specific file (the file is the same for steps in the same episode) in ./debug/sample
        # dump_info = {"episode_id": self.episodes, "step_id": self.steps, "Social": {"global": social_global}}
        # with open(f'./debug/sample/social_global_{self.episodes}_{self.steps}.json', 'a') as f:
        #     json.dump(dump_info, f, cls=NumpyEncoder, indent=4)
        
        for player in self.players:
            obs[player.name]['Social']['sharings'] = self._get_social_sharing(player, obs)
        return obs
    
    def _get_all_resource(self):
        resource_list = []
        for resource in self.resource_dict.values():
            while resource:
                resource_list.append(resource.get_dict_info())
                resource = resource.stacked_resource
        return resource_list

    def _get_visible_resource(self, player):
        visible_resources_dict = []
        for resource in player.visible_resources:
            visible_resources_dict.append(resource.get_dict_info())
        return visible_resources_dict

    def _get_visible_event(self, player):
        visible_events_dict = []
        for event in player.visible_events:
            visible_events_dict.append(event.get_dict_info())
        return visible_events_dict

    def _get_visible_player(self, player):
        visible_players_dict = []
        for other_player in player.visible_players:
            visible_players_dict.append(other_player.get_dict_info())
        return visible_players_dict
    
    def _get_all_communication(self):
        communication_list = []
        for from_node, to_node, communication_unit in self.social.social_graph.edges(data = 'communication', default=None):
            if communication_unit is not None:
                communication_list.append({
                    "from": from_node._id,
                    "to": to_node._id,
                    "words": communication_unit
                })
        return communication_list

    def _get_single_communication(self, player):
        communication_list = []
        for from_node, _, communication_unit in self.social.social_graph.in_edges(player, data = 'communication', default=None):
            if communication_unit is not None:
                communication_list.append({
                    "from": from_node._id,
                    "to": player._id,
                    "words": communication_unit
                })
        return communication_list
    
    def _get_social_groups(self):
        groups = []
        for node, attr in self.social.social_graph.nodes(data=True):
            if attr['type'] == 'group':
                groups.append(node)
        return groups
    
    def _get_social_global(self):
        return {
            "nodes": self.social.get_node_list(),
            "edges": self.social.get_edge_list(),
        }
        
    def _get_social_sharing(self, player, obs):
        available_key = ['Map', 'Player']
        sharings = {}
        for from_node, _, attr in self.social.social_graph.in_edges(player, data='sharing', default={}):
            if attr:
                for key in available_key:
                    if attr.get(key) is True:
                        sharing = obs[from_node.name][key]
                        if from_node._id in sharings:
                            sharings[from_node._id].update({key: sharing})
                        else:
                            sharings[from_node._id] = {key: sharing}
        return sharings

    def _get_terminateds(self):
        terminateds = {player.name: player.terminated for player in self.players}
        self.terminated = (self.steps >= self.max_length)
        terminateds['__all__'] = self.terminated
        return terminateds

    def _get_rewards(self):
        return {player.name: player.reward for player in self.players}

    def _get_infos(self):
        return {player.name: {} for player in self.players}
