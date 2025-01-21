import cv2
import pygame
import numpy as np
import os
from .canvas import Canvas


class Render:
    def __init__(self, config):
        self.config = config
        self.render_mode = config['mode']
        self.render_fps = config['fps']
        self.step_frames = config['step_frames']
        self.screen_w = config['screen']['width']
        self.screen_h = config['screen']['height']
        self.tileset_path = config['tileset_path']
        self.visible_resource = config['visible_resource']

        self.frame_id = 0
        self.saved_video = 0
        self.video_writer_initialized = False

        if self.render_mode in ['human', 'rgb_array', 'video']:
            self._pygame_init()
            self.render_frame = self._render_frame_rgb_array if self.render_mode == 'rgb_array' else self._render_frame_human
        else:
            self.render_frame = self._render_frame_null
            return

        self.canvas = None

    def load_game(self, game):
        if self.render_mode not in ['human', 'rgb_array', 'video']:
            return
        self.game = game
        self.canvas = Canvas(
            tile_size=(48, 48),
            tileset_path=self.tileset_path,
            step_frames=self.step_frames,
        )
        self.canvas.load_game(self.game)
        self.canvas.update(visible_resource=self.visible_resource)
        self.draw()

    def draw(self):
        self.canvas.draw(self.screen)
        if self.render_mode != 'video':
            pygame.display.flip()

    def tick(self):
        self.clock.tick(self.render_fps)
        self.frame_id += 1

    def render(self):
        return self.render_frame()

    def _pygame_init(self):
        pygame.init()
        pygame.display.init()
        if self.render_mode != 'video':
            self.screen = pygame.display.set_mode(
                (self.screen_w, self.screen_h)
            )
        else:
            self.screen = pygame.Surface((self.screen_w, self.screen_h))
            pygame.display.set_mode((self.screen_w, self.screen_h))

        self.screen.fill(pygame.Color(30, 188, 115, 100))
        pygame.display.set_caption('AdaSociety - Brave New World')
        self.clock = pygame.time.Clock()
        self.clock.tick(self.render_fps)

    def _render_frame_human(self):
        for _ in range(self.step_frames):
            if self.canvas:
                self.canvas.update(frame_id=self.frame_id, visible_resource=self.visible_resource)
                self.draw()
                self.tick()

            if self.render_mode in ['human', 'video']:
                frame = np.transpose(np.array(pygame.surfarray.pixels3d(self.screen)), axes=(1, 0, 2))
                frame = frame[..., ::-1]
                self._write_frame_to_video(frame)

    def _render_frame_rgb_array(self):
        if self.canvas:
            self.canvas.update(visible_resource=self.visible_resource)
            self.draw()
            frame = np.transpose(np.array(pygame.surfarray.pixels3d(self.screen)), axes=(1, 0, 2))
            if self.render_mode == 'rgb_array':
                self._write_frame_to_video(frame)
            return frame

    def _render_frame_null(self):
        pass

    def _write_frame_to_video(self, frame):
        if not self.video_writer_initialized:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            name = 'output_video_' + str(self.saved_video) + '.avi'
            self.out = cv2.VideoWriter(name, fourcc, self.render_fps, (self.screen_w, self.screen_h))
            self.video_writer_initialized = True

        self.out.write(frame)

    def close(self):
        if self.render_mode in ['rgb_array', 'human']:
            if hasattr(self, 'out'):
                self.out.release()
                self.video_writer_initialized = False
                print(f"Video saved as output_video_{self.saved_video}.avi")
            else:
                print("Warning: Video writer was not initialized. No video to save.")
            self.saved_video += 1

    def rerender(self):
        if self.render_mode in ['rgb_array', 'human', 'video']:
            if self.video_writer_initialized:
                self._write_frame_to_video(self.frame)

    def save_video(self):
        self.close()
        if self.render_mode in ['human', 'rgb_array', 'video']:
            print("save video successfully")
        self.rerender()

    def _render_frame_null(self):
        pass
