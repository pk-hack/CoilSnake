from array import array
from coilsnake.util.common.yml import yml_dump
import re
import logging

from typing import Any, Dict, List, Tuple, Union
from coilsnake.model.common.blocks import Block
from coilsnake.util.common.type import enum_class_from_name_list, StringRepresentationMixin, EqualityMixin

from coilsnake.exceptions.common.exceptions import CoilSnakeInternalError, InvalidUserDataError, OutOfBoundsError

from dataclasses import dataclass

from functools import lru_cache

log = logging.getLogger(__name__)

CONFIG_TXT_FILENAME = "config.txt"

YML_INST_PACK_1 = "Instrument pack 1"
YML_INST_PACK_2 = "Instrument pack 2"

INST_OVERWRITE = 0x00
INST_DEFAULT   = 0x1a
SAMPLE_OFFSET_OVERWRITE = 0x7000
SAMPLE_OFFSET_DEFAULT   = 0x95b0

def extract_pack_parts(rom: Block, pack_ptr: int) -> List[Tuple[int,int,Block]]:
    parts = []
    start_bank = pack_ptr & 0xff0000
    while pack_ptr & 0xff0000 == start_bank:
        length = rom.read_multi(pack_ptr, 2)
        if length == 0:
            pack_ptr += 2
            break
        addr = rom.read_multi(pack_ptr + 2, 2)
        pack_ptr += 4
        data = rom[pack_ptr:pack_ptr+length]
        parts.append((addr, length, data))
        pack_ptr += length
    # Ensure the bank of the last byte read doesn't exceed the current bank.
    if (pack_ptr - 1) & 0xff0000 > start_bank:
        raise InvalidUserDataError("Music pack did not end before bank boundary.")
    return parts

@lru_cache(20)
def extract_brr_chunk(brr_start_addr: int, brr_sample_addr: int, brr_block: Block) -> Block:
    start = brr_sample_addr - brr_start_addr
    end = start
    while end < len(brr_block):
        b = brr_block[end]
        end += 9
        if b & 1:
            return brr_block[start:end]
    raise InvalidUserDataError("BRR data at ARAM address ${04X} is missing a terminator".format(brr_sample_addr))

def read_hex_or_default_or_overwrite(s: str, default=None, overwrite=None):
    m = re.match("^.*(default|overwrite).*$", s, flags=re.IGNORECASE)
    if m:
        s2 = m.group(1).lower()
        if s2 == 'default':
            return default
        if s2 == 'overwrite':
            return overwrite
    return int(s.strip(), base=16)

def parse_config_txt(config_txt: str) -> Tuple[int, int, int, List[Tuple]]:
    lines = config_txt.splitlines()
    instrument_keyword_hit = False
    in_instruments = False
    pack_num, base_inst, brr_offset = None
    instruments = []
    line_iter = iter(enumerate(lines, start=1))
    for line_num, line in line_iter:
        # Strip comments out of line
        if ';' in line:
            line = line.split(';')[0]
        # Strip whitespace from line
        line = line.strip()
        if len(line) <= 0:
            continue
        if in_instruments:
            if line == '}':
                # That's it! No more config.txt
                break
            m = re.match(r'^"([^"]*)"(?:\s+\$([0-9a-f]{2})){5}$', line, flags=re.IGNORECASE)
            if m:
                if line_num > 3:
                    raise InvalidUserDataError("Error at line {} in config.txt: pack number directive can only be within first 3 lines".format(line_num))
                pack_num = read_hex_or_default_or_overwrite(m.group(1), default=None, overwrite="ow")
                if pack_num == "ow":
                    raise InvalidUserDataError("Error at line {} in config.txt: pack number cannot be 'override'".format(line_num))
                continue
        else:
            if instrument_keyword_hit:
                if line != '{':
                    raise InvalidUserDataError("Error at line {} in config.txt: expecting '{'".format(line_num))
                in_instruments = True
                continue
            else:
                m = re.match("^.*pack num.*: (\w+)\s*$", line, flags=re.IGNORECASE)
                if m:
                    if line_num > 3:
                        raise InvalidUserDataError("Error at line {} in config.txt: pack number directive can only be within first 3 lines".format(line_num))
                    pack_num = read_hex_or_default_or_overwrite(m.group(1), default=None, overwrite="ow")
                    if pack_num == "ow":
                        raise InvalidUserDataError("Error at line {} in config.txt: pack number cannot be 'override'".format(line_num))
                    continue
                m = re.match("^.*base inst.*: (\w+)\s*$", line, flags=re.IGNORECASE)
                if m:
                    if line_num > 3:
                        raise InvalidUserDataError("Error at line {} in config.txt: base instrument directive can only be within first 3 lines".format(line_num))
                    base_inst = read_hex_or_default_or_overwrite(m.group(1), default=INST_DEFAULT, overwrite=INST_OVERWRITE)
                    continue
                m = re.match("^.*offset.*: (\w+)\s*$", line, flags=re.IGNORECASE)
                if m:
                    if line_num > 3:
                        raise InvalidUserDataError("Error at line {} in config.txt: BRR sample offset directive can only be within first 3 lines".format(line_num))
                    brr_offset = read_hex_or_default_or_overwrite(m.group(1), default=SAMPLE_OFFSET_DEFAULT, overwrite=SAMPLE_OFFSET_OVERWRITE)
                    continue
                m = re.match("^#instruments$", line, flags=re.IGNORECASE)
                if m:
                    instrument_keyword_hit = True
                    continue
                raise InvalidUserDataError("Error at line {} in config.txt: Unexpected text '{}'".format(line_num, line))
                
    return pack_num, base_inst, brr_offset, instruments

