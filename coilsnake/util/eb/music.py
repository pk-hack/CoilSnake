import logging

from coilsnake.model.eb.music import Chunk


log = logging.getLogger(__name__)


def read_pack(block, offset):
    pack = dict()

    while True:
        chunk = Chunk.from_block(block, offset)
        if chunk is None:
            break
        pack[chunk.spc_address] = chunk
        offset += chunk.chunk_size()

    return pack


def get_sequence_pointer(bgm_id, program):
    return program.read_multi(0x294c + bgm_id*2, 2)


def get_sequence_as_chunk(bgm_id, program, sequence_pack):
    sequence_pointer = get_sequence_pointer(bgm_id=bgm_id, program=program)
    log.debug("Reading sequence for BGM {:#x} from address[{:#x}]".format(bgm_id+1, sequence_pointer))
    if sequence_pack and sequence_pointer in sequence_pack:
        return sequence_pack[sequence_pointer]
    # TODO read in sequences bundled with the program using hardcoded lengths
    log.error("Attempted to read sequence @ {:#x} which is not in a sequence chunk".format(sequence_pointer))
    return None

