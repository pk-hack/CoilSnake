import logging

from PIL import Image

from coilsnake.model.eb.fonts import EbFont, EbCreditsFont, FONT_IMAGE_PALETTE
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.common.yml import yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


log = logging.getLogger(__name__)

FONT_POINTER_TABLE_OFFSET = 0xC3F054
FONT_FILENAMES = ["0", "1", "3", "4", "2"]

CREDITS_GRAPHICS_ASM_POINTER = 0x4f1a7
CREDITS_PALETTES_ADDRESS = 0x21e914


class FontModule(EbModule):
    NAME = "Fonts"
    FREE_RANGES = [
        (0x21e528, 0x21e913),  # Credits font graphics
        (0x210c7a, 0x212ef9),  # Fonts 0, 2, 3, and 4
        (0x201359, 0x201fb8),  # Font 1
    ]

    def __init__(self):
        super(FontModule, self).__init__()
        self.font_pointer_table = eb_table_from_offset(offset=FONT_POINTER_TABLE_OFFSET)
        self.fonts = [
            EbFont(num_characters=128, tile_width=16, tile_height=16),
            EbFont(num_characters=128, tile_width=16, tile_height=16),
            EbFont(num_characters=128, tile_width=8, tile_height=16),
            EbFont(num_characters=128, tile_width=8, tile_height=8),
            EbFont(num_characters=128, tile_width=16, tile_height=16)
        ]
        self.credits_font = EbCreditsFont()

    def read_from_rom(self, rom):
        self.font_pointer_table.from_block(block=rom,
                                           offset=from_snes_address(FONT_POINTER_TABLE_OFFSET))
        for i, font in enumerate(self.fonts):
            log.debug("Reading font #{} from the ROM".format(FONT_FILENAMES[i]))
            font.from_block(block=rom,
                            tileset_offset=from_snes_address(self.font_pointer_table[i][1]),
                            character_widths_offset=from_snes_address(self.font_pointer_table[i][0]))

        self.read_credits_font_from_rom(rom)

    def write_to_rom(self, rom):
        self.font_pointer_table.from_block(block=rom,
                                           offset=from_snes_address(FONT_POINTER_TABLE_OFFSET))
        for i, font in enumerate(self.fonts):
            log.debug("Writing font #{} to the ROM".format(FONT_FILENAMES[i]))

            graphics_offset, widths_offset = font.to_block(block=rom)
            self.font_pointer_table[i][0] = to_snes_address(widths_offset)
            self.font_pointer_table[i][1] = to_snes_address(graphics_offset)
        self.font_pointer_table.to_block(block=rom,
                                         offset=from_snes_address(FONT_POINTER_TABLE_OFFSET))

        self.write_credits_font_to_rom(rom)

    def read_from_project(self, resource_open):
        for i, font in enumerate(self.fonts):
            with resource_open("Fonts/" + FONT_FILENAMES[i], 'png') as image_file:
                with resource_open("Fonts/" + FONT_FILENAMES[i] + "_widths", "yml", True) as widths_file:
                    font.from_files(image_file, widths_file, image_format="png", widths_format="yml")

        self.read_credits_font_from_project(resource_open)

    def write_to_project(self, resource_open):
        for i, font in enumerate(self.fonts):
            # Write the PNG
            with resource_open("Fonts/" + FONT_FILENAMES[i], 'png') as image_file:
                with resource_open("Fonts/" + FONT_FILENAMES[i] + "_widths", "yml", True) as widths_file:
                    font.to_files(image_file, widths_file, image_format="png", widths_format="yml")

        self.write_credits_font_to_project(resource_open)

    def read_credits_font_from_rom(self, rom):
        log.debug("Reading the credits font from the ROM")
        self.credits_font.from_block(block=rom,
                                     tileset_asm_pointer_offset=CREDITS_GRAPHICS_ASM_POINTER,
                                     palette_offset=CREDITS_PALETTES_ADDRESS)

    def write_credits_font_to_rom(self, rom):
        log.debug("Writing the credits font to the ROM")
        self.credits_font.to_block(block=rom,
                                   tileset_asm_pointer_offset=CREDITS_GRAPHICS_ASM_POINTER,
                                   palette_offset=CREDITS_PALETTES_ADDRESS)

    def write_credits_font_to_project(self, resource_open):
        with resource_open("Fonts/credits", "png") as image_file:
            self.credits_font.to_files(image_file, "png")

    def read_credits_font_from_project(self, resource_open):
        with resource_open("Fonts/credits", "png") as image_file:
            self.credits_font.from_files(image_file, "png")

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version == 5:
            # Expand all the fonts from 96 characters to 128 characters
            for i, font in enumerate(self.fonts):
                log.debug("Expanding font #{}".format(FONT_FILENAMES[i]))
                image_resource_name = "Fonts/" + FONT_FILENAMES[i]
                widths_resource_name = "Fonts/" + FONT_FILENAMES[i] + "_widths"
                new_image_w, new_image_h = font.image_size()

                # Expand the image

                with resource_open_r(image_resource_name, 'png') as image_file:
                    image = open_indexed_image(image_file)

                    expanded_image = Image.new("P", (new_image_w, new_image_h), None)
                    for y in range(new_image_h):
                        for x in range(new_image_w):
                            expanded_image.putpixel((x, y), 1)
                    FONT_IMAGE_PALETTE.to_image(expanded_image)
                    expanded_image.paste(image, (0, 0))

                    with resource_open_w(image_resource_name, 'png') as image_file2:
                        expanded_image.save(image_file2, "png")

                # Expand the widths

                with resource_open_r(widths_resource_name, "yml", True) as widths_file:
                    widths_dict = yml_load(widths_file)

                for character_id in range(96, 128):
                    if character_id not in widths_dict:
                        widths_dict[character_id] = 0

                with resource_open_w(widths_resource_name, "yml", True) as widths_file:
                    yml_dump(widths_dict, widths_file, default_flow_style=False)

            self.upgrade_project(6, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        elif old_version <= 2:
            # The credits font was a new feature in version 3

            self.read_credits_font_from_rom(rom)
            self.write_credits_font_to_project(resource_open_w)
            self.upgrade_project(3, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