class GenericMusicPack:
    def __init__(self, pack_num: int) -> None:
        self.pack_num = pack_num
        self.parts: List[Tuple[int, int, Block]] = []
    def get_aram_byte(self, addr: int) -> Union[int, None]:
        for paddr, plen, pdata in self.parts:
            if paddr <= addr < paddr + plen:
                return pdata[addr - paddr]
        return None
    def set_aram_byte(self, addr: int, value: int) -> bool:
        for paddr, plen, pdata in self.parts:
            if paddr <= addr < paddr + plen:
                pdata[addr - paddr] = value
                return True
        return False
    def get_aram_region(self, addr: int, length: int) -> Block:
        for paddr, plen, pdata in self.parts:
            if paddr <= addr < paddr + plen:
                return pdata[addr - paddr : addr - paddr + length]
        return None
    def set_aram_region(self, addr: int, length: int, value: Any) -> bool:
        for paddr, plen, pdata in self.parts:
            if paddr <= addr < paddr + plen:
                if isinstance(value, int):
                    value = [value for _ in range(length)]
                pdata[addr - paddr : addr - paddr + length] = value
                return True
        return False
    
    def load_from_parts(self, parts: List[Tuple[int, int, Block]]) -> None:
        '''
        Converts data from the pack part form into the internal data structure.

        This function should be overridden for each different pack type.
        '''
        self.parts = parts
    def save_to_parts(self) -> None:
        '''
        Converts data from the internal data structure to pack part form.

        This function should be overridden for each different pack type.
        '''
        pass

    def get_pack_binary_data(self) -> Block:
        # Pack any custom data into the parts
        self.save_to_parts()
        # Size = (4 header bytes + length) for each block + 2 bytes for 00 00 at the end
        total_size = sum((4 + plen for _, plen, _ in self.parts)) + 2
        ret_block = Block(total_size)
        dptr = 0
        for paddr, plen, pdata in self.parts:
            # Write length, addr
            ret_block.write_multi(dptr, plen, 2)
            ret_block.write_multi(dptr + 2, paddr, 2)
            dptr += 4
            # Write data chunk
            ret_block[dptr:dptr+plen] = pdata
            dptr += plen
        # Write length of 0 to mark end
        ret_block.write_multi(dptr, 0, 2)
        dptr += 2
        if total_size != dptr:
            log.error('Check these parts: {}'.format(self.parts))
            raise CoilSnakeInternalError("Coding error: data format miscalculation in musicpack.combine_parts")
        return ret_block
    def convert_to_files(self) -> List[Tuple[str, Union[Block,str]]]:
        '''
        Converts a pack into a set of files to store in a directory.

        This function should be overridden for each different pack type.
        '''
        return [("pack.bin", self.get_pack_binary_data())]
    
    def load_from_files(self, files: Dict[str, Union[Block,str]]):
        if "pack.bin" not in files:
            raise InvalidUserDataError("pack.bin doesn't exist in pack directory")
        self.packs = extract_pack_parts(files["pack.bin"], 0)

class EngineMusicPack(GenericMusicPack):
    def __init__(self, pack_num: int) -> None:
        if pack_num != 1:
            raise InvalidUserDataError('Engine pack must have pack number $01, has pack ${:02X}'.format(pack_num))
        super().__init__(pack_num)

