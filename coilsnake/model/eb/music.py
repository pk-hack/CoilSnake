from coilsnake.exceptions.common.exceptions import CoilSnakeError


class Chunk(object):
    def __init__(self, spc_address, data):
        if spc_address + len(data) > 0x10000:
            raise CoilSnakeError("Invalid chunk, stretches past SPC memory")

        self.spc_address = spc_address
        self.data = data

    @classmethod
    def create_from_block(cls, block, offset):
        size = block.read_multi(offset, 2)
        if size == 0:
            return None

        spc_address = block.read_multi(offset + 2, 2)
        data = block[offset + 4:offset + 4 + size]
        return Chunk(spc_address=spc_address, data=data)

    def to_file(self, f):
        data_size = self.data_size()
        f.write(bytearray([data_size & 0xff, data_size >> 8, self.spc_address & 0xff, self.spc_address >> 8]))
        self.data.to_file(f)

    def data_size(self):
        return len(self.data)

    def chunk_size(self):
        return 4 + self.data_size()