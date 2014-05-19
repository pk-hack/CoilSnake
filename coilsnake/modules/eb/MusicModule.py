import logging

from coilsnake.model.eb.music import EbInstrumentSet, EbNoteStyles
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.eb.music import read_pack, create_sequence
from coilsnake.util.eb.pointer import from_snes_address


log = logging.getLogger(__name__)

PACK_POINTER_TABLE_OFFSET = 0xC4F947
MUSIC_DATASET_TABLE_OFFSET = 0xC4F70A


class MusicModule(EbModule):
    NAME = "Music"

    def __init__(self):
        super(MusicModule, self).__init__()
        self.pack_pointer_table = eb_table_from_offset(offset=PACK_POINTER_TABLE_OFFSET)
        self.music_dataset_table = eb_table_from_offset(offset=MUSIC_DATASET_TABLE_OFFSET)

        self.note_styles = EbNoteStyles()
        self.instrument_sets = []
        self.sequences = []

    def read_from_rom(self, rom):
        self.pack_pointer_table.from_block(block=rom, offset=from_snes_address(PACK_POINTER_TABLE_OFFSET))
        self.music_dataset_table.from_block(block=rom, offset=from_snes_address(MUSIC_DATASET_TABLE_OFFSET))
        self.instrument_sets = [None] * 255
        self.sequences = [None] * (self.music_dataset_table.num_rows + 1)

        # Read the packs
        pack_offsets = [from_snes_address(self.pack_pointer_table[i][0])
                        for i in range(self.pack_pointer_table.num_rows)]
        packs = [read_pack(rom, x) for x in pack_offsets]
        program_chunk = packs[1][0x0500]

        self.note_styles.read_from_packs(packs)

        # Read the pack ids which are used as instrument packs by BGMs
        instrument_pack_ids = reduce(lambda x, y: x.union(y),
                                     [[self.music_dataset_table[bgm_id][0], self.music_dataset_table[bgm_id][1]]
                                         for bgm_id in range(self.music_dataset_table.num_rows)],
                                     set())
         # Pack 1 is always loaded in SPC memory so it's not loaded by a BGM, but it does have instruments in it
        instrument_pack_ids.update([1])
        for instrument_pack_id in instrument_pack_ids:
            if instrument_pack_id == 0xff:
                continue
            pack = packs[instrument_pack_id]
            log.debug("Reading instrument set from pack #{}".format(instrument_pack_id))
            self.instrument_sets[instrument_pack_id] = EbInstrumentSet.create_from_pack(pack)

        # Read the sequences
        for bgm_id in range(1, self.music_dataset_table.num_rows+1):
            sequence_pack_id = self.music_dataset_table[bgm_id-1][2]
            log.info("Reading sequence for BGM {:#x} using sequence pack[{:#x}]".format(bgm_id, sequence_pack_id))
            if sequence_pack_id == 0xff:
                sequence_pack = None
            else:
                sequence_pack = packs[sequence_pack_id]
            self.sequences[bgm_id] = create_sequence(bgm_id=bgm_id,
                                                     sequence_pack_id=sequence_pack_id,
                                                     sequence_pack=sequence_pack,
                                                     program_chunk=program_chunk)

    def write_to_project(self, resource_open):
        self.note_styles.write_to_project(resource_open)

        sequence_pack_map = dict()
        for sequence in self.sequences[1:]:
            sequence_pack_id = sequence.sequence_pack_id
            if sequence_pack_id in sequence_pack_map:
                sequence_pack_map[sequence_pack_id].append(sequence)
            else:
                sequence_pack_map[sequence_pack_id] = [sequence]

        for sequence in self.sequences[1:]:
            sequence.write_to_project(resource_open=resource_open,
                                      sequence_pack_map=sequence_pack_map)

        for instrument_set_id, instrument_set in enumerate(self.instrument_sets):
            if instrument_set is None:
                continue
            instrument_set.write_to_project(resource_open=resource_open, instrument_set_id=instrument_set_id)