@dataclass
class EBInstrument:
    '''Class that keeps track of all of an instrument's data.'''
    adsr1: int
    adsr2: int
    gain: int
    multiplier: int
    submultiplier: int
    sample: Union[Block, int]
    sample_loop_offset: int

class InstrumentMusicPack(GenericMusicPack):
    def __init__(self, pack_num: int) -> None:
        super().__init__(pack_num)
        self.instruments: List[EBInstrument] = []
        self.base_instrument: int = 0
        self.brr_sample_dump_offset: int = 0
    
    def load_from_parts(self, parts: List[Tuple[int, int, Block]]) -> GenericMusicPack:
        self.parts = parts
        if len(parts) != 3:
            raise InvalidUserDataError("Invalid number of parts for instrument pack, must be 3")
        
        # Check for sample dir. part
        cand_parts = [p for p in parts if 0x6c00 <= p[0] < 0x6e00]
        if len(cand_parts) != 1:
            raise InvalidUserDataError("Invalid number of sample directory parts for instrument pack, must be 1")
        sample_dir_part = cand_parts[0]
        if (sample_dir_part[0] - 0x6c00) % 4 != 0:
            raise InvalidUserDataError("Invalid sample directory part for instrument pack, (address - 0x6c00) must be divisible by 4")
        if sample_dir_part[1] % 4 != 0:
            raise InvalidUserDataError("Invalid sample directory part for instrument pack, length must be divisible by 4")

        # Check for instrument dir. part
        cand_parts = [p for p in parts if 0x6e00 <= p[0] < 0x6f80]
        if len(cand_parts) != 1:
            raise InvalidUserDataError("Invalid number of instrument directory parts for instrument pack, must be 1")
        instrument_dir_part = cand_parts[0]
        if (instrument_dir_part[0] - 0x6e00) % 6 != 0:
            raise InvalidUserDataError("Invalid instrument directory part for instrument pack, (address - 0x6e00) must be divisible by 6")
        if instrument_dir_part[1] % 6 != 0:
            raise InvalidUserDataError("Invalid instrument directory part for instrument pack, length must be divisible by 6")

        # Check for BRR part
        cand_parts = [p for p in parts if 0x7000 <= p[0] <= 0xe800]
        if len(cand_parts) != 1:
            raise InvalidUserDataError("Invalid number of BRR parts for instrument pack, must be 1")
        brr_part = cand_parts[0]

        inst_base = (instrument_dir_part[0] - 0x6e00) // 6
        inst_count = instrument_dir_part[1] // 6

        # Double-check sample directory
        samp_base = (sample_dir_part[0] - 0x6c00) // 4
        samp_count = sample_dir_part[1] // 4
        if inst_base != samp_base:
            raise InvalidUserDataError("Invalid start address of instrument or sample directory part, must start at same instrument number")
        if samp_count < inst_count:
            raise InvalidUserDataError("Invalid number of samples, must be greater than or equal to instrument count, sample count = {}, instrument count = {}".format(samp_count, inst_count))

        # Let's start unpacking the samples!
        self.base_instrument = inst_base
        self.brr_sample_dump_offset = brr_part[0]
        self.instruments = []
        for inst_rel_num in range(inst_count):
            if inst_rel_num + inst_base != instrument_dir_part[2][inst_rel_num*6]:
                raise InvalidUserDataError("Invalid instrument directory, sample number must match instrument number")
            inst_data: Tuple[int,int,int,int,int] = tuple(instrument_dir_part[2][inst_rel_num*6+1 : inst_rel_num*6+6].to_list())
            samp_start, samp_loop = sample_dir_part[2].read_multi(inst_rel_num*4, 2), sample_dir_part[2].read_multi(inst_rel_num*4+2, 2)
            # If the sample start is >= the start of BRR data provided by this instrument pack
            if samp_start >= brr_part[0]:
                # then extract the sample data from the BRR part
                sample = extract_brr_chunk(self.brr_sample_dump_offset, samp_start, brr_part[2])
            else:
                # otherwise, just use the address
                sample = samp_start
            inst = EBInstrument(*inst_data, sample, samp_loop - samp_start)
            self.instruments.append(inst)
        # We've constructed the full list of instruments. We're done! B)
    
    def save_to_parts(self) -> None:
        # Determine the set of BRRs used
        brr_set = {inst.sample for inst in self.instruments if isinstance(inst.sample, Block)}
        # Determine the addresses of the BRRs
        brr_ptr = self.brr_sample_dump_offset
        brr_addrs: Dict[Block, int] = {}
        for brr in brr_set:
            brr_addrs[brr] = brr_ptr
            brr_ptr += len(brr)
        brr_part_size = brr_ptr - self.brr_sample_dump_offset
        # Create the BRR part
        brr_part = (self.brr_sample_dump_offset, brr_part_size, Block(brr_part_size))
        for brr in brr_set:
            brr_ptr = brr_addrs[brr]
            brr_part[2][brr_ptr:brr_ptr + len(brr)] = brr
        
        # Create the sample and inst. directory parts
        inst_count = len(self.instruments)
        inst_base = self.base_instrument
        sample_dir_part = (0x6c00 + 4 * inst_base, inst_count * 4, Block(inst_count * 4))
        inst_dir_part =   (0x6e00 + 6 * inst_base, inst_count * 6, Block(inst_count * 6))
        # Populate sample and inst. directories
        for inst_rel_num, inst in enumerate(self.instruments):
            # Populate sample directory
            if isinstance(inst.sample, Block):
                sample_addr = brr_addrs[inst.sample]
            else:
                sample_addr = inst.sample
            sample_loop = sample_addr + inst.sample_loop_offset
            sample_dir_part[2].write_multi(inst_rel_num * 4 + 0, sample_addr, 2)
            sample_dir_part[2].write_multi(inst_rel_num * 4 + 2, sample_loop, 2)
            # Populate instrument directory
            inst_dir_part[2][inst_rel_num * 6 + 0] = inst_base + inst_rel_num
            inst_dir_part[2][inst_rel_num * 6 + 1] = inst.adsr1
            inst_dir_part[2][inst_rel_num * 6 + 2] = inst.adsr2
            inst_dir_part[2][inst_rel_num * 6 + 3] = inst.gain
            inst_dir_part[2][inst_rel_num * 6 + 4] = inst.multiplier
            inst_dir_part[2][inst_rel_num * 6 + 5] = inst.submultiplier
        
        # Set our parts
        self.parts = [sample_dir_part, inst_dir_part, brr_part]

    # For writing to project
    def convert_to_files(self) -> List[Tuple[str, Union[Block,str]]]:
        files_to_output: List[Tuple[str, Union[Block,str]]] = []
        # Build BRR use list
        brr_use_list: Dict[Block, List[int]] = {}
        brr_loop_addr: Dict[Block, int] = {}
        brr_filenames: Dict[Block, str] = {}
        for inst_num, inst in enumerate(self.instruments, self.base_instrument):
            if not isinstance(inst.sample, Block):
                continue
            if inst.sample not in brr_use_list:
                brr_use_list[inst.sample] = []
                brr_loop_addr[inst.sample] = inst.sample_loop_offset
            elif brr_loop_addr[inst.sample] != inst.sample_loop_offset:
                raise InvalidUserDataError("Sample is shared but with different loop points, cannot save to file.")
            brr_use_list[inst.sample].append(inst_num)
        # Add BRR files to output list
        for brr, use_list in brr_use_list.items():
            # Prepend loop address to BRR
            brr_with_loop = Block(len(brr)+2)
            brr_with_loop.write_multi(0, brr_loop_addr[brr], 2)
            brr_with_loop.from_block(brr, 2)
            # Generate file name
            brr_file_name = "sample-{}.brr".format("-".join(("{:02X}".format(x) for x in use_list)))
            brr_filenames[brr] = brr_file_name
            # Add to output files
            files_to_output.append((brr_file_name, brr_with_loop))
        
        # Create "config.txt"
        config_lines: List[str] = []
        config_lines.append("Pack number: {:02X}".format(self.pack_num))
        base_instrument_str = "default" if self.base_instrument == 0x1A else "{:02X}".format(self.base_instrument)
        config_lines.append("Base instrument: " + base_instrument_str)
        brr_sample_dump_offset_str = "default" if self.brr_sample_dump_offset == 0x95B0 else "{:04X}".format(self.brr_sample_dump_offset)
        config_lines.append("BRR sample dump offset: " + brr_sample_dump_offset_str)
        config_lines.append("")
        config_lines.append("#instruments")
        config_lines.append("{")
        for inst in self.instruments:
            if isinstance(inst.sample, Block):
                inst_sample = brr_filenames[inst.sample]
            else:
                inst_sample = '0x{:04X} 0x{:04X}'.format(inst.sample, inst.sample + inst.sample_loop_offset)
            line_parts: List[str] = []
            line_parts.append('  "{}"'.format(inst_sample))
            line_parts.append(''.ljust(31-len(line_parts[0])))
            line_parts.append(' ${:02X}'.format(inst.adsr1))
            line_parts.append(' ${:02X}'.format(inst.adsr2))
            line_parts.append(' ${:02X}'.format(inst.gain))
            line_parts.append(' ${:02X}'.format(inst.multiplier))
            line_parts.append(' ${:02X}'.format(inst.submultiplier))
            config_lines.append(''.join(line_parts))
        config_lines.append("}\n")
        config_txt = "\n".join(config_lines)
        files_to_output.append((CONFIG_TXT_FILENAME, config_txt))
        return files_to_output
    
    def load_from_files(self, files: Dict[str, Union[Block,str]]):
        if CONFIG_TXT_FILENAME not in files:
            raise InvalidUserDataError("config doesn't exist in instrument pack directory")
        pack_num, base_instrument, brr_sample_dump_offset, instrument_defs = parse_config_txt(files[CONFIG_TXT_FILENAME])

        self.packs = extract_pack_parts(files["pack.bin"], 0)

