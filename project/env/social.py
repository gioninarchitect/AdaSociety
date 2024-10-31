import networkx as nx
from .group import Group


class Social:
    def __init__(self, players):
        self.players = players
        self.social_graph = nx.DiGraph()
        for player in players:
            self.social_graph.add_node(player)
            self.social_graph.nodes[player].update(
                {
                    'type': 'player',
                    'id': player._id
                }
            )
            self.social_graph.nodes[player]['_dict_view'] = self.node_to_dict(self.social_graph.nodes[player])
        self.group_dict = {}
        self.next_group_id = 0
        self.obs = {}
        self.sharings = {}
        self.communications = []

    def check_relation(self, player_from, player_to, **attr):
        if self.social_graph.has_edge(player_from, player_to):
            if list(attr.keys())[0] in self.social_graph.edges[player_from, player_to]:
                return list(attr.values())[0] == self.social_graph.edges[player_from, player_to][list(attr.keys())[0]]
        return False

    def add_relation(self, player_from, player_to, **attr):
        self.social_graph.add_edge(player_from, player_to, **attr)
        self.update_edge_dict(player_from, player_to)

    def remove_relation(self, player_from, player_to, attribute):
        if attribute in self.social_graph.edges[player_from, player_to]:
            del self.social_graph.edges[player_from, player_to][attribute]
            del self.social_graph.edges[player_from, player_to]['_dict_view']['attributes'][attribute]
        if len(self.social_graph.edges[player_from, player_to]) == 1:
            assert '_dict_view' in self.social_graph.edges[player_from, player_to]
            self.social_graph.remove_edge(player_from, player_to)

    def create_group(self, name='', **attr):
        group = Group(_id=self.next_group_id, name=name, players=[])
        self.group_dict[self.next_group_id] = group
        self.next_group_id += 1
        self.social_graph.add_node(group, **attr)
        self.social_graph.nodes[group].update(
            {
                'type': 'group',
                'id': group._id,
            }
        )
        self.social_graph.nodes[group]['_dict_view'] = self.node_to_dict(self.social_graph.nodes[group])
        return group

    def remove_group(self, group):
        for player in group.players:
            self.quit_group(player, group)
        self.social_graph.remove_node(group)
        self.group_dict.pop(group._id, None)

    def join_group(self, player, group, **attr):
        self.social_graph.add_edge(group, player, **attr)
        self.update_edge_dict(group, player)
        player.join_group(group, list(attr.keys()))
        group.add_player(player)

    def quit_group(self, player, group, attributes=None):
        if attributes is None:
            attributes = []
        if attributes:
            d = self.social_graph.edges[group, player]
            for attribute in attributes:
                del d[attribute]
                del d['_dict_view']['attributes'][attribute]
            if len(d) == 1:
                assert '_dict_view' in d
                self.social_graph.remove_edge(group, player)
                player.quit_group(group, attributes)
                group.remove_player(player)
        else:
            self.social_graph.remove_edge(group, player)
            player.quit_group(group)
            group.remove_player(player)

    def merge_group(self, attribute):
        for player in self.players:
            groups = player.group_dict.get(attribute, [])
            if len(group) > 1:
                for group in groups[1:]:
                    self.merge_two_groups(self, groups[0], group, attribute)

    def merge_two_groups(self, group_1, group_2, attribute):
        for player in self.social_graph.successors(group_2):
            if self.social_graph.has_edge(group_1, player):
                edge_attr = self.social_graph[group_1][player]
                if edge_attr != self.social_graph[group_2][player]:
                    return False
            value = self.social_graph[group_2, player][attribute]
            self.quit_group(player, group_2, attributes=[attribute])
            self.join_group(player, group_1, **{attribute: value})
        if not self.social_graph.successors(group_2):
            self.remove_group(group_2)
        return True

    def find_matching_pairs(self):
        pairs = []
        for node1, node2 in self.social_graph.edges():
            if self.social_graph.has_edge(node2, node1):
                edge1_condition = self.social_graph[node1][node2].get('matching_condition', None)
                edge2_condition = self.social_graph[node2][node1].get('matching_condition', None)
                if edge1_condition == edge2_condition:
                    pairs.append((node1, node2))

        return pairs

    def clear_graph(self):
        for player in self.players:
            groups = player.groups.copy()
            for group in groups:
                self.quit_group(player, group)
        self.social_graph = nx.DiGraph()
        for player in self.players:
            self.social_graph.add_node(player)
            self.social_graph.nodes[player].update(
                {
                    'type': 'player',
                    'id': player._id,
                }
            )
            self.social_graph.nodes[player]['_dict_view'] = self.node_to_dict(self.social_graph.nodes[player])
        self.group_dict = {}
        self.next_group_id = 0
        self.obs = {}
        self.sharings = {}
        self.communications = []

    def load_graph(self, config):
        for c in config["relations"]:
            attr = {}
            if 'name' in c:
                attr['name'] = c['name']
            attr.update(c.get('attributes', {}))
            for player_pair in c['players']:
                from_id = player_pair['from']
                to_id = player_pair['to']
                self.add_relation(self.players[from_id], self.players[to_id], **attr)
        for c in config["groups"]:
            group = self.create_group(name=c.get('name', ''))
            player_config = c.get('players', {})
            ids = player_config.get('ids', {})
            attr = player_config.get('attributes', {})
            attr_list = [dict(zip(attr, v)) for v in zip(*attr.values())] if attr else [{}] * len(ids)
            for _id, a in zip(ids, attr_list):
                self.join_group(self.players[_id], group, **a)

    def get_node_list(self):
        return [data for _, data in self.social_graph.nodes(data='_dict_view')]
    
    def get_edge_list(self):
        return [data for _, _, data in self.social_graph.edges(data='_dict_view')]
        
    def update_edge_dict(self, u, v):
        if '_dict_view' not in self.social_graph.edges[u, v]:
            self.social_graph.edges[u, v]['_dict_view'] = self.edge_to_dict(
                u, v, {k: v for k, v in self.social_graph.edges[u, v].items() if k != '_dict_view'}
            )
        else:
            self.social_graph.edges[u, v]['_dict_view']["attributes"].update({
                k: v for k, v in self.social_graph.edges[u, v].items() if k != '_dict_view'
            })
        
    def node_to_dict(self, attr):
        return {
                "type": attr["type"],
                attr["type"]: {"id": attr["id"]},
            }
        
    def edge_to_dict(self, u, v, attr):
        return {
            "from": {
                "type": self.social_graph.nodes[u]["type"], 
                "id": self.social_graph.nodes[u]["id"],
            },
            "to": {
                "type": self.social_graph.nodes[v]["type"], 
                "id": self.social_graph.nodes[v]["id"],
            },
            "attributes": attr,
        }
            
    @property
    def observation(self):
        # TODO
        return self.obs
