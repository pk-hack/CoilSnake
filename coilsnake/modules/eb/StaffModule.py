import logging

from coilsnake.exceptions.common.exceptions import CoilSnakeError, InvalidUserDataError
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.assets import open_asset
from coilsnake.util.common.yml import yml_load
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address

log = logging.getLogger(__name__)

STAFF_TEXT_POINTER_OFFSET = 0x4f253
LENGTH_OFFSETS = [0x4f583, 0x4f58c, 0x4f66f]

MODE_CONTROL = 0
MODE_SMALL   = 1
MODE_BIG     = 2
MODE_SPACE   = 3

HEIGHT_SMALL = 8
HEIGHT_BIG   = 16

CONTROL_END_OF_LINE  = 0x00
CONTROL_SMALL        = 0x01
CONTROL_BIG          = 0x02
CONTROL_SPACE        = 0x03
CONTROL_PLAYER_NAME  = 0x04
CONTROL_END_OF_STAFF = 0xff

MAX_ROW = 0xf - 0x4
MAX_COL = 0xf

SCREEN_WIDTH_IN_TILES = 32

ENTRY_TYPE = 'Type'
ENTRY_ROW  = 'Row'
ENTRY_COL  = 'Column'
ENTRY_CHAR = 'Character'

STAFF_CHARS_FILE_NAME = 'Staff/staff_chars'
STAFF_TEXT_FILE_NAME  = 'Staff/staff_text'

KEYWORD_BYTE_HEIGHT = {
    'player_name': (CONTROL_PLAYER_NAME, HEIGHT_BIG)
}


