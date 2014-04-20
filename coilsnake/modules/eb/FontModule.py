import logging

from coilsnake.model.eb.fonts import EbFont, EbCreditsFont
from coilsnake.modules.eb.EbModule import EbModule


log = logging.getLogger(__name__)

FONT_GRAPHICS_ADDRESSES = [0x210cda, 0x2013b9, 0x2122fa, 0x21193a, 0x211f9a]
FONT_CHARACTER_WIDTHS_ADDRESSES = [0x210c7a, 0x201359, 0x21229a, 0x2118da, 0x2118da, 0x211f3a]
CREDITS_GRAPHICS_ASM_POINTER = 0x4f1a7
CREDITS_PALETTES_ADDRESS = 0x21e914


class FontModule(EbModule):
    NAME = "Fonts"
    FREE_RANGES = [(0x21e528, 0x21e913)]  # Credits font graphics

    def __init__(self):
        super(FontModule, self).__init__()
        self.fonts = [
            EbFont(num_characters=96, tile_width=16, tile_height=16),
            EbFont(num_characters=96, tile_width=16, tile_height=16),
            EbFont(num_characters=96, tile_width=16, tile_height=16),
            EbFont(num_characters=96, tile_width=8, tile_height=16),
            EbFont(num_characters=96, tile_width=8, tile_height=8)
        ]
        self.credits_font = EbCreditsFont()

    def read_credits_font_from_rom(self, rom):
        log.info("Reading the credits font from the ROM")
        self.credits_font.from_block(block=rom,
                                     tileset_asm_pointer_offset=CREDITS_GRAPHICS_ASM_POINTER,
                                     palette_offset=CREDITS_PALETTES_ADDRESS)

    def read_from_rom(self, rom):
        for i, (font, graphics_address, widths_address) in enumerate(zip(self.fonts, FONT_GRAPHICS_ADDRESSES,
                                                                         FONT_CHARACTER_WIDTHS_ADDRESSES)):
            log.info("Reading font #{} from the ROM".format(i))
            font.from_block(block=rom, tileset_offset=graphics_address, character_widths_offset=widths_address)

        self.read_credits_font_from_rom(rom)

    def write_credits_font_to_rom(self, rom):
        log.info("Writing the credits font to the ROM")
        self.credits_font.to_block(block=rom,
                                   tileset_asm_pointer_offset=CREDITS_GRAPHICS_ASM_POINTER,
                                   palette_offset=CREDITS_PALETTES_ADDRESS)

    def write_to_rom(self, rom):
        for i, (font, graphics_address, widths_address) in enumerate(zip(self.fonts, FONT_GRAPHICS_ADDRESSES,
                                                                         FONT_CHARACTER_WIDTHS_ADDRESSES)):
            log.info("Writing font #{} to the ROM".format(i))
            font.to_block(block=rom, tileset_offset=graphics_address, character_widths_offset=widths_address)

        self.write_credits_font_to_rom(rom)

    def write_credits_font_to_project(self, resource_open):
        with resource_open("Fonts/credits", "png") as image_file:
            self.credits_font.to_files(image_file, "png")

    def write_to_project(self, resource_open):
        for i, font in enumerate(self.fonts):
            # Write the PNG
            with resource_open("Fonts/" + str(i), 'png') as image_file:
                with resource_open("Fonts/" + str(i) + "_widths", "yml") as widths_file:
                    font.to_files(image_file, widths_file, image_format="png", widths_format="yml")

        self.write_credits_font_to_project(resource_open)

    def read_credits_font_from_project(self, resource_open):
        with resource_open("Fonts/credits", "png") as image_file:
            self.credits_font.from_files(image_file, "png")

    def read_from_project(self, resource_open):
        for i, font in enumerate(self.fonts):
            with resource_open("Fonts/" + str(i), 'png') as image_file:
                with resource_open("Fonts/" + str(i) + "_widths", "yml") as widths_file:
                    font.from_files(image_file, widths_file, image_format="png", widths_format="yml")

        self.read_credits_font_from_project(resource_open)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version <= 2:
            # The credits font was a new feature in version 3

            self.read_credits_font_from_rom(rom)
            self.write_credits_font_to_project(resource_open_w)
            self.upgrade_project(3, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