def relocate_song_data(src: int, dst: int, data: Block) -> Block:
    # Deep copy so we won't be modifying the original data
    out = Block()
    out.from_block(data)
    # Let's parse a song :)
    try:
        # Helper functions
        data_ptr = 0
        relocation_count = 0
        def consume_byte() -> int:
            nonlocal data_ptr
            val = out.read_multi(data_ptr, 1)
            data_ptr += 1
            return val
        def consume_word() -> int:
            nonlocal data_ptr
            val = out.read_multi(data_ptr, 2)
            data_ptr += 2
            return val
        def change_last_word(val=None):
            nonlocal relocation_count
            relocation_count += 1
            if val is None:
                val = out.read_multi(data_ptr - 2, 2) + dst - src
            out.write_multi(data_ptr - 2, val, 2)
        def check_rel_ptr_in_bounds(rel_ptr: int, description: str):
            if not 0 <= rel_ptr < len(data):
                raise OutOfBoundsError("{} out of bounds (address={}), corrupted song".format(description, rel_ptr))
        
        # Parse all phrases / "block list"
        pattern_list = []
        while True:
            pattern_ptr = consume_word()
            if pattern_ptr & 0xff00 == 0:
                # Special meaning - not a phrase address
                if pattern_ptr == 0:
                    # End of phrases
                    # - Stop processing
                    break
                elif pattern_ptr == 0x80:
                    # Debug: Fast forward on
                    # - Skip this, it's not a phrase address
                    continue
                elif pattern_ptr == 0x81:
                    # Debug: Fast forward off
                    # - Skip this, it's not a phrase address
                    pass
                else:
                    # Loop (0x01-0x7f) / Jump (0x82-0xff)
                    # - Relocate jump address
                    # Consume, then change, jump address
                    rel_jump_ptr = consume_word() - src
                    check_rel_ptr_in_bounds(rel_jump_ptr, "Phrase loop address")
                    change_last_word()
            else:
                # Actually a phrase pointer - add to list and change
                rel_pattern_ptr = pattern_ptr - src
                check_rel_ptr_in_bounds(rel_pattern_ptr, "Pattern address")
                pattern_list.append(rel_pattern_ptr)
                change_last_word()
        
        # Parse all patterns
        track_list = []
        for pattern_table_addr in pattern_list:
            for pattern_idx in range(8):
                data_ptr = pattern_table_addr + pattern_idx * 2
                track_ptr = consume_word()
                if track_ptr == 0:
                    continue
                rel_track_ptr = track_ptr - src
                check_rel_ptr_in_bounds(rel_track_ptr, "Track address")
                if rel_track_ptr not in track_list:
                    track_list.append(rel_track_ptr)
                change_last_word()

        # Parse all tracks
        for track_ptr in track_list:
            data_ptr = track_ptr
            while True:
                cmd = consume_byte()
                if cmd == 0:
                    break
                elif cmd < 0xe0:
                    # 1-byte note duration / parameter / note command
                    continue
                elif cmd == 0xef:
                    # VCMD $EF: subroutine
                    # EF aa aa nn
                    #   a = address of subroutine
                    #   n = number of times to repeat
                    # Deal with subroutine address
                    rel_sub_ptr = consume_word() - src
                    check_rel_ptr_in_bounds(rel_sub_ptr, "Subroutine address")
                    if rel_sub_ptr not in track_list:
                        track_list.append(rel_sub_ptr)
                    change_last_word()
                    # Deal with repeat count
                    consume_byte() # We don't care what it is, we just skip it
                else:
                    # Other VCMD
                    # Skip the correct number of bytes
                    additional_byte_counts = [
                    	1, 1, 2, 3, 0, 1, 2, 1, 2, 1, 1, 3, 0, 1, 2, 3,
	                    1, 3, 3, 0, 1, 3, 0, 3, 3, 3, 1, 2, 0, 0, 0, 0
                    ]
                    for _ in range(additional_byte_counts[cmd-0xe0]):
                        consume_byte()
        
        # We should be done! :)
        log.debug("Moved {}-byte song from {:04X} to {:04X}, {} relocations".format(len(data), src, dst, relocation_count))
        # Return the adjusted song
        return out
    except OutOfBoundsError as e:
        raise InvalidUserDataError("OutOfBoundsError encountered while parsing song: {}".format(e))