class StaffModule(EbModule):
    NAME = 'Staff'
    FREE_RANGES = [(0x21413f, 0x214de7)]

    def __init__(self):
        self.big    = {}
        self.small  = {}
        self.data   = []
        self.height = 0

    @staticmethod
    def check_row_col_error(name, val, max_val):
        if val > max_val:
            raise InvalidUserDataError(
                'Invalid \'{}\'={} - should be between 0 and {}.'.format(
                    name, val, max_val
                )
            )

    def read_staff_chars(self, yml_data):
        log.debug('Reading staff character-to-code mapping')

        for k, v in yml_data.items():
            vrow  = v[ENTRY_ROW]
            vcol  = v[ENTRY_COL]
            self.check_row_col_error(ENTRY_ROW, vrow, MAX_ROW)
            self.check_row_col_error(ENTRY_COL, vcol, MAX_COL)
            vtile = (vrow << 4) | vcol
            vtype = v[ENTRY_TYPE]
            vchar = v[ENTRY_CHAR]

            if vtype == 'big':
                self.big[str(vchar)]   = vtile + 0x40
            elif vtype == 'small':
                self.small[str(vchar)] = vtile + 0x40
            else:
                raise InvalidUserDataError(
                    'Invalid \'{}\' for entry with \'{}\'={}, \'{}\'={} and \'{}\'={}.'.format(
                        ENTRY_TYPE, ENTRY_ROW, vrow, ENTRY_COL, vcol, ENTRY_CHAR, vchar
                    )
                )

    def read_staff_chars_from_assets(self):
        with open_asset('structures', 'eb_staff_chars.yml') as f:
            yml_data = yml_load(f)

        self.read_staff_chars(yml_data)

    def read_staff_chars_from_project(self, resource_open):
        with resource_open(STAFF_CHARS_FILE_NAME, 'yml', True) as f:
            yml_data = yml_load(f)

        self.read_staff_chars(yml_data)

    def read_text_line_from_project(self, byte, line, mapping, height):
        self.data.append(byte)

        if not line:
            line = ' '

        for char in line:
            self.data.append(mapping[char])

        self.data.append(CONTROL_END_OF_LINE)
        self.height += height

    def read_small_line_from_project(self, line):
        self.read_text_line_from_project(CONTROL_SMALL, line, self.small, HEIGHT_SMALL)

    def read_big_line_from_project(self, line):
        self.read_text_line_from_project(CONTROL_BIG, line, self.big, HEIGHT_BIG)

    def read_space_from_project(self, how_much):
        if how_much == 0: # Ignore zero-sized space
            return

        self.data.append(CONTROL_SPACE)
        self.data.append(how_much)
        self.height += HEIGHT_SMALL * how_much

    def read_keyword_from_project(self, keyword):
        if keyword not in KEYWORD_BYTE_HEIGHT:
            raise InvalidUserDataError(
                'Invalid keyword={} in {}.yml - should be one of {}.'.format(
                    keyword, name, KEYWORD_BYTE_HEIGHT.keys()
                )
            )

        byte, height = KEYWORD_BYTE_HEIGHT[keyword]
        self.data.append(byte)
        self.height += height

    def read_staff_text_from_project(self, resource_open):
        with resource_open(STAFF_TEXT_FILE_NAME, 'md', True) as f:
            line = f.readline()

            while line:
                line = line.strip()

                if not line:
                    line = f.readline()
                    continue

                text = line[1:].lstrip()
                mark = line[0]
                line = f.readline()

                if mark == '>':
                    self.read_space_from_project(int(text))
                elif mark not in ['#', '-']:
                    self.read_keyword_from_project(mark + text)
                elif len(text) > SCREEN_WIDTH_IN_TILES:
                    raise InvalidUserDataError(
                        'Text \'{}\' is too long - must have at most {} characters'.format(
                            text, SCREEN_WIDTH_IN_TILES
                        )
                    )
                elif mark == '#':
                    self.read_small_line_from_project(text)
                else:
                    self.read_big_line_from_project(text)

        self.data.append(CONTROL_END_OF_STAFF)

    def print_keyword(self, f, byte):
        for item in KEYWORD_BYTE_HEIGHT.items():
            keyword, v = item
            b, h = v

            if byte == b:
                f.write('{}\n'.format(keyword))
                return MODE_CONTROL
        else:
            raise CoilSnakeError('Unknown control byte 0x{:X}'.format(byte))

    def print_control(self, f, byte):
        if byte == CONTROL_SMALL:
            f.write('# ')
            return MODE_SMALL
        elif byte == CONTROL_BIG:
            f.write('- ')
            return MODE_BIG
        elif byte == CONTROL_SPACE:
            f.write('> ')
            return MODE_SPACE
        elif byte == CONTROL_END_OF_STAFF:
            return MODE_CONTROL
        else:
            return self.print_keyword(f, byte)

    def print_space(self, f, byte):
        f.write('{}\n\n'.format(byte))
        return MODE_CONTROL

    def print_char(self, f, byte, mode, mapping_big, mapping_small):
        if byte == CONTROL_END_OF_LINE:
            f.write('\n')
            return MODE_CONTROL

        if mode == MODE_BIG:
            f.write(mapping_big[byte])
        else:
            f.write(mapping_small[byte])

        return mode

    def read_pointer_from_rom(self, rom):
        return (
            (rom[STAFF_TEXT_POINTER_OFFSET + 6] << 16) |
            rom.read_multi(STAFF_TEXT_POINTER_OFFSET, 2)
        )

    def write_pointer_to_rom(self, rom, pointer):
        rom[STAFF_TEXT_POINTER_OFFSET + 6] = pointer >> 16
        rom.write_multi(STAFF_TEXT_POINTER_OFFSET, pointer & 0xFFFF, 2)

    def read_from_rom(self, rom):
        staff_text_offset = from_snes_address(self.read_pointer_from_rom(rom))
        self.read_staff_chars_from_assets()
        log.debug('Reading staff text')
        i    = 0
        byte = 0x00

        while byte != CONTROL_END_OF_STAFF:
            byte = rom[staff_text_offset + i]
            self.data.append(byte)
            i += 1

    def write_to_rom(self, rom):
        offset = rom.allocate(size=len(self.data))
        self.write_pointer_to_rom(rom, to_snes_address(offset))
        log.debug('Writing staff text')
        rom[offset:offset + len(self.data)] = self.data

        for length_offset in LENGTH_OFFSETS:
            rom.write_multi(length_offset, self.height, 2)

    def read_from_project(self, resource_open):
        self.read_staff_chars_from_project(resource_open)
        log.debug('Reading staff text')
        self.read_staff_text_from_project(resource_open)

    def write_to_project(self, resource_open):
        mode     = MODE_CONTROL
        invbig   = {v: k for (k, v) in self.big.items()}
        invsmall = {v: k for (k, v) in self.small.items()}

        with open_asset('structures', 'eb_staff_chars.yml') as f:
            staff_chars = f.read()

        with resource_open(STAFF_CHARS_FILE_NAME, 'yml', True) as f:
            f.write(staff_chars)

        with resource_open(STAFF_TEXT_FILE_NAME, 'md', True) as f:
            for byte in self.data:
                if mode == MODE_CONTROL:
                    mode = self.print_control(f, byte)
                elif mode == MODE_SPACE:
                    mode = self.print_space(f, byte)
                else:
                    mode = self.print_char(f, byte, mode, invbig, invsmall)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version < 10:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
