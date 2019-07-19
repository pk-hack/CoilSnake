import logging

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.eb.graphics import EbCastMiscGraphic, EbCastNameGraphic
from coilsnake.model.eb.table import EbStandardNullTerminatedTextTableEntry
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_image, open_indexed_image
from coilsnake.util.common.yml import yml_dump, yml_load
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, to_snes_address, write_asm_pointer

log = logging.getLogger(__name__)


CAST_DYNAMIC_NAMES_FILE_NAME = 'Cast/dynamic_names'
CAST_FORMATTING_FILE_NAME = 'Cast/graphics_entries'

CAST_FORMATTING_ENTRY_SIZE = 3
CAST_FORMATTING_OFFSET = 0x212efa + CAST_FORMATTING_ENTRY_SIZE # skip the first entry
CAST_FORMATTING_TABLE_SIZE = 0x90 - CAST_FORMATTING_ENTRY_SIZE # first entry was skipped
CAST_FORMATTING_OFFSET_END = CAST_FORMATTING_OFFSET + CAST_FORMATTING_TABLE_SIZE

CAST_GRAPHICS_PALETTE_OFFSET = 0x21d815
CAST_MISC_GRAPHICS_ASM_POINTER_OFFSET = 0x4e42e
CAST_NAME_GRAPHICS_ASM_POINTER_OFFSET = 0x4e446

CAST_GRAPHICS_BLOCK_BEGIN = 0x21d815
CAST_GRAPHICS_BLOCK_END = 0x21e4e7


class EbDynamicCastName(object):
    def __init__(self, key, asm_offset):
        self.key = key
        self.asm_offset = asm_offset
        self.table_entry = EbStandardNullTerminatedTextTableEntry.create(12)
        self.name = ''
        self.prefixed = True

    def read_from_rom(self, rom):
        self.name = self.table_entry.from_block(rom, from_snes_address(read_asm_pointer(block=rom, offset=self.asm_offset)))
        self.prefixed = (rom.read_multi(self.asm_offset - 0x14, 4) != 0xeaeaeaea)

    def write_to_rom(self, rom):
        loc = rom.allocate(size=len(self.name) + 1)
        write_asm_pointer(block=rom, offset=self.asm_offset, pointer=to_snes_address(loc))
        self.table_entry.to_block(rom, loc, self.name)

        if not self.prefixed:
            rom.write_multi(self.asm_offset - 0x14, 0xeaeaeaea, 4)

    def read_from_yml_data(self, yml_data):
        self.name = yml_data[self.key]['name']
        self.prefixed = yml_data[self.key]['prefixed']

    def write_to_yml_data(self, yml_data):
        yml_data[self.key] = {
            'name': self.name,
            'prefixed': self.prefixed
        }

# This info will be exported as if the game:
# - Uses 16x16 tiles (instead of 8x8), preventing bad text alignment with odd sizes.
# - Begins image indexing at 0 (instead of 0x10 for misc, 0x30 for names).
# - Has a special field to choose between name and misc graphics.
# - Does not need the first entry to have size 0 (by not exporting it).
class EbCastEntry(object):
    def __init__(self):
        self.begin = 0
        self.size = 0
        self.misc = False

    def read_from_rom(self, rom, offset):
        self.begin = (rom[offset + 1] << 8) | rom[offset]
        self.size = rom[offset + 2] // 2
        self.misc = self.begin < 0x30
        self.begin -= (0x10 if self.misc else 0x30)
        self.begin //= 2

    def write_to_rom(self, rom, offset):
        begin = (self.begin * 2) + (0x10 if self.misc else 0x30)
        size = self.size * 2
        rom[offset]     = begin & 0xFF
        rom[offset + 1] = begin >> 8
        rom[offset + 2] = size

    def set_values(self, begin, size, misc):
        self.begin = begin
        self.size = size
        self.misc = misc

class EbCastFormatting(object):
    def __init__(self):
        self.entries = []

    def read_from_rom(self, rom):
        for addr in range(CAST_FORMATTING_OFFSET, CAST_FORMATTING_OFFSET_END, CAST_FORMATTING_ENTRY_SIZE):
            entry = EbCastEntry()
            entry.read_from_rom(rom, addr)
            self.entries.append(entry)

    def write_to_rom(self, rom):
        for i, entry in enumerate(self.entries):
            entry.write_to_rom(rom, CAST_FORMATTING_OFFSET + i * CAST_FORMATTING_ENTRY_SIZE)

    def read_from_project(self, resource_open):
        formatting_data = {}

        with resource_open(CAST_FORMATTING_FILE_NAME, 'yml', True) as f:
            formatting_data = yml_load(f)

        for fmt_entry in formatting_data:
            entry = EbCastEntry()
            entry.set_values(
                formatting_data[fmt_entry]['begin'],
                formatting_data[fmt_entry]['size'],
                formatting_data[fmt_entry]['misc']
            )
            self.entries.append(entry)

            if entry.size == 0:
                raise InvalidArgumentError('Cast graphics entry number {} has size 0 - would crash the cast screen.'.format(fmt_entry))

    def write_to_project(self, resource_open):
        formatting_data = {}

        for i, entry in enumerate(self.entries):
            formatting_data[i] = {
                'begin': entry.begin,
                'size':  entry.size,
                'misc':  entry.misc
            }

        with resource_open(CAST_FORMATTING_FILE_NAME, 'yml', True) as f:
            yml_dump(formatting_data, f, default_flow_style=False)