class Song:
    def get_song_packs(self) -> Tuple[int,int,int]:
        raise NotImplementedError('Please use a subclass of Song')
    def get_song_aram_address(self) -> int:
        raise NotImplementedError('Please use a subclass of Song')

@dataclass
class SongWithData(Song):
    song_number: int
    instrument_pack_1: int
    instrument_pack_2: int
    
    pack_number: int
    data_address: int
    data: Block

    def get_song_packs(self) -> Tuple[int, int, int]:
        return (self.instrument_pack_1, self.instrument_pack_2, self.pack_number)
    def get_song_aram_address(self) -> int:
        return self.data_address

@dataclass
class SongOffsettedFromAnother(Song):
    song: Song
    offset: int

class SongMusicPack(GenericMusicPack):
    def __init__(self, pack_num: int) -> None:
        super().__init__(pack_num)
        self.songs: List[Song] = []
    
    def load_from_parts(self, parts: List[Tuple[int, int, Block]]) -> None:
        self.parts = parts
        self.songs = []
        for part_addr, part_len, part_data in parts:
            song = SongWithData(None, None, None, self.pack_num, part_addr, part_data)
            self.songs.append(song)

    # For writing to project
    def convert_to_files(self) -> List[Tuple[str, Union[Block,str]]]:
        files_to_output: List[Tuple[str, Union[Block,str]]] = []

        for song_idx, song in enumerate(self.songs, 1):
            if song.song_number is None:
                log.error("Issue with song pack ${:02X} at address ${:04X}".format(self.pack_num, song.get_song_aram_address()))
                raise CoilSnakeInternalError("Metadata is not set when converting songs to files")
            song_name = "song-{:02X}".format(song.song_number)

            ### Write out EBM file
            ebm_data = Block(len(song.data) + 4)
            # Write length, addr
            ebm_data.write_multi(0, len(song.data), 2)
            ebm_data.write_multi(2, song.data_address, 2)
            # Write data chunk
            ebm_data[4:len(ebm_data)] = song.data
            # Add to file list
            files_to_output.append((song_name + '.ebm',ebm_data))

            ### Write out EBM.yml file
            yml_data = {}
            yml_data[YML_INST_PACK_1] = song.instrument_pack_1
            yml_data[YML_INST_PACK_2] = song.instrument_pack_2
            yml_str = str(yml_dump(yml_data))
            files_to_output.append((song_name + '.ebm.yml',yml_str))

        return files_to_output


def find_containing_song(song_pack: SongMusicPack, song_addr: int) -> Union[None,Tuple[Song,int]]:
    for song in song_pack.songs:

        if song.data_address <= song_addr < song.data_address + len(song.data):
            return (song, song_addr - song.data_address)
    return None

def create_pack_object_from_parts(pack_num: int, parts: List[Tuple[int, int, Block]]) -> GenericMusicPack:
    formats = [
        ("instrument", InstrumentMusicPack),
        ("engine",     EngineMusicPack),
        ("song",       SongMusicPack),
    ]
    fmt_fail_msg = {}
    for fmt_name, fmt_cls in formats:
        try:
            pack = fmt_cls(pack_num)
            pack.load_from_parts(parts)
        except InvalidUserDataError as e:
            fmt_fail_msg[fmt_name] = e.message
        else:
            return pack
    fmt_list = ", ".join((fmt[0] for fmt in formats))
    for fmt_name, msg in fmt_fail_msg.items():
        log.debug("Unable to process pack {:02X} as {} pack, encountered error: \"{}\"".format(pack_num, fmt_name, msg))
    raise InvalidUserDataError("Invalid pack format, must be one of the following: {}".format(fmt_list))
