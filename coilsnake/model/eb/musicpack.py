from array import array
from coilsnake.util.common.yml import yml_dump, yml_load
import re
import logging

from typing import Any, Dict, Generic, List, TextIO, Tuple, Union
from coilsnake.model.common.blocks import Block
from coilsnake.util.common.type import enum_class_from_name_list, StringRepresentationMixin, EqualityMixin

from coilsnake.exceptions.common.exceptions import CoilSnakeInternalError, InvalidUserDataError, OutOfBoundsError

from dataclasses import dataclass

from functools import lru_cache

log = logging.getLogger(__name__)

CONFIG_TXT_FILENAME = "config.txt"

YML_INST_PACK_1 = "Instrument Pack 1"
YML_INST_PACK_2 = "Instrument Pack 2"

YML_SONG_PACK         = "Song Pack"
YML_SONG_FILENAME     = "Song File"
YML_SONG_TO_REFERENCE = "Song to Reference"
YML_SONG_OFFSET       = "Offset"
YML_SONG_ADDRESS      = "Address"

INST_OVERWRITE = 0x00
INST_DEFAULT   = 0x1a
SAMPLE_OFFSET_OVERWRITE = 0x7000
SAMPLE_OFFSET_DEFAULT   = 0x95b0
SONG_ADDRESS_TABLE_ENGINE_ARAM_ADDR = 0x2e4a

@dataclass
class EBInstrument:
    '''Class that keeps track of all of an instrument's data.'''
    adsr1: int
    adsr2: int
    gain: int
    multiplier: int
    submultiplier: int
    sample: Union[Block, int, None]
    sample_loop_offset: Union[int, None]

def extract_pack_parts(rom: Block, pack_ptr: int) -> List[Tuple[int,int,Block]]:
    parts = []
    start_bank = pack_ptr & 0xff0000
    while pack_ptr < rom.size and pack_ptr & 0xff0000 == start_bank:
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

def parse_config_txt(config_txt: Union[TextIO, str]) -> Tuple[int, int, int, List[EBInstrument], List[EBInstrument]]:
    instrument_keyword_hit = False
    in_instruments = False
    pack_num, base_inst, brr_offset = None, None, None
    instruments: List[EBInstrument] = []
    instrument_files: List[EBInstrument] = []
    if isinstance(config_txt, str):
        lines = config_txt.splitlines()
        line_iter = enumerate(lines, start=1)
    else:
        line_iter = enumerate(config_txt, start=1)
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
            m = re.match(r'^"([^"]*)"\s+\$([0-9a-f]{2})\s+\$([0-9a-f]{2})\s+\$([0-9a-f]{2})\s+\$([0-9a-f]{2})\s+\$([0-9a-f]{2})$', line, flags=re.IGNORECASE)
            if m:
                filename = m.group(1)
                instinfo = [int(val, base=16) for val in m.groups()[1:]]
                instrument = EBInstrument(*(instinfo + [None, None]))
                instruments.append(instrument)
                instrument_files.append(filename)
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
                
    return pack_num, base_inst, brr_offset, instruments, instrument_files

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
        raise NotImplementedError('Please use a subclass of GenericMusicPack')

class EmptyPack(GenericMusicPack):
    def get_pack_binary_data(self) -> Block:
        return Block(2)

