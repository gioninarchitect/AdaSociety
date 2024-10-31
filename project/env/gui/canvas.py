import pygame

from .cell import Cell
from .player import Player


class Canvas:
    def __init__(
        self,
        tile_size,
        tileset_path,
        step_frames=1,
    ):
        self.tile_w, self.tile_h = tile_size
        self.offset_x = 0
        self.offset_y = 0
        self.layers = []
        self.num_layer = len(self.layers)
        self.players = pygame.sprite.Group()
        # Load tileset
        self.tileset = pygame.image.load(tileset_path).convert_alpha()
        self.tileset.set_colorkey((0, 0, 0))
        self.step_frames = step_frames

    def reset_layer(self):
        self.layers = []

    def add_layer(self, layer):
        self.layers.append(layer)
        self.num_layer += 1

    def load_game(self, game):
        self.game = game
        self.load_player(self.game.players)

    def load_map(self, world_map):
        self.map_h, self.map_w = world_map.shape
        grid = []
        for y in range(self.map_h):
            grid.append([])
            for x in range(self.map_w):
                grid[y].append(Cell(
                    _id=world_map.token_array[y][x],
                    x=x*self.tile_w,
                    y=y*self.tile_h,
                    width=self.tile_w,
                    height=self.tile_h,
                ))
        self.add_layer(grid)

    def load_event(self, event_dict):
        units = []
        for pos, event in event_dict.items():
            units.append(Cell(
                _id=event.name,
                x=pos[0]*self.tile_w,
                y=pos[1]*self.tile_h,
                width=self.tile_w,
                height=self.tile_h,
            ))
        self.add_layer(units)

    def load_all_resource(self, resource_dict):
        units = []
        for pos, resource in resource_dict.items():
            units.append(Cell(
                _id=resource.name,
                x=pos[0]*self.tile_w,
                y=pos[1]*self.tile_h,
                width=self.tile_w,
                height=self.tile_h,
            ))
        self.add_layer(units)

    def load_global_resource(self, resource_dict, players):
        units = []
        for pos, resource in resource_dict.items():
            visible = False
            while resource:
                for player in players:
                    if resource.check_visible(player):
                        visible = True
                        break
                if visible:
                    break
                else:
                    resource = resource.stacked_resource
            if visible:
                units.append(Cell(
                    _id=resource.name,
                    x=pos[0]*self.tile_w,
                    y=pos[1]*self.tile_h,
                    width=self.tile_w,
                    height=self.tile_h,
                ))
        self.add_layer(units)

    def load_local_resource(self, players):
        units = []
        for player in players:
            for resource in player.visible_resources:
                units.append(Cell(
                    _id=resource.name,
                    x=resource.position[0]*self.tile_w,
                    y=resource.position[1]*self.tile_h,
                    width=self.tile_w,
                    height=self.tile_h,
                ))
        self.add_layer(units)

    def load_player(self, players):
        for player in players:
            self.players.add(Player(
                player=player,
                width=self.tile_w,
                height=self.tile_h,
                tileset=self.tileset,
                step_frames=self.step_frames,
            ))

    def update(self, frame_id=0, visible_resource='global'):
        frame_offset = frame_id % self.step_frames
        self.reset_layer()
        self.load_map(self.game.world_map)
        self.load_event(self.game.event_dict)
        if visible_resource == 'all':
            self.load_all_resource(self.game.resource_dict)
        elif visible_resource == 'global':
            self.load_global_resource(self.game.resource_dict, self.game.players)
        elif visible_resource == 'local':
            self.load_local_resource(self.game.players)
        self.players.update(frame_offset=frame_offset)

    def draw(self, surface):
        grid = self.layers[0]
        for y in range(self.map_h):
            for x in range(self.map_w):
                cell = grid[y][x]
                dest = pygame.Rect(
                    x * self.tile_w + self.offset_x,
                    y * self.tile_h + self.offset_y,
                    self.tile_w,
                    self.tile_h,
                )
                surface.blit(self.tileset, dest, cell.src_rect)
                surface.set_colorkey((0, 0, 0))
        for units in self.layers[1:]:
            for cell in units:
                dest = pygame.Rect(
                    #x * self.tile_w + self.offset_x,
                    #y * self.tile_h + self.offset_y,
                    cell.x + self.offset_x,
                    cell.y + self.offset_y,
                    self.tile_w,
                    self.tile_h,
                )
                surface.blit(self.tileset, dest, cell.src_rect)
                surface.set_colorkey((0, 0, 0))
        self.players.draw(surface)
