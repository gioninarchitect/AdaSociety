import random
import numpy as np

BLANK = 0
BLOCK = 1

UP = np.array([0, -1])
DOWN = np.array([0, 1])
LEFT = np.array([-1, 0])
RIGHT = np.array([1, 0])
UPPER_LEFT = UP + LEFT
UPPER_RIGHT = UP + RIGHT
LOWER_LEFT = DOWN + LEFT
LOWER_RIGHT = DOWN + RIGHT


class WorldMap:
    def __init__(
        self,
        # [[token_row_0_col_0, token_row_0_col_1, ...], [token_row_1_col_0, ...]]
        token_array,
        token_lookup_table=None,
    ):
        if token_lookup_table is None:
            self.token_lookup_table = self._generate_token_lookup_table(token_array)
        else:
            self.token_lookup_table = token_lookup_table
        self.block_lookup_table = {k: v for k, v in self.token_lookup_table.items() if v == BLOCK}
        self.token_array = token_array
        self.map_data = [list(map(self.token_lookup_table.get, row)) for row in self.token_array]
        assert np.all(self.map_data != None)
        self.map_data = np.array(self.map_data)
        self.size_y, self.size_x = self.map_data.shape
        # Blank positions
        self.blank_pos = set(map(tuple, np.argwhere(self.map_data.T == BLANK).tolist()))

    @property
    def shape(self):
        return self.size_x, self.size_y

    @property
    def observation(self):
        return self.map_data

    def add_block(self, position):
        choices = set()
        for delta_pos in [UP, DOWN, LEFT, RIGHT, UPPER_LEFT, UPPER_RIGHT, LOWER_LEFT, LOWER_RIGHT]:
            x = (position[0] + delta_pos[0]) % self.size_x
            y = (position[1] + delta_pos[1]) % self.size_y
            if self.map_data[y, x] == BLOCK:
                choices.add(self.token_array[y][x])
        if not choices:
            choices = set(self.block_lookup_table.keys())
        token = random.choice(list(choices))
        x, y = position
        self.map_data[y, x] = BLOCK
        self.token_array[y][x] = token
        # Remove (x, y) from blanks if existed
        self.blank_pos.discard((x, y))

    def add_blocks(self, positions):
        for pos in positions:
            self.add_block(pos)

    def is_block(self, position):
        return self.map_data[position[1], position[0]] == BLOCK

    def grids(self, x_start, x_end, y_start, y_end):
        rows = np.arange(y_start, y_end) % self.size_y
        cols = np.arange(x_start, x_end) % self.size_x
        return self.map_data[rows][:, cols]

    def pretty_print(self):
        s = '\n'.join([''.join(row) for row in self.token_array])
        print(s)

    def _generate_token_lookup_table(self, token_array):
        # All tokens are blocks except SPACE
        # The length of all tokens must be same
        token_set = set().union(*token_array)
        token_lookup_table = {t: BLOCK for t in token_set}
        token_lookup_table[' ' * len(token_array[0][0])] = BLANK
        return token_lookup_table