class EngineMusicPack(GenericMusicPack):
    def __init__(self, pack_num: int) -> None:
        if pack_num != 1:
            raise InvalidUserDataError('Engine pack must have pack number $01, has pack ${:02X}'.format(pack_num))
        super().__init__(pack_num)
    def process_song_addresses(self, song_addresses: List[int]) -> None:
        pass
    def convert_to_files(self) -> List[Tuple[str, Union[Block,str]]]:
        return [("engine.bin", self.get_pack_binary_data())]
    def load_from_files(self, file_loader):
        try:
            with file_loader('engine.bin') as f:
                data = Block()
                data.from_array(array('B',f.read()))
        except FileNotFoundError:
            raise InvalidUserDataError("engine.bin doesn't exist")
        self.parts = extract_pack_parts(data, 0)

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
        brr_ptr = 0
        brr_addrs: Dict[Block, int] = {}
        for brr in brr_set:
            brr_addrs[brr] = brr_ptr
            brr_ptr += len(brr)
        brr_part_size = brr_ptr
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
                sample_addr = brr_addrs[inst.sample] + self.brr_sample_dump_offset
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
            brr_with_loop[2:] = brr
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
    
    # For loading from project
    def load_from_files(self, file_loader):
        # Check for config.txt
        try:
            config_txt = file_loader('config.txt', astext=True)
        except FileNotFoundError:
            raise InvalidUserDataError("config doesn't exist in instrument pack directory")
        # Parse config.txt
        pack_num, base_instrument, brr_sample_dump_offset, instruments, instrument_files = parse_config_txt(config_txt)
        if pack_num != self.pack_num:
            # TODO: Should this throw an error??
            raise InvalidUserDataError("instrument pack {:02X}'s config.txt has pack number {:02X}".format(self.pack_num, pack_num))
        # Set our class's data
        self.base_instrument = base_instrument
        self.brr_sample_dump_offset = brr_sample_dump_offset
        # Load BRR data
        for inst, filename in zip(instruments, instrument_files):
            try:
                brr_raw_data: bytes = file_loader(filename, astext=False).read()
                brr_data = Block()
                brr_data.from_array(array('B',brr_raw_data))
            except FileNotFoundError:
                raise InvalidUserDataError("instrument BRR '{}' doesn't exist in instrument pack directory".format(filename))
            inst.sample = brr_data[2:]
            inst.sample_loop_offset = brr_data.read_multi(0, 2)
        self.instruments = instruments

def relocate_song_data(src: int, dst: int, data: Block) -> Block:
    # Deep copy so we won't be modifying the original data
    out = Block()
    out.from_block(data)
    # Let's parse a song :)
    data_ptr = 0
    try:
        # Helper functions
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
        pattern_set = set()
        phrases_done = set()
        phrase_relocations = set()
        while True:
            phrases_done.add(data_ptr)
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
                    # Note that we have to fix the loop address later
                    phrase_relocations.add(data_ptr + 2)
                    rel_jump_ptr = consume_word() - src
                    check_rel_ptr_in_bounds(rel_jump_ptr, "Phrase loop address")
                    if rel_jump_ptr not in phrases_done:
                        # Take jump if we haven't yet
                        data_ptr = rel_jump_ptr
                    elif pattern_ptr >= 0x80:
                        # Don't fallthrough on unconditional jump - stop processing
                        break       
            else:
                # Actually a phrase pointer - add to list
                phrase_relocations.add(data_ptr)
                rel_pattern_ptr = pattern_ptr - src
                check_rel_ptr_in_bounds(rel_pattern_ptr, "Pattern address")
                pattern_set.add(rel_pattern_ptr)
        # Relocate phrase pointers
        for phrase_ptr in phrase_relocations:
            # We change the last word, so we have to set data_ptr
            # at the end of the word.
            data_ptr = phrase_ptr + 2
            change_last_word()
        
        # Parse all patterns
        track_list = []
        for pattern_table_addr in pattern_set:
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
        tracks_done = set()
        cmds_done = set()
        for track_ptr in track_list:
            data_ptr = track_ptr
            if track_ptr in tracks_done:
                continue
            tracks_done.add(track_ptr)
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
                    if data_ptr in cmds_done:
                        consume_word()
                        consume_byte()
                        continue
                    cmds_done.add(data_ptr)
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
        raise InvalidUserDataError("Error at addr ${:04X}: {}".format(data_ptr + src, e))

@dataclass
class Song:
    song_number: int
    @classmethod
    def from_yml_data(cls, song_num: int, yml_data: Dict[str,Union[int,str]]):
        raise NotImplementedError('Please use a subclass of Song')
    def get_song_packs(self) -> Tuple[int,int,int]:
        raise NotImplementedError('Please use a subclass of Song')
    def get_song_aram_address(self) -> int:
        raise NotImplementedError('Please use a subclass of Song')
    def to_yml_lines(self) -> List[str]:
        raise NotImplementedError('Please use a subclass of Song')

