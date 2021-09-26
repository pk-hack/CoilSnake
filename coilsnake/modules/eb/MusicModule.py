from coilsnake.model.common.table import LittleEndianHexIntegerTableEntry, Table
from coilsnake.model.common.blocks import Block
import logging
from typing import List

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

    def __init__(self):
        super(EbModule, self).__init__()
        self.song_pack_table = eb_table_from_offset(MusicModule.SONG_PACK_TABLE_ROM_ADDR)
        self.pack_pointer_table = eb_table_from_offset(MusicModule.PACK_POINTER_TABLE_ROM_ADDR)
        self.song_address_table = Table(MusicModule.SONG_ADDRESS_TABLE_SCHEMA, name="Song Address Table", num_rows=self.song_pack_table.num_rows)
        self.packs: List[mp.GenericMusicPack] = []
        self.in_engine_songs: List[int] = []

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
        song_address_table_data = self.packs[1].get_aram_region(
            MusicModule.SONG_ADDRESS_TABLE_ENGINE_ARAM_ADDR,
            self.song_address_table.size)
        self.song_address_table.from_block(song_address_table_data, 0)
        # Update song metadata
        self.in_engine_songs = []
        for song_table_ind in range(self.song_pack_table.num_rows):
            song_num = song_table_ind + 1
            inst_pack_1, inst_pack_2, song_pack_num = tuple(self.song_pack_table[song_table_ind])
            log.debug(f'Song num = {song_num:02X}, packs = {self.song_pack_table[song_table_ind]}')
            if song_pack_num == 0xff or song_pack_num == 0x01:
                self.in_engine_songs.append(song_num)
                continue
            song_addr = self.song_address_table[song_table_ind]
            pack_obj_of_song = self.packs[song_pack_num]
            if not isinstance(pack_obj_of_song, mp.SongMusicPack):
                raise InvalidUserDataError("Invalid type {} of song pack ${:02X} when processing song ${:02X}, expected SongMusicPack".format(type(pack_obj_of_song).__name__, song_pack_num, song_num))
            matching_songs_in_pack = [x for x in pack_obj_of_song.songs if x.data_address == song_addr]
            if len(matching_songs_in_pack) < 1:
                log.debug('Unable to find pack part with address ${:04X}'.format(song_addr))
                log.debug('Song addresses in pack: ' + ', '.join('${:04X}'.format(song.data_address) for song in pack_obj_of_song.songs))
                containing_song_info = mp.find_containing_song(pack_obj_of_song, song_addr)
                if containing_song_info is None:
                    raise InvalidUserDataError("Song pack ${:02X} missing song at address ${:04X} when processing song ${:02X}".format(song_pack_num, song_addr, song_num))
                # TODO: make new song object that refers to other song
                continue
            else:
                if len(matching_songs_in_pack) > 1:
                    raise InvalidUserDataError("Song pack ${:02X} has multiple songs at address ${:04X} when processing song ${:02X}".format(song_pack_num, song_addr, song_num))
                # We've found the song part in the pack. Use that
                song_obj = matching_songs_in_pack[0]
                # Update data in song object
                song_obj.song_number = song_num
                song_obj.instrument_pack_1 = inst_pack_1
                song_obj.instrument_pack_2 = inst_pack_2



    def write_to_project(self, resourceOpener):
        for pack in self.packs:
            # Each pack knows how to turn itself into files.
            # Write those files into the pack folder.
            pack_base_fname = 'MusicPacks/{:02X}/'.format(pack.pack_num)
            for fname, data in pack.convert_to_files():
                fname_spl = fname.split('.')
                is_text = isinstance(data,str)
                with resourceOpener(pack_base_fname+fname_spl[0],fname_spl[1],is_text) as f:
                    if is_text:
                        f.write(data)
                    else:
                        f.write(data.data)

    def read_from_project(self, resourceOpener):
        # TODO
        return

    def write_to_rom(self, rom):
        # TODO
        return
