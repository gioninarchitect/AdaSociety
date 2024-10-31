import numpy as np
import pygame

from .canvas import Canvas


class Render:
    def __init__(self, config):
        self.config = config
        self.render_mode = config['mode']

        if self.render_mode not in ['human', 'rgb_array']:
            self.render_frame = self._render_frame_null
            return

        self.render_fps = config['fps']
        self.step_frames = config['step_frames']
        self.screen_w = config['screen']['width']
        self.screen_h = config['screen']['height']
        self.tileset_path = config['tileset_path']
        # visibility
        self.visible_resource = config['visible_resource']

        self.frame_id = 0
        if self.render_mode == 'human':
            self._pygame_init()
            self.render_frame = self._render_frame_human
        elif self.render_mode == 'rgb_array':
            self.render_frame = self._render_frame_rgb_array
        self.screen.set_colorkey((0, 0, 0))

    def load_game(self, game):
        if self.render_mode not in ['human', 'rbg_array']:
            return
        self.game = game
        # Canvas
        self.canvas = Canvas(
            tile_size=(48, 48),
            tileset_path=self.tileset_path,
            step_frames=self.step_frames,
        )
        self.canvas.load_game(self.game)
        self.canvas.update(
            visible_resource=self.visible_resource,
        )
        self.draw()
        #self.render_frame()

    def draw(self):
        self.canvas.draw(self.screen)
        pygame.display.flip()

    def tick(self):
        self.clock.tick(self.render_fps)
        self.frame_id += 1

    def render(self):
        return self.render_frame()

    def _pygame_init(self):
        pygame.init()
        pygame.display.init()
        # Screen window
        self.screen = pygame.display.set_mode(
            (self.screen_w, self.screen_h)
        )
        self.screen.fill(pygame.Color(30, 188, 115, 100))
        #os.environ['SDL_VIDEO_WINDOW_POS'] = center_win
        pygame.display.set_caption('AdaSociety - Brave New World')
        # Clock
        self.clock = pygame.time.Clock()
        self.clock.tick(self.render_fps)

    def _render_frame_human(self):
        for _ in range(self.step_frames):
            self.canvas.update(
                frame_id=self.frame_id,
                visible_resource=self.visible_resource,
            )
            self.draw()
            self.tick()

    def _render_frame_rgb_array(self):
        self.canvas.update(
            visible_resource=self.visible_resource,
        )
        self.draw()
        return np.transpose(
            np.array(pygame.surfarray.pixels3d(canvas)), axes=(1, 0, 2)
        )

    def _render_frame_null(self):
        pass