@dataclass
class SongWithData(Song):
    instrument_pack_1: int
    instrument_pack_2: int
    
    pack_number: int
    data_address: int
    data: Block

    song_path: str

    @classmethod
    def from_yml_data(cls, song_num: int, yml_data: Dict[str,Union[int,str]]):
        required_fields = (YML_SONG_PACK, YML_SONG_FILENAME)
        for field in required_fields:
            if field not in yml_data:
                raise InvalidUserDataError("Expected field {} in YAML")
        return cls(song_num, None, None,
                   yml_data[YML_SONG_PACK], None, None,
                   yml_data[YML_SONG_FILENAME])
    def get_song_packs(self) -> Tuple[int, int, int]:
        return (self.instrument_pack_1, self.instrument_pack_2, self.pack_number)
    def get_song_aram_address(self) -> int:
        return self.data_address
    def to_yml_lines(self) -> List[str]:
        yml_lines = [
            '{}: 0x{:02X}'.format(YML_SONG_PACK, self.pack_number),
            '{}: {}'.format(YML_SONG_FILENAME, self.song_path),
        ]
        return yml_lines

@dataclass
class SongThatIsPartOfAnother(Song):
    parent_song: Union[int,SongWithData]
    offset: int

    @classmethod
    def from_yml_data(cls, song_num: int, yml_data: Dict[str,Union[int,str]]):
        required_fields = (YML_SONG_TO_REFERENCE, YML_SONG_OFFSET)
        for field in required_fields:
            if field not in yml_data:
                raise InvalidUserDataError("Expected field {} in YAML")
        return cls(song_num, yml_data[YML_SONG_TO_REFERENCE], yml_data[YML_SONG_OFFSET])
    def get_song_packs(self) -> Tuple[int, int, int]:
        return self.parent_song.get_song_packs()
    def get_song_aram_address(self) -> int:
        return self.parent_song.get_song_aram_address() + self.offset
    def to_yml_lines(self) -> List[str]:
        yml_lines = [
            '{}: 0x{:02X}'.format(YML_SONG_TO_REFERENCE, self.parent_song.song_number),
            '{}: {}'.format(YML_SONG_OFFSET, self.offset),
        ]
        return yml_lines

@dataclass
class InEngineSong(Song):
    instrument_pack_1: int
    instrument_pack_2: int
    pack_number: int
    data_address: int

    @classmethod
    def from_yml_data(cls, song_num: int, yml_data: Dict[str,Union[int,str]]):
        required_fields = (YML_SONG_PACK, YML_INST_PACK_1, YML_INST_PACK_2, YML_SONG_ADDRESS)
        for field in required_fields:
            if field not in yml_data:
                raise InvalidUserDataError("Expected field {} in YAML")
        return cls(song_num,
                   yml_data[YML_INST_PACK_1],
                   yml_data[YML_INST_PACK_2],
                   yml_data[YML_SONG_PACK],
                   yml_data[YML_SONG_ADDRESS])
    def get_song_packs(self) -> Tuple[int, int, int]:
        return (self.instrument_pack_1, self.instrument_pack_2, self.pack_number)
    def get_song_aram_address(self) -> int:
        return self.data_address
    def to_yml_lines(self) -> List[str]:
        yml_lines = [
            '{}: 0x{:02X}'.format(YML_SONG_PACK, self.pack_number),
            '{}: 0x{:02X}'.format(YML_INST_PACK_1, self.instrument_pack_1),
            '{}: 0x{:02X}'.format(YML_INST_PACK_2, self.instrument_pack_2),
            '{}: 0x{:04X}'.format(YML_SONG_ADDRESS, self.get_song_aram_address()),
        ]
        return yml_lines

def song_obj_from_yml(song_num: int, yml_data: Dict[str,Union[str,int]]) -> Song:
    if YML_SONG_FILENAME in yml_data:
        song_type = SongWithData
    elif YML_SONG_TO_REFERENCE in yml_data:
        song_type = SongThatIsPartOfAnother
    elif YML_SONG_ADDRESS in yml_data:
        song_type = InEngineSong
    else:
        raise InvalidUserDataError("Unable to deduce song type from YAML data is missing one of these fields")
    return song_type.from_yml_data(song_num, yml_data)

