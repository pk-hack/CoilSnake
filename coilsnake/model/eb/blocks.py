import logging

from coilsnake.model.common.blocks import Block
from coilsnake.modules.eb import EbModule
from coilsnake.modules.eb.exceptions import InvalidEbCompressedDataError


log = logging.getLogger(__name__)


class EbCompressibleBlock(Block):
    def from_block_compressed(self, block, offset=0):
        self.data = EbModule.decomp(block, offset)
        if self.data[0] < 0:
            raise InvalidEbCompressedDataError("Couldn't decompress invalid data")
        self.size = len(self.data)

    def to_block_compressed(self, block, offset=0):
        compressed_data = EbModule.comp(self.to_list())
        block[offset:offset + len(compressed_data)] = compressed_data