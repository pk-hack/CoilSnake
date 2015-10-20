import logging

from coilsnake.exceptions.common.exceptions import ResourceNotFoundError
from coilsnake.model.eb.music import EbInstrumentSet, EbNoteStyles, ChunkSequence, Subsequence, Chunk
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import yml_dump, yml_load
from coilsnake.util.eb.music import read_pack, create_sequence, remove_sequences_from_program_chunk, write_pack
from coilsnake.util.eb.pointer import from_snes_address


log = logging.getLogger(__name__)

PACK_POINTER_TABLE_OFFSET = 0xC4F947
MUSIC_DATASET_TABLE_OFFSET = 0xC4F70A


class MusicModule(EbModule):
    NAME = "Music"

    def __init__(self):
        super(MusicModule, self).__init__()
        self.pack_pointer_table = eb_table_from_offset(offset=PACK_POINTER_TABLE_OFFSET)
        self.music_dataset_table = eb_table_from_offset(offset=MUSIC_DATASET_TABLE_OFFSET,
                                                        hidden_columns=["Sequence Set"])

        self.note_styles = EbNoteStyles()
        self.instrument_sets = []
        self.sequences = []
        self.program_chunk = None

    def read_from_rom(self, rom):
        self.pack_pointer_table.from_block(block=rom, offset=from_snes_address(PACK_POINTER_TABLE_OFFSET))
        self.music_dataset_table.from_block(block=rom, offset=from_snes_address(MUSIC_DATASET_TABLE_OFFSET))
        self.instrument_sets = [None] * 255
        self.sequences = [None] * (self.music_dataset_table.num_rows + 1)

        # Read the packs
        pack_offsets = [from_snes_address(self.pack_pointer_table[i][0])
                        for i in range(self.pack_pointer_table.num_rows)]
        packs = [read_pack(rom, x) for x in pack_offsets]
        self.program_chunk = packs[1][0x0500]

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
                                                     program_chunk=self.program_chunk)

        remove_sequences_from_program_chunk(self.program_chunk)

    def write_to_rom(self, rom):
        # 0a. Determine which packs are primary instrument packs, and which are secondary
        instrument_pack_ids = reduce(lambda x, y: x.union(y),
                                     [[self.music_dataset_table[bgm_id][0], self.music_dataset_table[bgm_id][1]]
                                         for bgm_id in range(self.music_dataset_table.num_rows)],
                                     set())
        instrument_pack_ids.update(1)
        primary_instrument_pack_ids = reduce(lambda x, y: x.union(y),
                                             [[self.music_dataset_table[bgm_id][0]]
                                              for bgm_id in range(self.music_dataset_table.num_rows)],
                                             set())
        primary_instrument_pack_ids.update(1)
        secondary_instrument_pack_ids = instrument_pack_ids - primary_instrument_pack_ids

        # 0b. Determine which other instrument packs are used in conjunction with all instrument packs
        instrument_pack_partner_pack_ids = dict()
        for primary_instrument_pack_id in primary_instrument_pack_ids:
            instrument_pack_partner_pack_ids[primary_instrument_pack_id] = {1}
        for secondary_instrument_pack_id in secondary_instrument_pack_ids:
            partner_pack_ids = {1}
            for bgm_id in range(self.music_dataset_table.num_rows):
                if self.music_dataset_table[bgm_id][1] == secondary_instrument_pack_id:
                    partner_pack_ids.update(self.music_dataset_table[bgm_id][0])

        # 1. Put all of the chunks into packs
        packs = [dict() for x in range(256)]
        free_pack_ids = set(range(256)) - instrument_pack_ids

        # 1a. Put the program chunk into pack 1, offset 0x500
        packs[1][0x0500] = self.program_chunk

        # 1b. Write the note styles chunk to pack 1
        self.note_styles.write_to_pack(packs[1])

        # 1c. Insert the primary instrument packs
        for pack_id, instrument_set in [(x, self.instrument_sets[x]) for x in primary_instrument_pack_ids]:
            instrument_set.write_to_pack(
                packs=packs,
                pack_id=pack_id,
                partner_pack_ids=instrument_pack_partner_pack_ids[pack_id])

        # 1d. Insert the secondary instrument packs
        for pack_id, instrument_set in [(x, self.instrument_sets[x]) for x in secondary_instrument_pack_ids]:
            instrument_set.write_to_pack(
                packs=packs,
                pack_id=pack_id,
                partner_pack_ids=instrument_pack_partner_pack_ids[pack_id])

        # 1e. Insert the "always loaded" sequences
        bgm_spc_offsets = {}
        for bgm_id, sequence in zip(range(1, len(self.sequences)), self.sequences):
            if not sequence.is_always_loaded:
                continue

            self.music_dataset_table[bgm_id][2] = 1

            sequence_offset = sequence.write_to_pack(
                packs=packs,
                pack_id=1,
                partner_pack_ids={},
                chunk_size=sequence.chunk.size())
            bgm_spc_offsets[bgm_id] = sequence_offset

        # 1f. Insert the other sequences
        subsequence_ids = []
        for bgm_id, sequence in zip(range(1, len(self.sequences)), self.sequences):
            if sequence is not ChunkSequence:
                subsequence_ids.append(bgm_id)
                continue

            pack_id = free_pack_ids.pop()
            self.music_dataset_table[bgm_id][2] = pack_id

            partner_pack_ids = {1}
            for instrument_pack_id in self.music_dataset_table[bgm_id][0:2]:
                if instrument_pack_id:
                    partner_pack_ids.add(instrument_pack_id)

            sequence_offset = sequence.write_to_pack(
                packs=packs,
                pack_id=pack_id,
                partner_pack_ids=partner_pack_ids)
            bgm_spc_offsets[bgm_id] = sequence_offset

        # 2. Write packs to the rom
        for pack_id, pack in enumerate(packs):
            if pack:
                pack_offset = write_pack(rom, x)
                self.pack_pointer_table[pack_id][0] = pack_offset
            else:
                self.pack_pointer_table[pack_id][0] = 0

        # 3. Write the data tables
        # 3a. Set up references for the subsequences
        for bgm_id, sequence in zip(range(1, len(self.sequences)), self.sequences):
            if sequence is not Subsequence:
                continue

            pack_id = self.music_dataset_table[sequence.source_bgm_id][2]
            self.music_dataset_table[bgm_id][2] = pack_id

            base_spc_offset = bgm_spc_offsets[bgm_id]
            bgm_spc_offsets[bgm_id] = base_spc_offset + sequence.source_bgm_offset

        # 3b. Write the data tables to the rom
        self.pack_pointer_table.to_block(block=rom, offset=from_snes_address(PACK_POINTER_TABLE_OFFSET))
        self.music_dataset_table.to_block(block=rom, offset=from_snes_address(MUSIC_DATASET_TABLE_OFFSET))

    def write_to_project(self, resource_open):
        self.note_styles.write_to_project(resource_open)
        with resource_open("Music/songs", "yml") as f:
            self.music_dataset_table.to_yml_file(f)
        with resource_open("Music/program", "bin") as f:
            self.program_chunk.to_file(f)

        always_loaded_songs = [x.bgm_id
                               for x in self.sequences
                               if x.is_always_loaded]
        with resource_open("Music/always_loaded_songs", "yml") as f:
            yml_dump(always_loaded_songs, f)

        self.write_sequences_to_project(resource_open)
        self.write_instruments_to_project(resource_open)

    def write_sequences_to_project(self, resource_open):
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

    def write_instruments_to_project(self, resource_open):
        for instrument_set_id, instrument_set in enumerate(self.instrument_sets):
            if instrument_set is None:
                continue
            instrument_set.write_to_project(resource_open=resource_open, instrument_set_id=instrument_set_id)

    def read_from_project(self, resource_open):
        self.instrument_sets = [None] * 255
        self.sequences = [None] * (self.music_dataset_table.num_rows + 1)

        log.debug("Reading note styles")
        self.note_styles.read_from_project(resource_open)

        with resource_open("Music/songs", "yml") as f:
            self.music_dataset_table.from_yml_file(f)

        with resource_open("Music/program", "bin") as f:
            self.program_chunk = Chunk.create_from_file(f)

        self.read_sequences_from_project(resource_open)
        self.read_instruments_from_project(resource_open)

        with resource_open("Music/always_loaded_songs", "yml") as f:
            always_loaded_bgm_ids = yml_load(f)
        for bgm_id in always_loaded_bgm_ids:
            self.sequences[bgm_id].is_always_loaded = True

        # TODO - Check if any instrument packs used together have conflicting instruments or samples

    def read_sequences_from_project(self, resource_open):
        non_chunk_sequences = set()
        for bgm_id in range(1, len(self.sequences)):
            log.debug("Reading sequence for bgm #{}".format(bgm_id))
            try:
                self.sequences[bgm_id] = ChunkSequence.create_from_project(bgm_id, resource_open)
            except ResourceNotFoundError:
                non_chunk_sequences.add(bgm_id)

        for bgm_id in non_chunk_sequences:
            log.debug("Reading sequence for bgm #{} as subsequence".format(bgm_id))
            try:
                self.sequences[bgm_id] = Subsequence.create_from_project(bgm_id, resource_open)
            except ResourceNotFoundError:
                pass

    def read_instruments_from_project(self, resource_open):
        self.instrument_sets = [None] * 255
        for instrument_id in range(len(self.instrument_sets)):
            log.debug("Reading instrument set #{}".format(instrument_id))
            try:
                self.instrument_sets[instrument_id] = EbInstrumentSet.create_from_project(instrument_id, resource_open)
            except ResourceNotFoundError:
                pass