import os
import json
import pygame

from ray.rllib.env.multi_agent_env import MultiAgentEnv

from .gui.canvas import Canvas
from .gui.render import Render
from ..utils.config_loader import ConfigLoader
from ..utils.game_editor import GameEditor
import random


class Environment(MultiAgentEnv):
    def __init__(
        self,
        config_name='./config/main.json',
    ):
        self.config_loader = ConfigLoader(config_name)
        self.game_editor = GameEditor(config=self.config_loader.config)
        self.episode = -1

        # Render
        render_config = self.config_loader.render
        self.rendering = Render(render_config)

    def reset(
        self,
        *,
        seed=None,
        options=None,
    ):
        super().reset(seed=seed, options=options)

        self.episode += 1
        self.step_num = 0

        self.game = self.game_editor.generate_game()
        obs = self.game.observations
        events = self.config_loader.config['event']
        resource_name_list = [resource.name for resource in self.game.resources]
        event_in_name_list = sum([list(events[e.name]['in'].keys()) for e in self.game.events],[])
        event_out_name_list = sum([list(events[e.name]['out'].keys()) for e in self.game.events],[])
        resource_name = list(set(resource_name_list + event_in_name_list + event_out_name_list))
        node_list = self.game.social.get_node_list()
        player_num = len(self.game.players)
        group_num = len(self.game.social.group_dict)
        random_seed = random.randint(0, 2**32-1)
        
        infos = {player.name: {
            'episode_id': self.episode,
            'step_id': self.step_num,
            'max_length': self.game.max_length,
            'map_size': self.game.world_map.shape,
            'seed': random_seed,
            'group_num': group_num,
            'player_num': player_num,
            '_id': player._id,
            'obs_range': player.fov,
            'inventory_capacity': player.resource_max_dict,
            'events':events,
            'resource_name': resource_name,
            'resource_num': len(resource_name),
            'player_num': player_num,
            'group_num': group_num,
            'map_size': self.game.world_map.shape,
            'communication_length': self.config_loader.config.task.static.communication_length,
            'nodes': node_list,
            'obs_range': player.fov,
            "max_length": self.game.max_length,
            'inventory_capacity': player.resource_max_dict,
            'nodes': node_list,
            "negotiation_steps":self.config_loader.config.task.negotiation.get('negotiation_steps', 0),
            "claim_proposal_interval":self.config_loader.config.task.negotiation.get('claim_proposal_interval', 0),
        } for player in self.game.players}

        self.rendering.load_game(self.game)

        return obs, infos

    def step(
        self,
        action_dict,
    ):
        self.game.pre_update()
        self.game.update(action_dict)
        self.rendering.render_frame()
        self.game.post_update()
        next_obs = self.game.observations
        rewards = self.game.rewards
        terminateds = self.game.terminateds
        # TODO Add an agent callback func
        truncateds = {_id: v for _id, v in terminateds.items()}
        self.step_num += 1
        infos = {player.name: {
            'step': self.step_num,
        } for player in self.game.players}

        return (
            next_obs,
            rewards,
            terminateds,
            truncateds,
            infos,
        )

    def render(self):
        pass

    def save_video(self):
        self.rendering.save_video()


