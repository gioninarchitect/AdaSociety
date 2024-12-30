import json
import random
import numpy as np

from ..env.event import Event
from ..env.game import Game
from ..env.player import Player
from ..env.resource import Resource
from ..env.social import Social
from ..env.group import Group
from ..env.world_map import WorldMap

BLANK = 0
BLOCK = 1
SPACE = ' '
TREE = 'T'
ROCK = 'R'
WATER = 'W'
MAP_STR_DICT = {
    SPACE: BLANK,
    TREE: BLOCK,  # Tree
    ROCK: BLOCK,  # Rock
    WATER: BLOCK,  # Water
}
NAME_LIST = ['Adam', 'Buford', 'Cindy', 'Dax', 'Eva', 'Fate', 'Gustav', 'Hampton', 'Ima', 'Jack']


class GameEditor:
    def __init__(self, config):
        self.config = config
        self.world_map = None
        # Load default config

    def generate_game(self):
        world_map = self.generate_map()
        resources = self.generate_resources(world_map)
        events = self.generate_events(world_map)
        players = self.generate_players(world_map)
        social = self.generate_social(players)
        game = Game(
            world_map=world_map,
            resources=resources,
            events=events,
            players=players,
            social=social,
            social_schedule=self.config.task.static.social_schedule,
            negotiation_steps=self.config.task.negotiation_steps,
            pre_updates=self.config.task.pre_updates,
            post_updates=self.config.task.post_updates,
            max_length = self.config.task.max_length,
        )
        return game

    def generate_map(self):
        # Base
        base_map_config = self.config['task']['base_map']
        base_map_init_rule = base_map_config['init_rule']
        if 'size' in base_map_config:
            size_x, size_y = base_map_config['size']['x'], base_map_config['size']['y']
        else:
            size_x, size_y = None, None
        file_path = base_map_config.get('file_path')
        world_map = self._load_map(base_map_init_rule, size_x, size_y, file_path)
        # TODO load static blocks
        config = self.config.task.static.blocks
        # Load random blocks
        # TODO
        config = self.config.task.random.blocks
        conf_list = [c for c in config for _ in range(c['repeat'])]
        block_num = len(conf_list)
        blank_pos = world_map.blank_pos.copy()
        for k in ['resources', 'events', 'players']:
            k_confs = self.config.task.static.get(k, [])
            for c in k_confs:
                positions = c['positions']
                if not isinstance(positions[0], list):
                    positions = [positions]
                for pos in positions:
                    blank_pos.discard(tuple(pos))
        pos_list = random.sample(list(blank_pos), block_num)
        world_map.add_blocks(pos_list)
        return world_map

    def generate_resources(self, world_map):
        resources = []
        # Load static resources
        config = self.config.task.static.resources
        for c in config:
            names = c['name']
            if not isinstance(names, list):
                names = [names]
            positions = c['positions']
            if not isinstance(positions[0], list):
                positions = [positions]
            nums = c['num']
            if not isinstance(nums, list):
                nums = [nums]
            name_num = len(names)
            pos_num = len(positions)
            num_num = len(nums)
            for i in range(max(name_num, pos_num, num_num)):
                name = names[i % name_num]
                pos = positions[i % pos_num]
                num = nums[i % num_num]
                resources.append(self._create_resource(
                    name=name,
                    position=pos,
                    amount=num,
                ))
        # Load random resources
        config = self.config.task.random.resources
        conf_list = [c for c in config for _ in range(c['repeat'])]
        resource_num = len(conf_list)
        # TODO stackable = True
        blank_pos = world_map.blank_pos.copy()
        for resource in resources:
            blank_pos.discard(resource.position)
        pos_list = random.sample(list(blank_pos), resource_num)
        resource_config = self.config['resource']
        for conf, pos in zip(conf_list, pos_list):
            resources.append(self._create_resource(
                name=conf['name'],
                position=pos,
                amount=self._num_generator(conf['num']),
            ))
        return resources

    def generate_events(self, world_map):
        events = []
        # Load static events
        config = self.config.task.static.events
        for c in config:
            names = c['name']
            if not isinstance(names, list):
                names = [names]
            positions = c['positions']
            if not isinstance(positions[0], list):
                positions = [positions]
            name_num = len(names)
            pos_num = len(positions)
            for i in range(max(name_num, pos_num)):
                name = names[i % name_num]
                pos = positions[i % pos_num]
                events.append(self._create_event(
                    name=name,
                    position=pos,
                ))
        # Load random events
        config = self.config.task.random.events
        conf_list = [c for c in config for _ in range(c['repeat'])]
        event_num = len(conf_list)
        blank_pos = world_map.blank_pos.copy()
        for event in events:
            blank_pos.discard(event.position)
        pos_list = random.sample(list(blank_pos), event_num)
        for conf, pos in zip(conf_list, pos_list):
            events.append(self._create_event(
                name = conf['name'],
                position=pos,
            ))
        return events

    def generate_players(self, world_map):
        players = []
        # Load static players
        config = self.config.task.static.players
        for c in config:
            job_name = c['job']
            positions = c['positions']
            if not isinstance(positions[0], list):
                positions = [positions]
            for pos in positions:
                player_id = len(players)
                players.append(self._create_player(
                    player_id=player_id,
                    # name=NAME_LIST[player_id % len(NAME_LIST)],
                    name=f'{job_name}_{player_id}',
                    position=pos,
                    rotation=None,
                    job_name=job_name,
                ))
        # Load random players
        config = self.config.task.random.players
        conf_list = [c for c in config for _ in range(c['repeat'])]
        # TODO shuffle will break the name order, and thus break rllib training for now
        # random.shuffle(conf_list)
        player_num = len(conf_list)
        pos_list = random.sample(list(world_map.blank_pos), player_num)
        for c, pos in zip(conf_list, pos_list):
            job_name = c['job']
            player_id = len(players)
            players.append(self._create_player(
                player_id=player_id,
                # TODO
                # name=NAME_LIST[player_id % len(NAME_LIST)],
                name=f'{job_name}_{player_id}',
                position=pos,
                rotation=None,
                job_name=job_name,
            ))
        return players

    def generate_social(self, players):
        social = Social(players)
        groups = []
        # Load static relations
        config = self.config.task.static.social.relations
        for c in config:
            attr = {}
            if 'name' in c:
                attr['name'] = c['name']
            attr.update(c.get('attributes', {}))
            for player_pair in c['players']:
                from_id = player_pair['from']
                to_id = player_pair['to']
                social.add_relation(players[from_id], players[to_id], **attr)
        config = self.config.task.static.social.groups
        for c in config:
            group = social.create_group(name=c.get('name', ''))
            player_config = c.get('players', {})
            ids = player_config.get('ids', {})
            attr = player_config.get('attributes', {})
            attr_list = [dict(zip(attr, v)) for v in zip(*attr.values())] if attr else [{}] * len(ids)
            for _id, a in zip(ids, attr_list):
                social.join_group(players[_id], group, **a)
        # TODO Load random relations
        return social

    def _num_generator(self, config, index=None):
        rule = config['rule']
        if rule == 'static':
            return config['num']
        elif rule == 'loop':
            raise NotImplementedError
        elif rule == 'random':
            dist = config.get('dist', 'uniform')
            dtype = config.get('type', 'int')
            min_n = config['min']
            max_n = config['max']
            if dist == 'uniform':
                if dtype == 'int':
                    return random.randint(min_n, max_n)
                else:
                    raise NotImplementedError
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    def _load_map(self, init_rule, size_x, size_y, file_path=None):
        token_array = []
        if init_rule == 'blank':
            token_array = [[' '] * size_x for _ in range(size_y)]
            return WorldMap(token_array, token_lookup_table=MAP_STR_DICT)
        elif init_rule == 'box':
            token_array = (
                [[TREE] * size_x]
                + [[TREE] + [SPACE] * (size_x - 2) + [TREE]] * (size_y - 2)
                + [[TREE] * size_x]
            )
            return WorldMap(token_array, token_lookup_table=MAP_STR_DICT)
        elif init_rule == 'map_file':
            unit_str_len = 1
            with open(file_path, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    token_array.append([line[i:i+unit_str_len] for i in range(0, len(line), unit_str_len)])
            world_map = WorldMap(token_array)
            return world_map
        else:
            raise NotImplementedError

    def _create_resource(self, name, position, amount):
        config = self.config['resource']
        return Resource(
            name=name,
            _type=config[name]['type'],
            position=position,
            amount=amount,
            requirements=config[name].get('requirements', {}),
            unit_score=config[name].get('score', 0),
        )

    def _create_event(self, name, position):
        config = self.config['event']
        resource_pool = {}
        for resource_name in config[name].get('out', {}):
            resource_pool[resource_name] = self._create_resource(
                name=resource_name,
                position=None,
                amount=float('inf'),
            )
        return Event(
            name=name,
            position=position,
            inputs=config[name].get('in', {}),
            outputs=config[name].get('out', {}),
            resource_pool=resource_pool,
            requirements=config[name].get('requirements', {}),
        )

    def _create_player(self, player_id, name, job_name, position, rotation):
        job_config = self.config['job'][job_name]
        inventory_config = job_config.get('inventory', {})
        init_resources = []
        for c in inventory_config.get('init', []):
            init_resources.append(self._create_resource(
                name=c['name'],
                position=None,
                amount=c['num'],
            ))
        return Player(
            player_id=player_id,
            name=name,
            job=job_name,
            position=position,
            rotation=rotation,
            fov=job_config['fov'],
            inventory_size=inventory_config.get('size', float('inf')),
            init_resources=init_resources,
            resource_max_dict=dict(inventory_config.get('max', {})),
            resource_preference_dict=dict(inventory_config.get('score', {})),
        )
