import pygame

SRC_POS = [
    (1, 0),
    (22, 1),
    (2, 109),
    (7, 35),
    (16, 37),
    (13, 111),
    (1, 112),
    (11, 114),
    #(41, 40),
    #(38, 16),
]
SRC_NUM = len(SRC_POS)


class Player(pygame.sprite.Sprite):
    def __init__(self, player, width, height, tileset, step_frames=1):
        super().__init__()
        self.player = player
        self.total_player_num = player.game.player_num
        self.width = width
        self.height = height
        self.step_frames = step_frames
        src_x, src_y = SRC_POS[self.player._id % SRC_NUM]
        src_rect = pygame.Rect(src_x * width, src_y * height, width, height)
        dest_rect = pygame.Rect(0, 0, width, height)
        self.image = pygame.Surface([width, height]).convert()
        self.image.blit(tileset, dest_rect, src_rect)
        self.image.set_colorkey((0, 0, 0))
        self._shift_color(self.image, self.player._id, self.total_player_num)
        self.rect = self.image.get_rect()
        self.update()

    def update(self, frame_offset=0):
        p = frame_offset / self.step_frames
        x0, y0 = self.player.position
        x1, y1 = self.player.next_position
        self.rect.x = (x0 * (1 - p) + x1 * p) * self.width
        self.rect.y = (y0 * (1 - p) + y1 * p) * self.height

    def _shift_color(self, surface, offset_id, offset_max):
        pixels = pygame.PixelArray(surface)
        colorkey = surface.get_colorkey()
        offset_h = (offset_id // SRC_NUM) / ((offset_max // SRC_NUM) + 1) * 360
        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                color = surface.unmap_rgb(pixels[x][y])
                if color == colorkey:
                    continue
                h, s, l, a = color.hsla
                h = (h + offset_h) % 360
                color.hsla = (h, s, l, a)
                pixels[x][y] = color
