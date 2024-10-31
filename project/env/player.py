class Player:
    def __init__(
        self,
        player_id,
        name,
        job,
        fov,
        position,
        rotation,
        inventory_size,
        init_resources=[],
        resource_max_dict={},
        resource_preference_dict={},
    ):
        self._id = player_id
        self.name = name
        self.job = job
        # States
        self.x, self.y = position
        self.next_x, self.next_y = self.x, self.y
        self.next_scolled_x, self.next_scolled_y = self.x, self.y
        self.is_moved = False
        self.rotation = rotation
        # Field of View: [left & right, front & back]
        if isinstance(fov, int):
            self.fov = [fov, fov]
        elif isinstance(fov, list):
            self.fov = [fov[0], fov[1]]
        else:
            raise ValueError
        # TODO
        self.inventory = {}
        self.inventory_size = inventory_size
        self.resource_total = 0
        self.resource_max_dict = resource_max_dict
        self.resource_preference_dict = resource_preference_dict
        for resource in init_resources:
            self.pick_up(resource)
        self.terminated = False
        # Social
        self.groups = set()
        self.group_dict = {}
        # Reward
        self.prev_score = 0
        self.score = 0
        self._shared_score_in = 0
        self._shared_score_out = 0
        self.reward = 0
        # Observation functions
        self._obs_funcs = {
            'position': self._obs_position,
            'inventory': self._obs_inventory,
        }
        # Action functions
        self._action_funcs = {
            'no_act': self._act_null,
            'move': self._act_move,
            'move_up': self._act_move_up,
            'move_down': self._act_move_down,
            'move_left': self._act_move_left,
            'move_right': self._act_move_right,
            'pick': self._act_pick,
            'pick_by_name': self._act_pick_by_name,
            'dump_by_name': self._act_dump_by_name,
            'produce': self._act_produce,
            'request_matching': self._act_request_matching,
            'accept_proposal': self._act_accept_proposal,
            'end_bargaining': self._act_end_bargaining,
            'propose': self._act_propose,
            'check_relation': self._act_check_relation,
            'add_relation': self._act_add_relation,
            'remove_relation': self._act_remove_relation,
            'quit_group': self._act_quit_group,
            'join_group': self._act_join_group,
        }

    def join_game(self, game):
        self.game = game

    def pre_update(self):
        pass
    
    def update(self, actions):
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            if isinstance(action, str):
                _action = action
                kwargs = {}
            elif isinstance(action, dict):
                _action = action['action']
                kwargs = action.get('kwargs', {})
            else:
                _action, kwargs = action
            self._action_funcs[_action](**kwargs)

    def post_update(self):
        # Move
        #if self.is_moved:
        self.x = self.next_scolled_x
        self.y = self.next_scolled_y
        self.next_x = self.x
        self.next_y = self.y
        self.is_moved = False
        # Update score
        self.prev_score = self.score
        self.score = 0
        for resources in self.inventory.values():
            for resource in resources:
                self.score += resource.score
        self.reward = self.score - self.prev_score

    def undo_action(self):
        self.next_x = self.x
        self.next_y = self.y
        self.next_scolled_x = self.x
        self.next_scolled_y = self.y
        self.is_moved = False

    def move(self, dx, dy):
        self.next_x = self.x + dx
        self.next_y = self.y + dy
        self.next_scolled_x = self.next_x % self.game.world_map.size_x
        self.next_scolled_y = self.next_y % self.game.world_map.size_y
        self.is_moved = True

    def pick_up(self, resource):
        name = resource.name
        if self.resource_total + resource.amount > self.inventory_size:
            resource.amount = self.inventory_size - self.resource_total
        if resource.amount <= 0:
            return
        if resource.name in self.resource_preference_dict:
            resource.set_unit_score(self.resource_preference_dict[resource.name])
        if name in self.inventory:
            self.inventory[name].append(resource)
        else:
            self.inventory[name] = [resource]

    def dump(self, resource_name, n):
        resources = self.inventory.get(resource_name, [])
        remain_n = n
        while resources and remain_n > 0:
            resource = resources[0]
            dumped_resource = resource.provide(remain_n)
            dumped_resource.set_position(self.position)
            dumped_resource.reset_unit_score()
            self.game.lay_resource(dumped_resource)
            remain_n -= dumped_resource.amount
            if not resource.is_available:
                del resources[0]

    def check_amount(self, resource_name, n):
        resources = self.inventory.get(resource_name, [])
        remain_n = n
        for resource in resources:
            remain_n -= resource.amount
            if remain_n <= 0:
                return True
        return False

    def consume(self, resource_name, n):
        resources = self.inventory.get(resource_name, [])
        remain_n = n
        while resources and remain_n > 0:
            resource = resources[0]
            remain_n = resource.consume(remain_n)
            if not resource.is_available:
                del resources[0]
        return remain_n

    def earn_score(self, score):
        self._shared_score_in += score

    def provide_score(self, score):
        self._shared_score_out += score

    def settle_score(self):
        self.reward = self.reward + self._shared_score_in - self._shared_score_out
        self._shared_score_in = 0
        self._shared_score_out = 0

    def request_matching(self, from_player, to_player):
        pass

    def join_group(self, group, attributes=[]):
        self.groups.add(group)
        for attribute in attributes:
            if attribute in self.group_dict:
                self.group_dict[attribute].add(group)
            else:
                self.group_dict[attribute] = {group}

    def quit_group(self, group, attributes=[]):
        self.groups.discard(group)
        if attributes:
            for attribute in attributes:
                self.group_dict.get(attribute, set()).discard(group)
        else:
            for group_set in self.group_dict.values():
                group_set.discard(group)

    def set_observation_keys(self, keys):
        self._obs_keys = keys

    def get_dict_info(self):
        return {
            'id':self._id,
            'name': self.name,
            'position': self.position
        }
        
    def get_inventory(self):
        return [resource.observation for resources in self.inventory.values() for resource in resources]

    @property
    def observation(self):
        obs = {
            'id': self._id,
            'name': self.name,
        }
        for k in self._obs_keys:
            obs[k] = self._obs_funcs[k]()
        return obs

    # @property
    # def reward(self):
    #     return self.score - self.prev_score

    @property
    def position(self):
        return (self.x, self.y)

    @property
    def next_position(self):
        return (self.next_x, self.next_y)

    @property
    def next_scolled_position(self):
        return (self.next_scolled_x, self.next_scolled_y)

    @property
    def visible_resources(self):
        x, y = self.position
        h, v = self.fov
        resources = []
        for dh in range(-h, h + 1):
            for dv in range(-v, v + 1):
                scolled_x = (x + dh) % self.game.world_map.size_x
                scolled_y = (y + dv) % self.game.world_map.size_y
                resource = self.game.resource_dict.get((scolled_x, scolled_y))
                if resource and resource.check_visible(self):
                    resources.append(resource)
        return resources

    @property
    def visible_events(self):
        x, y = self.position
        h, v = self.fov
        events = []
        for dh in range(-h, h + 1):
            for dv in range(-v, v + 1):
                scolled_x = (x + dh) % self.game.world_map.size_x
                scolled_y = (y + dv) % self.game.world_map.size_y
                event = self.game.event_dict.get((scolled_x, scolled_y))
                if event and event.check_visible(self):
                    events.append(event)
        return events

    @property
    def visible_players(self):
        x, y = self.position
        h, v = self.fov
        players = []
        for dh in range(-h, h + 1):
            for dv in range(-v, v + 1):
                scolled_x = (x + dh) % self.game.world_map.size_x
                scolled_y = (y + dv) % self.game.world_map.size_y
                player = self.game.player_position.get((scolled_x, scolled_y))
                if player and player.name != self.name:
                    players.append(player)
        return players

    def _obs_grid(self):
        return self.game.grid_map(self.position, self.rotation, self.fov)

    def _obs_position(self):
        return list(self.position)

    def _obs_inventory(self):
        return [resource.observation for resources in self.inventory.values() for resource in resources]

    def _act_null(self, **kwargs):
        pass

    def _act_move(self, dx, dy, **kwargs):
        self.move(dx, dy)

    def _act_move_up(self, **kwargs):
        self.move(0, -1)

    def _act_move_down(self, **kwargs):
        self.move(0, 1)

    def _act_move_left(self, **kwargs):
        self.move(-1, 0)

    def _act_move_right(self, **kwargs):
        self.move(1, 0)

    def _act_pick(self, **kwargs):
        resource = self.game.resource_dict.get(self.position)
        if resource and resource.check_visible(self):
            resource = self.game.provide_resource(self.position)
            if resource:
                self.pick_up(resource)
                # print(f'Player {self._id} picked up a {resource.name} at ({self.x}, {self.y}).')

    def _act_pick_by_name(self, resource_name, **kwargs):
        resource = self.game.bubble_up_resource(self.position, resource_name)
        if resource and resource.check_visible(self):
            resource = self.game.provide_resource(self.position)
            if resource:
                self.pick_up(resource)
                # print(f'Player {self._id} picked up a {resource.name} at ({self.x}, {self.y}).')

    def _act_dump_by_name(self, resource_name, **kwargs):
        self.dump(resource_name, n=1)
        # print(f'Player {self._id} dumped a {resource_name} as ({self.x}, {self.y})')

    def _act_produce(self, **kwargs):
        # TODO Trigger an event
        event = self.game.get_event(self.position)
        if event and event.is_available:
            # Check inventory
            for name, num in event.inputs.items():
                if not self.check_amount(name, num):
                    return
            # Produce
            for name, num in event.inputs.items():
                self.consume(name, num)
            for resource in event.provide():
                self.pick_up(resource)
                # print(f'Player {self._id} produce: {resource.name} at ({self.x}, {self.y}).')

    def _act_add_relation(self, to_player_id, attributes_dict={}, **kwargs):
        player_to = self.game.player_dict[to_player_id]
        self.game.social.add_relation(self, player_to, **attributes_dict)
        
    def _act_remove_relation(self, to_player_id, attribute_name, **kwargs):
        player_to = self.game.player_dict[to_player_id]
        self.game.social.remove_relation(self, player_to, attribute_name)

    def _act_quit_group(self, group_id, attribute_name, **kwargs):
        group = self.game.social.group_dict[group_id]
        self.game.social.quit_group(self, group, [attribute_name])

    def _act_join_group(self, group_id, attribute_dict={}, **kwargs):
        group = self.game.social.group_dict[group_id]
        self.game.social.join_group(self, group, **attribute_dict)

    def _act_check_relation(self, to_player_id, attribute_dict={}, **kwargs):
        player_to = self.game.player_dict[to_player_id]
        self.game.social.check_relation(self, player_to, **attribute_dict)

    def _act_scale_value(self, group, attr, scale, **kwargs):
        for pred, _, data in self.game.social.social_graph.out_edges(group, data=True):
            if attr in data:
                data[attr] *= scale

    def _act_request_matching(self, to_player_id, **kwargs):
        self._act_add_relation(to_player_id, attributes_dict={'matching_request_step': self.game.steps})
    
    def _act_accept_proposal(self, to_player_id, scale, **kwargs):
        social_graph = self.game.social.social_graph
        player_to = self.game.player_dict[to_player_id]
        groupA = next((group for group in social_graph.predecessors(self)
                       if social_graph.nodes[group].get('type') == 'group'), None)
        groupB = next((group for group in social_graph.predecessors(player_to)
                       if social_graph.nodes[group].get('type') == 'group'), None)
        accept_score1 = scale
        accept_score2 = 1 - scale
        if groupA is not None:
            self._act_scale_value(groupA, attr='score', scale=scale)
            accept_score1 = social_graph[groupA][self]['score']
        if groupB is not None:
            self._act_scale_value(groupB, attr='score', scale=1-scale)
            accept_score2 = social_graph[groupB][player_to]['score']

        self.game.social.add_relation(self, player_to, **{'accept': accept_score1})
        self.game.social.add_relation(player_to, self, **{'accept': accept_score2})
        self.game.social.remove_relation(self, player_to, attribute='proposal')
        self.game.social.remove_relation(player_to, self, attribute='proposal')
        self.game.social.remove_relation(self, player_to, attribute='parity')
        self.game.social.remove_relation(player_to, self, attribute='parity')

    def _act_end_bargaining(self, to_player_id, **kwargs):
        player_to = self.game.player_dict[to_player_id]
        self.game.social.remove_relation(self, player_to, attribute='proposal')
        self.game.social.remove_relation(player_to, self, attribute='proposal')
        self.game.social.remove_relation(self, player_to, attribute='parity')
        self.game.social.remove_relation(player_to, self, attribute='parity')

    def _act_propose(self, to_player_id, score):
        self._act_add_relation(to_player_id, attributes_dict={'proposal': score})