class SongMusicPack(GenericMusicPack):
    def __init__(self, pack_num: int) -> None:
        super().__init__(pack_num)
        self.songs: List[SongWithData] = []
    
    def set_data_from_yaml(self, song_metadata: Dict[int, Dict]) -> None:
        for song_num, yml_data in song_metadata.items():
            song_obj = song_obj_from_yml(song_num, yml_data)
            self.songs.append(song_obj)
    
    def load_from_parts(self, parts: List[Tuple[int, int, Block]]) -> None:
        self.parts = parts
        self.songs = []
        for part_addr, _, part_data in parts:
            song = SongWithData(None, None, None, self.pack_num, part_addr, part_data, None)
            self.songs.append(song)

    def save_to_parts(self) -> None:
        song_output_ptr = 0x4800
        self.parts = []
        for song in sorted((s for s in self.songs if isinstance(s, SongWithData)), key=lambda s: s.data_address):
            if song.data_address != song_output_ptr:
                # Relocate song
                log.debug("Relocating song $%02X to address $%04X", song.song_number, song_output_ptr)
                new_data = relocate_song_data(song.data_address, song_output_ptr, song.data)
                song.data = new_data
            size = len(song.data)
            song.data_address = song_output_ptr
            self.parts.append((song.data_address, size, song.data))
            song_output_ptr += size
        if song_output_ptr > 0x6c00:
            raise InvalidUserDataError("Data for song pack {} extends past data area. "
                                       "Remove songs from the pack.".format(self.pack_num))

    # For writing to project
    def convert_to_files(self) -> List[Tuple[str, Union[Block,str]]]:
        files_to_output: List[Tuple[str, Union[Block,str]]] = []

        for song in self.songs:
            if song.song_number is None:
                log.error("Issue with song pack ${:02X} at address ${:04X}".format(self.pack_num, song.get_song_aram_address()))
                raise CoilSnakeInternalError("Metadata is not set when converting songs to files")
            ebm_path = "song-{:02X}.ebm".format(song.song_number)
            song.song_path = ebm_path

            ### Write out EBM file
            ebm_data = Block(len(song.data) + 4)
            # Write length, addr
            ebm_data.write_multi(0, len(song.data), 2)
            ebm_data.write_multi(2, song.data_address, 2)
            # Write data chunk
            ebm_data[4:len(ebm_data)] = song.data
            # Add to file list
            files_to_output.append((ebm_path, ebm_data))

            ### Write out EBM.yml file
            yml_lines = []
            yml_lines.append("{}: 0x{:02X}\n".format(YML_INST_PACK_1, song.instrument_pack_1))
            yml_lines.append("{}: 0x{:02X}\n".format(YML_INST_PACK_2, song.instrument_pack_2))
            yml_str = ''.join(yml_lines)
            files_to_output.append((ebm_path + '.yml', yml_str))

        return files_to_output
    
    # For loading from project
    def load_from_files(self, file_loader):
        songs_with_data = {s.song_number: s for s in self.songs if isinstance(s, SongWithData)}
        for song in self.songs:
            if song.song_number in songs_with_data:
                # Read YML
                try:
                    ebm_yml_data = yml_load(file_loader(song.song_path+'.yml', astext=True))
                except FileNotFoundError:
                    raise InvalidUserDataError("'{}' missing".format(song.song_path+'.yml'))
                required_fields = (YML_INST_PACK_1, YML_INST_PACK_2)
                for field in required_fields:
                    if field not in ebm_yml_data:
                        raise InvalidUserDataError("Expected field {} in YAML")
                song.instrument_pack_1 = ebm_yml_data[YML_INST_PACK_1]
                song.instrument_pack_2 = ebm_yml_data[YML_INST_PACK_2]
                # Read EBM
                try:
                    ebm_raw_data = file_loader(song.song_path, astext=False).read()
                except FileNotFoundError:
                    raise InvalidUserDataError("'{}' missing".format(song.song_path))
                ebm_data = Block(len(ebm_raw_data))
                ebm_data.from_array(array('B',ebm_raw_data))
                song.data_address = ebm_data.read_multi(2, 2)
                song.data = ebm_data[4:]
            elif isinstance(song, SongThatIsPartOfAnother) and isinstance(song.parent_song, int):
                try:
                    song.parent_song = songs_with_data[song.parent_song]
                except KeyError:
                    raise CoilSnakeInternalError("Dependent song is not in same pack as parent song")

def check_if_song_is_part_of_another(song_num: int, song_pack: SongMusicPack, song_addr: int) -> Union[None,SongThatIsPartOfAnother]:
    for song in song_pack.songs:
        if song.data_address <= song_addr < song.data_address + len(song.data):
            return SongThatIsPartOfAnother(song_num, song, song_addr - song.data_address)
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
