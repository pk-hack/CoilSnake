import logging

from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.eb.music import read_pack, get_sequence_as_chunk
from coilsnake.util.eb.pointer import from_snes_address


log = logging.getLogger(__name__)

PACK_POINTER_TABLE_OFFSET = 0xC4F947
MUSIC_DATASET_TABLE_OFFSET = 0xC4F70A


def resource_open_sequence(resource_open, sequence_id):
    return resource_open("Music/sequences/{:03d}".format(sequence_id), "ebm")


class MusicModule(EbModule):
    NAME = "Music"

    def __init__(self):
        super(MusicModule, self).__init__()
        self.pack_pointer_table = eb_table_from_offset(offset=PACK_POINTER_TABLE_OFFSET)
        self.music_dataset_table = eb_table_from_offset(offset=MUSIC_DATASET_TABLE_OFFSET)
        self.sequences = []

    def read_from_rom(self, rom):
        self.pack_pointer_table.from_block(block=rom, offset=from_snes_address(PACK_POINTER_TABLE_OFFSET))
        self.music_dataset_table.from_block(block=rom, offset=from_snes_address(MUSIC_DATASET_TABLE_OFFSET))
        self.sequences = [None] * self.music_dataset_table.num_rows

        # Read the packs
        pack_offsets = [from_snes_address(self.pack_pointer_table[i][0])
                        for i in range(self.pack_pointer_table.num_rows)]
        packs = [read_pack(rom, x) for x in pack_offsets]
        program = packs[1][0x0500].data

        # Read the sequences
        for bgm_id in range(self.music_dataset_table.num_rows):
            sequence_pack_id = self.music_dataset_table[bgm_id][2]
            log.info("Reading sequence for BGM {:#x} using sequence pack[{:#x}]".format(bgm_id+1, sequence_pack_id))
            if sequence_pack_id == 0xff:
                sequence_pack = None
            else:
                sequence_pack = packs[sequence_pack_id]
            sequence_chunk = get_sequence_as_chunk(bgm_id=bgm_id, program=program, sequence_pack=sequence_pack)
            self.sequences[bgm_id] = sequence_chunk

    def write_to_project(self, resource_open):
        for bgm_id, sequence in enumerate(self.sequences):
            with resource_open_sequence(resource_open, bgm_id) as f:
                if sequence:
                    sequence.to_file(f)