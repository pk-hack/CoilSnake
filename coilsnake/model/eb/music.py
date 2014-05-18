import abc
import logging

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.util.common.type import StringRepresentationMixin
from coilsnake.util.common.yml import yml_dump


log = logging.getLogger(__name__)


class Chunk(object):
    def __init__(self, spc_address, data):
        if spc_address + len(data) > 0x10000:
            raise InvalidArgumentError(
                ("Could not create chunk with spc_address[{:#x}] and data of length[{}] as it would exceed "
                 "the bounds of the SPC's memory").format(spc_address, len(data)))

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


class Sequence(object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    def create_from_chunk(cls, chunk, bgm_id, sequence_pack_id):
        return ChunkSequence(chunk=chunk, bgm_id=bgm_id, sequence_pack_id=sequence_pack_id)

    @classmethod
    def create_from_spc_address(cls, spc_address, bgm_id, sequence_pack_id):
        return Subsequence(spc_address=spc_address, bgm_id=bgm_id, sequence_pack_id=sequence_pack_id)

    @abc.abstractmethod
    def to_resource(self, resource_open, sequence_pack_map):
        """Write the sequence to a resource file"""
        return

    @abc.abstractmethod
    def contains_spc_address(self, spc_address):
        """Returns true iff this sequence is contains data at the given address"""
        return

    @abc.abstractmethod
    def get_spc_address(self):
        """Returns the address of this sequence in SPC memory"""
        return


class ChunkSequence(StringRepresentationMixin, Sequence):
    def __init__(self, chunk, bgm_id, sequence_pack_id):
        self.chunk = chunk
        self.bgm_id = bgm_id
        self.sequence_pack_id = sequence_pack_id

    @staticmethod
    def _resource_open_sequence(resource_open, bgm_id):
        return resource_open("Music/sequences/{:03d}".format(bgm_id), "ebm")

    def to_resource(self, resource_open, sequence_pack_map):
        with ChunkSequence._resource_open_sequence(resource_open, self.bgm_id) as f:
            self.chunk.to_file(f)

    def contains_spc_address(self, spc_address):
        return self.chunk.spc_address <= spc_address < (self.chunk.spc_address + self.chunk.data_size())

    def get_spc_address(self):
        return self.chunk.spc_address


class Subsequence(StringRepresentationMixin, Sequence):
    def __init__(self, spc_address, bgm_id, sequence_pack_id):
        self.spc_address = spc_address
        self.bgm_id = bgm_id
        self.sequence_pack_id = sequence_pack_id

    @staticmethod
    def _resource_open_sequence(resource_open, bgm_id):
        return resource_open("Music/sequences/{:03d}".format(bgm_id), "yml")

    def to_resource(self, resource_open,  sequence_pack_map):
        # Get a list of possible sequence which this could be a subsequence of.
        # A subsequence can be of any sequence which is loaded. Sequences will only be loaded if they are either in
        # the loaded sequence pack or the program pack (1).
        if self.sequence_pack_id == 0xff:
            possible_sequences = []
        else:
            possible_sequences = sequence_pack_map[self.sequence_pack_id]

        if self.sequence_pack_id != 1:
            possible_sequences += sequence_pack_map[1]

        for possible_sequence in possible_sequences:
            if possible_sequence.contains_spc_address(self.spc_address):
                offset_in_sequence = self.spc_address - possible_sequence.get_spc_address()

                yml_rep = {"type": "subsequence",
                           "song": possible_sequence.bgm_id,
                           "offset": offset_in_sequence}
                with Subsequence._resource_open_sequence(resource_open, self.bgm_id) as f:
                    yml_dump(yml_rep=yml_rep, f=f, default_flow_style=False)
                break
        else:
            # This subsequence does not match against any sequence, so it must be invalid.
            # Don't write it to any resources.
            log.error("{} did not match any sequence, not saving it to the project".format(self))

    def contains_spc_address(self, spc_address):
        return False

    def get_spc_address(self):
        return self.spc_address