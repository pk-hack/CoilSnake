import logging

from coilsnake.exceptions.common.exceptions import CoilSnakeError, InvalidArgumentError
from coilsnake.model.common.ips import IpsPatch
from coilsnake.model.eb.graphics import EbCastMiscGraphic, EbCastNameGraphic
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.table import EbStandardNullTerminatedTextTableEntry
from coilsnake.modules.common.PatchModule import get_ips_filename
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

FREE_CAST_GRAPHICS_BLOCK_BEGIN = 0x21d835
FREE_CAST_GRAPHICS_BLOCK_END   = 0x21e4e5

DYNAMIC_CAST_NAME_MODES = ['none', 'prefix', 'suffix']

# These entries are formatted to be used by EbDynamicCastName
# Their order must be key, asm_pointer_offset, custom_asm_offset, patch_name_prefix
DYNAMIC_CAST_ENTRIES = [
    ('Paula\'s dad',  0x4e915, 0x4e8c7, 'paulas_dad'),
    ('Paula\'s mom',  0x4e9b7, 0x4e980, 'paulas_mom'),
    ('Poo\'s master', 0x4ea60, 0x4ea22, 'poos_master')
]

class EbDynamicCastName(object):
    def __init__(self, key, asm_pointer_offset, custom_asm_offset, patch_name_prefix):
        self.key = key
        self.asm_pointer_offset = asm_pointer_offset
        self.table_entry = EbStandardNullTerminatedTextTableEntry.create(12)
        self.text = ''
        self.mode = 'suffix'
        self.custom_asm_offset = custom_asm_offset
        self.patch_name_prefix = patch_name_prefix

    def read_from_rom(self, rom):
        self.text = self.table_entry.from_block(rom, from_snes_address(read_asm_pointer(block=rom, offset=self.asm_pointer_offset)))

        for mode in DYNAMIC_CAST_NAME_MODES:
            if self.get_patch(mode, rom.type).is_applied(rom):
                self.mode = mode
                break

    def write_to_rom(self, rom):
        if self.mode != 'prefix':
            self.get_patch(self.mode, rom.type).apply(rom)

        loc = rom.allocate(size=self.table_entry.to_block_size(self.text))
        addr = to_snes_address(loc)
        write_asm_pointer(block=rom, offset=self.asm_pointer_offset, pointer=addr)
        self.table_entry.to_block(rom, loc, self.text)

        if self.mode == 'prefix':
            self.get_patch(self.mode, rom.type).apply(rom)
            rom.write_multi(self.custom_asm_offset + 9,  addr & 0xFFFF,       2)
            rom.write_multi(self.custom_asm_offset + 14, (addr >> 16) & 0xFF, 2)
            rom.write_multi(self.custom_asm_offset + 26, len(self.text),      2)

    def get_patch(self, mode, rom_type):
        ips = IpsPatch()
        ips.load(get_ips_filename(rom_type, '{}_{}'.format(self.patch_name_prefix, mode)), 0)
        return ips

    def read_from_yml_data(self, yml_data):
        self.text = yml_data[self.key]['text']
        self.mode = yml_data[self.key]['mode']

        if self.mode not in DYNAMIC_CAST_NAME_MODES:
            raise InvalidArgumentError('Invalid dynamic cast name mode \'{}\' for entry with text \'{}\'. Valid modes are {}'.format(self.mode, self.name, DYNAMIC_CAST_NAME_MODES))

    def write_to_yml_data(self, yml_data):
        yml_data[self.key] = {
            'text': self.text,
            'mode': self.mode
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
        self.begin = rom.read_multi(offset, 2)
        self.size = rom[offset + 2] // 2
        self.misc = (self.begin < 0x30)
        self.begin -= (0x10 if self.misc else 0x30)
        self.begin //= 2

    def write_to_rom(self, rom, offset):
        begin = (self.begin * 2) + (0x10 if self.misc else 0x30)
        rom.write_multi(offset, begin, 2)
        rom[offset + 2] = self.size * 2

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
    FREE_RANGES = [(FREE_CAST_GRAPHICS_BLOCK_BEGIN, FREE_CAST_GRAPHICS_BLOCK_END)]

    def __init__(self):
        super(CastModule, self).__init__()
        self.formatting    = EbCastFormatting()
        self.name_gfx      = EbCastNameGraphic()
        self.misc_gfx      = EbCastMiscGraphic()
        self.dynamic_names = [EbDynamicCastName(*entry) for entry in DYNAMIC_CAST_ENTRIES]

    def read_from_rom(self, rom):
        log.debug('Reading dynamic cast names')

        for n in self.dynamic_names:
            n.read_from_rom(rom)

        log.debug('Reading cast formatting data')
        self.formatting.read_from_rom(rom)

        log.debug('Reading cast name graphics')
        self.read_gfx_from_rom(rom, CAST_NAME_GRAPHICS_ASM_POINTER_OFFSET, self.name_gfx)

        log.debug('Reading miscellaneous cast graphics')
        self.read_gfx_from_rom(rom, CAST_MISC_GRAPHICS_ASM_POINTER_OFFSET, self.misc_gfx)

    def write_to_rom(self, rom):
        log.debug('Writing dynamic cast names')

        for n in self.dynamic_names:
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

        for n in self.dynamic_names:
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

        for n in self.dynamic_names:
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
        gfx.palettes[0].to_block(block=rom, offset=CAST_GRAPHICS_PALETTE_OFFSET)

    def read_gfx_from_project(self, obj, resource_open):
        with resource_open(obj.path(), 'png') as image_file:
            image = open_indexed_image(image_file)
            palette = EbPalette(num_subpalettes=1, subpalette_length=4)
            palette.from_image(image)
            obj.palettes[0] = palette
            obj.from_image(image, obj.cast_arrangement())

    def write_gfx_to_project(self, obj, resource_open):
        image = obj.image(obj.cast_arrangement())

        with resource_open(obj.path(), 'png') as image_file:
            image.save(image_file, 'png')

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version < 10:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