class CastModule(EbModule):
    NAME = 'Cast'
    FREE_RANGES = [(CAST_GRAPHICS_BLOCK_BEGIN, CAST_GRAPHICS_BLOCK_END)]

    def __init__(self):
        super(CastModule, self).__init__()
        self.cast_dynamic_names = [
            EbDynamicCastName('Paula\'s dad',  0x4e915),
            EbDynamicCastName('Paula\'s mom',  0x4e9b7),
            EbDynamicCastName('Poo\'s master', 0x4ea60)
        ]
        self.formatting = EbCastFormatting()
        self.name_gfx   = EbCastNameGraphic()
        self.misc_gfx   = EbCastMiscGraphic()

    def read_from_rom(self, rom):
        log.debug('Reading dynamic cast names')

        for n in self.cast_dynamic_names:
            n.read_from_rom(rom)

        log.debug('Reading cast formatting data')
        self.formatting.read_from_rom(rom)

        log.debug('Reading cast name graphics')
        self.read_gfx_from_rom(rom, CAST_NAME_GRAPHICS_ASM_POINTER_OFFSET, self.name_gfx)

        log.debug('Reading miscellaneous cast graphics')
        self.read_gfx_from_rom(rom, CAST_MISC_GRAPHICS_ASM_POINTER_OFFSET, self.misc_gfx)

    def write_to_rom(self, rom):
        log.debug('Writing dynamic cast names')

        for n in self.cast_dynamic_names:
            n.write_to_rom(rom)

        log.debug('Writing cast formatting data')
        self.formatting.write_to_rom(rom)

        log.debug('Writing cast name graphics')
        self.write_gfx_to_rom(rom, CAST_NAME_GRAPHICS_ASM_POINTER_OFFSET, self.name_gfx)

        log.debug('Writing miscellaneous cast graphics')
        self.write_gfx_to_rom(rom, CAST_MISC_GRAPHICS_ASM_POINTER_OFFSET, self.misc_gfx)

    def read_from_project(self, resource_open):
        log.debug('Reading dynamic cast names')
        yml_data = {}

        with resource_open(CAST_DYNAMIC_NAMES_FILE_NAME, 'yml', True) as f:
            yml_data = yml_load(f)

        for n in self.cast_dynamic_names:
            n.read_from_yml_data(yml_data)

        log.debug('Reading cast formatting data')
        self.formatting.read_from_project(resource_open)

        log.debug('Reading cast name graphics')
        self.read_gfx_from_project(self.name_gfx, resource_open)

        log.debug('Reading miscellaneous cast graphics')
        self.read_gfx_from_project(self.misc_gfx, resource_open)

    def write_to_project(self, resource_open):
        log.debug('Writing dynamic cast names')
        yml_data = {}

        for n in self.cast_dynamic_names:
            n.write_to_yml_data(yml_data)

        with resource_open(CAST_DYNAMIC_NAMES_FILE_NAME, 'yml', True) as f:
            yml_dump(yml_data, f, default_flow_style=False)

        log.debug('Writing cast formatting data')
        self.formatting.write_to_project(resource_open)

        log.debug('Writing cast name graphics')
        self.write_gfx_to_project(self.name_gfx, resource_open)

        log.debug('Writing miscellaneous cast graphics')
        self.write_gfx_to_project(self.misc_gfx, resource_open)

    def read_gfx_from_rom(self, rom, offset, gfx):
        gfx.from_block(
            block=rom,
            graphics_offset=from_snes_address(read_asm_pointer(block=rom, offset=offset)),
            arrangement_offset=None,
            palette_offsets=[CAST_GRAPHICS_PALETTE_OFFSET]
        )

    def write_gfx_to_rom(self, rom, offset, gfx):
        graphics_offset, arrangement_offset, palette_offsets = gfx.to_block(block=rom)
        write_asm_pointer(block=rom, offset=offset, pointer=to_snes_address(graphics_offset))

    def read_gfx_from_project(self, obj, resource_open):
        with resource_open(obj.path(), 'png') as image_file:
            image = open_indexed_image(image_file)
            obj.from_image(image, obj.cast_arrangement())

    def write_gfx_to_project(self, obj, resource_open):
        image = obj.image(obj.cast_arrangement())

        with resource_open(obj.path(), 'png') as image_file:
            image.save(image_file, 'png')

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version < 10:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
