from coilsnake.model.common.table import LittleEndianHexIntegerTableEntry, Table
from coilsnake.model.common.blocks import Block
import logging
from typing import Dict, List, Set

from coilsnake.exceptions.common.exceptions import CoilSnakeInternalError, InvalidUserDataError
import coilsnake.model.eb.musicpack as mp
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import convert_values_to_hex_repr, yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address

from collections import OrderedDict

log = logging.getLogger(__name__)

class MusicModule(EbModule):
    NAME = "Music"
    FREE_RANGES = [ # Every single vanilla pack location
        (0x0BE02A,0x0BFFFF),
        (0x0CF617,0x0CFFFF),
        (0x0EF8C6,0x0EFFFF),
        (0x0FF2B5,0x0FFFFF),
        (0x10DFB4,0x10FFFF),
        (0x18F6B7,0x18FFFF),
        (0x19FC18,0x19FFFF),
        (0x1AFB07,0x1AFFFF),
        (0x1BF2EB,0x1BFFFF),
        (0x1CE037,0x1CFFFF),
        (0x1DFECE,0x1DFFFF),
        (0x1EFCDD,0x1EFFFF),
        (0x1FEC46,0x1FFFFF),
        (0x20ED03,0x20FFFF),
        (0x21F581,0x21FFFF),
        (0x220000,0x22FFFF),
        (0x230000,0x23FFFF),
        (0x240000,0x24FFFF),
        (0x250000,0x25FFFF),
        (0x260000,0x26FFFF),
        (0x270000,0x27FFFF),
        (0x280000,0x28FFFF),
        (0x290000,0x29FFFF),
        (0x2A0000,0x2AFFFF),
        (0x2B0000,0x2BFFFF),
        (0x2C0000,0x2CFFFF),
        (0x2D0000,0x2DFFFF),
    ]
    SONG_PACK_TABLE_ROM_ADDR = 0xC4F70A
    PACK_POINTER_TABLE_ROM_ADDR = 0xC4F947
    SONG_ADDRESS_TABLE_ENGINE_ARAM_ADDR = 0x2E4A

    SONG_ADDRESS_TABLE_SCHEMA = LittleEndianHexIntegerTableEntry.create("Song Address", 2)

    MUSIC_PACK_PATH_FORMAT_STRING = 'Music/Packs/{:02X}/'

    def __init__(self):
        super(EbModule, self).__init__()
        self.song_pack_table = eb_table_from_offset(MusicModule.SONG_PACK_TABLE_ROM_ADDR)
        self.pack_pointer_table = eb_table_from_offset(MusicModule.PACK_POINTER_TABLE_ROM_ADDR)
        self.song_address_table = Table(MusicModule.SONG_ADDRESS_TABLE_SCHEMA, name="Song Address Table", num_rows=self.song_pack_table.num_rows)
        self.packs: List[mp.GenericMusicPack] = []
        self.songs: Dict[int, mp.Song] = {}

    def read_single_pack(self, rom: Block, pack_num: int) -> mp.GenericMusicPack:
        pack_ptr = from_snes_address(self.pack_pointer_table[pack_num][0])
        pack_parts = mp.extract_pack_parts(rom, pack_ptr)
        pack = mp.create_pack_object_from_parts(pack_num, pack_parts)
        return pack

    def read_from_rom(self, rom):
        self.song_pack_table.from_block(rom, from_snes_address(MusicModule.SONG_PACK_TABLE_ROM_ADDR))
        self.pack_pointer_table.from_block(rom, from_snes_address(MusicModule.PACK_POINTER_TABLE_ROM_ADDR))
        # Read out all packs
        self.packs = []
        for pack_num in range(self.pack_pointer_table.num_rows):
            pack = self.read_single_pack(rom, pack_num)
            self.packs.append(pack)
        # Read song address table from engine
        if not isinstance(self.packs[1], mp.EngineMusicPack):
            raise InvalidUserDataError("Expected pack 1 to be the music engine pack, instead it is of type {}".format(
                type(self.packs[1]).__name__))
        song_address_table_data = self.packs[1].get_aram_region(
            MusicModule.SONG_ADDRESS_TABLE_ENGINE_ARAM_ADDR,
            self.song_address_table.size)
        self.song_address_table.from_block(song_address_table_data, 0)
        # Update song metadata
        self.in_engine_songs = []
        for song_table_ind in range(self.song_pack_table.num_rows):
            song_num = song_table_ind + 1
            inst_pack_1, inst_pack_2, song_pack_num = tuple(self.song_pack_table[song_table_ind])
            song_addr = self.song_address_table[song_table_ind]
            if song_pack_num == 0xff or song_pack_num == 0x01:
                song_obj = mp.InEngineSong(song_num, inst_pack_1, inst_pack_2, song_pack_num, song_addr)
            else:
                # Song is not stored in the engine pack - determine which Song object it is
                pack_obj_of_song = self.packs[song_pack_num]
                if not isinstance(pack_obj_of_song, mp.SongMusicPack):
                    raise InvalidUserDataError("Invalid type {} of song pack ${:02X} when processing song ${:02X}, expected SongMusicPack".format(type(pack_obj_of_song).__name__, song_pack_num, song_num))
                matching_songs_in_pack = [x for x in pack_obj_of_song.songs if x.data_address == song_addr]
                if len(matching_songs_in_pack) < 1:
                    log.debug('Unable to find pack part with address ${:04X}'.format(song_addr))
                    log.debug('Song addresses in pack: ' + ', '.join('${:04X}'.format(song.data_address) for song in pack_obj_of_song.songs))
                    song_obj = mp.check_if_song_is_part_of_another(song_num, pack_obj_of_song, song_addr)
                    if song_obj is None:
                        raise InvalidUserDataError("Song pack ${:02X} missing song at address ${:04X} when processing song ${:02X}".format(song_pack_num, song_addr, song_num))
                else:
                    if len(matching_songs_in_pack) > 1:
                        raise InvalidUserDataError("Song pack ${:02X} has multiple songs at address ${:04X} when processing song ${:02X}".format(song_pack_num, song_addr, song_num))
                    # We've found the song part in the pack. Use that
                    song_obj = matching_songs_in_pack[0]
                    # Update data in song object
                    song_obj.song_number = song_num
                    song_obj.instrument_pack_1 = inst_pack_1
                    song_obj.instrument_pack_2 = inst_pack_2
            self.songs[song_num] = song_obj
        # Perform sanity checks on extracted songs
        for song_table_ind in range(self.song_pack_table.num_rows):
            song_num = song_table_ind + 1
            song_packs = tuple(self.song_pack_table[song_table_ind])
            if song_num not in self.songs:
                continue
            song_obj = self.songs[song_num]
            if isinstance(song_obj, mp.SongThatIsPartOfAnother):
                parent_packs = song_obj.get_song_packs()
                if song_packs != parent_packs:
                    raise InvalidUserDataError("Song number {} (packs: {}) is a subset of song {} (packs: {}) - packs do not match!".format(
                        song_num, song_packs, song_obj.parent_song.song_number, parent_packs
                    ))

    def write_to_project(self, resourceOpener):
        # Write out each pack to its folder.
        for pack in self.packs:
            # Each pack knows how to turn itself into files.
            # Write those files into the pack folder.
            pack_base_fname = self.MUSIC_PACK_PATH_FORMAT_STRING.format(pack.pack_num)
            for fname, data in pack.convert_to_files():
                fname_spl = fname.split('.')
                assert len(fname_spl) > 1, "Internal error in music module, can't write file '{}'".format(fname)
                fname_no_ext = '.'.join(fname_spl[:-1])
                is_text = isinstance(data,str)
                with resourceOpener(pack_base_fname+fname_no_ext,fname_spl[-1],is_text) as f:
                    if is_text:
                        f.write(data)
                    else:
                        f.write(data.data)
        # Create and write songs.yml
        yml_song_lines = []
        for song_num in sorted(self.songs.keys()):
            yml_song_lines.append("0x{:02X}:\n".format(song_num))
            yml_song_lines += ('  {}\n'.format(line) for line in self.songs[song_num].to_yml_lines())
        with resourceOpener('Music/songs','yml',True) as f:
            f.writelines(yml_song_lines)

    def read_from_project(self, resourceOpener):
        self.packs = []
        self.songs = {}
        # Read songs.yml
        songs_yml_data = yml_load(resourceOpener('Music/songs','yml',True))
        # Look up with song pack, then song number. Result is data from YAML.
        pack_song_metadata: Dict[int, Dict[int, Dict]] = {}
        for song_num, song_yml in songs_yml_data.items():
            if mp.YML_SONG_PACK in song_yml:
                pack = song_yml[mp.YML_SONG_PACK]
            else:
                # This must be a dependent song
                parent_song = song_yml[mp.YML_SONG_TO_REFERENCE]
                pack = songs_yml_data[parent_song][mp.YML_SONG_PACK]
            # Do an extra check to make in-engine songs work
            if pack == 0xff:
                # Make sure that the songs that are in song pack 0xff get put into the engine pack object.
                pack = 0x01
            d = pack_song_metadata.get(pack, dict())
            d[song_num] = song_yml
            pack_song_metadata[pack] = d
        # For each pack:
        for pack_num in range(self.pack_pointer_table.num_rows):
            pack_base_path = self.MUSIC_PACK_PATH_FORMAT_STRING.format(pack_num)
            def file_loader(fname, astext=False):
                fname_spl = fname.split('.')
                assert len(fname_spl) > 1, "Internal error in music module, can't read file '{}'".format(fname)
                fname_no_ext = '.'.join(fname_spl[:-1])
                return resourceOpener(pack_base_path + '/' + fname_no_ext, fname_spl[-1], astext=astext)
            eligible_types = []
            # Check for engine.bin
            try:
                with file_loader('engine.bin'):
                    eligible_types.append(mp.EngineMusicPack)
            except FileNotFoundError:
                pass
            # Check for config.txt
            try:
                with file_loader('config.txt'):
                    eligible_types.append(mp.InstrumentMusicPack)
            except FileNotFoundError:
                pass
            # Check if there are songs in this pack
            if pack_num in pack_song_metadata:
                eligible_types.append(mp.SongMusicPack)
            # Ensure we don't have incompatible pack types
            if mp.InstrumentMusicPack in eligible_types and len(eligible_types) > 1:
                explanation = None
                if mp.SongMusicPack in eligible_types:
                    explanation = "references in 'songs.yml'"
                elif mp.EngineMusicPack in eligible_types:
                    explanation = "engine.bin"
                assert explanation
                raise InvalidUserDataError("pack {:02X} has both config.txt and {} - please remove one of these".format(
                    pack_num, explanation))
            # Try out the pack type
            if eligible_types:
                pack_type = eligible_types[0]
                try:
                    pack_obj = pack_type(pack_num)
                    if isinstance(pack_obj, mp.SongMusicPack):
                        pack_obj.set_data_from_yaml(pack_song_metadata[pack_num])
                    pack_obj.load_from_files(file_loader)
                    if isinstance(pack_obj, mp.SongMusicPack):
                        for song in pack_obj.songs:
                            self.songs[song.song_number] = song
                    elif isinstance(pack_obj, mp.EngineMusicPack):
                        for song_num, song_md in pack_song_metadata[pack_num].items():
                            song_obj = mp.song_obj_from_yml(song_num, song_md)
                            self.songs[song_num] = song_obj
                except InvalidUserDataError as e:
                    raise InvalidUserDataError("Unable to interpret pack {:02X} as type {}: {}".format(pack_num, pack_type, e.message))
            else:
                # TODO: Remove this. This is just a workaround since we aren't reading songs.yml yet.
                pack_obj = mp.EmptyPack(pack_num)
            self.packs.append(pack_obj)
        return

    def write_to_rom(self, rom):
        # Prepare packs for writing out by converting them to parts
        for pack in self.packs:
            pack.save_to_parts()
        # Build song address table and song pack table
        for song_num, song in self.songs.items():
            song_ind = song_num - 1
            self.song_address_table[song_ind] = song.get_song_aram_address()
            self.song_pack_table[song_ind] = song.get_song_packs()
        # Write song address table into engine pack
        song_address_table_data = Block(self.song_address_table.size)
        self.song_address_table.to_block(song_address_table_data, 0)
        self.packs[0x01].set_aram_region(self.SONG_ADDRESS_TABLE_ENGINE_ARAM_ADDR,
                                         len(song_address_table_data),
                                         song_address_table_data)
        # Write out packs
        for i, pack in enumerate(self.packs):
            data = pack.get_pack_binary_data()
            pack_offset = rom.allocate(data=data)
            self.pack_pointer_table[i] = [to_snes_address(pack_offset)]
        # Write out pack pointer table
        self.pack_pointer_table.to_block(block=rom, offset=from_snes_address(self.PACK_POINTER_TABLE_ROM_ADDR))
        # Build song pack table
        self.song_pack_table.to_block(block=rom, offset=from_snes_address(self.SONG_PACK_TABLE_ROM_ADDR))
        return
