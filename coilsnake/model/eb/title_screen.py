CHARS_NUM_TILES = 1024


class TitleScreenLayoutEntry(object):

    SINGLE_FLAG = 0x01
    FINAL_FLAG = 0x80

    def __init__(self, x=0, y=0, tile=0, flags=0, unknown=12):
        self.x = x
        self.y = y
        self.tile = tile
        self.flags = flags
        self.unknown = unknown

    def from_block(self, block, offset=0):
        y = block[offset]
        self.y = y if y < 128 else -(256-y)  # Read signed value
        tile_bytes = block.read_multi(offset+1, 2)
        self.tile = tile_bytes & (CHARS_NUM_TILES - 1)
        self.unknown = tile_bytes >> (CHARS_NUM_TILES - 1).bit_length()
        x = block[offset+3]
        self.x = x if x < 128 else -(256-x)  # Read signed value
        self.flags = block[offset+4]

    def to_block(self, block, offset=0):
        block[offset] = self.y if self.y >= 0 else self.y+256
        block.write_multi(
            offset+1,
            self.tile | self.unknown << (CHARS_NUM_TILES - 1).bit_length(), 2
        )
        block[offset+3] = self.x if self.x >= 0 else self.x+256
        block[offset+4] = self.flags

    @staticmethod
    def block_size():
        return 5

    def is_single(self):
        return (self.flags & self.SINGLE_FLAG) == 0

    def set_single(self, single=True):
        if single:
            self.flags |= self.SINGLE_FLAG
        else:
            self.flags &= ~self.SINGLE_FLAG

    def is_final(self):
        return (self.flags & self.FINAL_FLAG) != 0

    def set_final(self, final=True):
        if final:
            self.flags |= self.FINAL_FLAG
        else:
            self.flags &= ~self.FINAL_FLAG

    def __str__(self):
        return "<tile={}, x={}, y={}, flags={}, unknown={}>".format(
            self.tile & (CHARS_NUM_TILES - 1), self.x, self.y,
            bin(self.flags)[2:], self.unknown
        )
