import logging
from typing import Dict, List

from coilsnake.exceptions.common.exceptions import InvalidUserDataError
from coilsnake.model.common.ips import IpsPatch
from coilsnake.model.common.table import LittleEndianHexIntegerTableEntry, Table
from coilsnake.model.common.blocks import Block
import coilsnake.model.eb.musicpack as mp
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.common.PatchModule import get_ips_filename
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import yml_load
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address

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
        song_address_table_data = self.packs[1].get_song_address_table_data(self.song_address_table.size)
        self.song_address_table.from_block(song_address_table_data, 0)
        # Update song metadata
        for song_table_ind in range(self.song_pack_table.num_rows):
            song_num = song_table_ind + 1
            inst_pack_1, inst_pack_2, song_pack_num = tuple(self.song_pack_table[song_table_ind])
            song_addr = self.song_address_table[song_table_ind]
            storage_song_pack_num = 0x01 if song_pack_num == 0xFF else song_pack_num
            pack_obj_of_song = self.packs[storage_song_pack_num]
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
                # We've found the song part in the pack. Use that.
                song_obj = matching_songs_in_pack[0]
                # Handle multiple songs pointing to the same data
                if song_obj.song_number:
                    log.debug("Song pack ${:02X} has multiple references in the song table to address ${:04X} - references include songs ${:02X}, ${:02X}".format(song_pack_num, song_addr, song_obj.song_number, song_num))
                    song_obj = mp.SongThatIsPartOfAnother(song_num, song_obj, 0)
                else:
                    # Update data in song object
                    song_obj.song_number = song_num
            # Set the song object's packs now - for SongThatIsPartOfAnother, we will clear it to None later if it's redundant
            song_obj.instrument_pack_1 = inst_pack_1
            song_obj.instrument_pack_2 = inst_pack_2
            # Store song object into our lookup table
            self.songs[song_num] = song_obj
        # Swap any referenced songs if applicable (so the .ebm.yml has the most complete instrument list)
        for song_num, song_obj in self.songs.items():
            # Only swap songs that use the exact same song data
            if not (isinstance(song_obj, mp.SongThatIsPartOfAnother) and song_obj.offset == 0):
                continue
            # Get parent info and song number
            parent_obj = song_obj.parent_song
            assert isinstance(parent_obj, mp.SongWithData), "Internal coding error in music module"
            parent_num = parent_obj.song_number
            # Get song packs
            song_packs = song_obj.get_song_packs()
            parent_packs = song_obj.parent_song.get_song_packs()
            # Check if there are unspecified packs on the parent and not on the current song
            should_swap = any(p == 0xFF for p in parent_packs[:2]) and all(p != 0xFF for p in song_packs[:2])
            # If so, then we should swap the two songs
            if not should_swap:
                continue
            # We are going to keep the same two objects, but swap the song number and packs inside (and also in self.songs)
            log.debug('Swapping song $%02X to be the dependent of $%02X', parent_num, song_num)
            # Swap song numbers and packs using getattr/setattr trickery
            for attr in ('song_number', 'instrument_pack_1', 'instrument_pack_2'):
                sa, pa = getattr(song_obj, attr), getattr(parent_obj, attr)
                setattr(song_obj, attr, pa)
                setattr(parent_obj, attr, sa)
            # Update references to song objects in self.songs
            self.songs[song_num], self.songs[parent_num] = parent_obj, song_obj
        # For all referenced songs, clear the instrument pack if it's redundant.
        for song_obj in (obj for obj in self.songs.values() if isinstance(obj, mp.SongThatIsPartOfAnother)):
            song_packs = song_obj.get_song_packs()
            parent_packs = song_obj.parent_song.get_song_packs()
            if song_packs[0] == parent_packs[0]:
                song_obj.instrument_pack_1 = None
            if song_packs[1] == parent_packs[1]:
                song_obj.instrument_pack_2 = None

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
                if pack == mp.YML_SONG_PACK_BUILTIN:
                    pack = 0xFF
            else:
                # This must be a dependent song
                parent_song = song_yml[mp.YML_SONG_TO_REFERENCE]
                pack = songs_yml_data[parent_song][mp.YML_SONG_PACK]
            # Do an extra check to make in-engine songs work
            storage_song_pack_num = 0x01 if pack == 0xFF else pack
            d = pack_song_metadata.get(storage_song_pack_num, dict())
            d[song_num] = song_yml
            pack_song_metadata[storage_song_pack_num] = d
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
            # Try out the pack type - this will be in the order that we check them above.
            # We will try Engine, then Instrument, then Song pack type in that order.
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
                except InvalidUserDataError as e:
                    raise InvalidUserDataError("Error reading pack ${:02X} as {}: {}".format(pack_num, pack_type.__name__, e.message))
            else:
                log.warn("Music pack ${:02X} contains no data.".format(pack_num))
                pack_obj = mp.EmptyPack(pack_num)
            self.packs.append(pack_obj)
        return

    def write_to_rom(self, rom):
        # Apply Gas Station instrument pack patch
        # In the vanilla game, there is a bug in the INITIALIZE_SPC700 function where it loads the
        # engine pack by looking at the sequence pack of song 00, but then stores the loaded pack
        # value into the secondary instrument pack variable. This means when we play the
        # Gas Station song, it will load the whole engine again, which includes some instrument
        # data. This instrument data will be loaded after the instrument packs, so this can result
        # in some corrupted instruments when changing the instrument packs used by Gas Station.
        self.get_patch(rom).apply(rom)
        # Prepare packs for writing out by converting them to parts
        for pack in self.packs:
            pack.save_to_parts()
        # Build song address table and song pack table
        for song_num, song in self.songs.items():
            song_ind = song_num - 1
            self.song_address_table[song_ind] = song.get_song_aram_address()
            self.song_pack_table[song_ind] = song.get_song_packs()
        # Write song address table into engine pack
        if not isinstance(self.packs[1], mp.EngineMusicPack):
            raise InvalidUserDataError("Expected pack 1 to be the music engine pack, instead it is of type {}".format(
                type(self.packs[1]).__name__))
        song_address_table_data = Block(self.song_address_table.size)
        self.song_address_table.to_block(song_address_table_data, 0)
        self.packs[0x01].set_song_address_table_data(song_address_table_data)
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

    def get_patch(self, rom):
        ips = IpsPatch()
        ips.load(get_ips_filename(rom.type, 'gas_station_pack_fix'), 0)
        return ips

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        if old_version == 11:
            # Upgrade 11 to 12
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
        self.upgrade_project(
            11 if old_version < 11 else old_version + 1,
            new_version,
            rom,
            resource_open_r,
            resource_open_w,
            resource_delete)
