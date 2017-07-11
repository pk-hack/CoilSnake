from collections import namedtuple
import logging

from coilsnake.model.eb.graphics import EbTileArrangement, EbTownMap, EbCompanyLogo, EbAttractModeLogo, \
    EbGasStationLogo, EbTownMapIcons
from coilsnake.model.eb.town_maps import TOWN_MAP_NAMES
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image, open_image
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address, read_asm_pointer, write_asm_pointer


log = logging.getLogger(__name__)


TOWN_MAP_RESOURCE_NAMES = ["TownMaps/" + x for x in TOWN_MAP_NAMES]
TOWN_MAP_POINTER_OFFSETS = range(0x202190, 0x202190 + 6 * 4, 4)

TOWN_MAP_ICON_GRAPHICS_ASM_POINTER_OFFSET = 0x4d62f
TOWN_MAP_ICON_PALETTE_ASM_POINTER_OFFSET = 0x4d5c4

EbCompressedGraphicInfo = namedtuple("EbCompressedGraphicInfo",
                                     ["name",
                                      "graphics_asm_pointer_offsets",
                                      "arrangement_asm_pointer_offsets",
                                      "palette_asm_pointer_offsets"])

COMPANY_LOGO_INFOS = [EbCompressedGraphicInfo(name="Logos/Nintendo",
                                              graphics_asm_pointer_offsets=[0xeea3],
                                              arrangement_asm_pointer_offsets=[0xeebb],
                                              palette_asm_pointer_offsets=[0xeed3]),
                      EbCompressedGraphicInfo(name="Logos/APE",
                                              graphics_asm_pointer_offsets=[0xeefb],
                                              arrangement_asm_pointer_offsets=[0xef13],
                                              palette_asm_pointer_offsets=[0xef2b]),
                      EbCompressedGraphicInfo(name="Logos/HALKEN",
                                              graphics_asm_pointer_offsets=[0xef52],
                                              arrangement_asm_pointer_offsets=[0xef6a],
                                              palette_asm_pointer_offsets=[0xef82])]

ATTRACT_MODE_INFOS = [EbCompressedGraphicInfo(name="Logos/ProducedBy",
                                              graphics_asm_pointer_offsets=[0x4dd73],
                                              arrangement_asm_pointer_offsets=[0x4dd3a],
                                              palette_asm_pointer_offsets=[0x4dd9f]),
                      EbCompressedGraphicInfo(name="Logos/PresentedBy",
                                              graphics_asm_pointer_offsets=[0x4de1b],
                                              arrangement_asm_pointer_offsets=[0x4dde2],
                                              palette_asm_pointer_offsets=[0x4de47])]

GAS_STATION_INFO = EbCompressedGraphicInfo(name="Logos/GasStation",
                                           graphics_asm_pointer_offsets=[0xf0f0],
                                           arrangement_asm_pointer_offsets=[0xf11b],
                                           palette_asm_pointer_offsets=[0xf147, 0xf3ba, 0xf3f0])

TOWN_MAP_ICON_PREVIEW_SUBPALETTES = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,

    0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,

    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,

    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,

    1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,

    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
TOWN_MAP_ICON_PREVIEW_ARRANGEMENT = EbTileArrangement(width=16, height=18)
for i in range(16 * 18):
    item = TOWN_MAP_ICON_PREVIEW_ARRANGEMENT[i % 16, i // 16]
    item.is_priority = False
    item.is_horizontally_flipped = False
    item.is_vertically_flipped = False
    item.subpalette = TOWN_MAP_ICON_PREVIEW_SUBPALETTES[i]
    item.tile = i


class CompressedGraphicsModule(EbModule):
    NAME = "Compressed Graphics"
    FREE_RANGES = [(0x2021a8, 0x20ed02),  # Town Map data
                   (0x214ec1, 0x21ae7b),  # Company Logos, "Produced by" and "Presented by", and Gas Station
                   (0x21ea50, 0x21f203)]  # Town map icon graphics and palette

    def __init__(self):
        super(CompressedGraphicsModule, self).__init__()
        self.town_maps = [EbTownMap() for x in TOWN_MAP_POINTER_OFFSETS]
        self.town_map_icons = EbTownMapIcons()
        self.company_logos = [EbCompanyLogo() for x in COMPANY_LOGO_INFOS]
        self.attract_mode_logos = [EbAttractModeLogo() for x in ATTRACT_MODE_INFOS]
        self.gas_station_logo = EbGasStationLogo()

    def __exit__(self, type, value, traceback):
        del self.town_maps
        del self.town_map_icons
        del self.company_logos
        del self.attract_mode_logos
        del self.gas_station_logo

    def read_from_rom(self, rom):
        self.read_town_maps_from_rom(rom)
        self.read_town_map_icons_from_rom(rom)
        self.read_company_logos_from_rom(rom)
        self.read_attract_mode_logos_from_rom(rom)
        self.read_gas_station_from_rom(rom)

    def write_to_rom(self, rom):
        self.write_town_maps_to_rom(rom)
        self.write_town_map_icons_to_rom(rom)
        self.write_company_logos_to_rom(rom)
        self.write_attract_mode_logos_to_rom(rom)
        self.write_gas_station_to_rom(rom)

    def read_town_maps_from_rom(self, rom):
        log.debug("Reading town maps")
        for pointer_offset, town_map in zip(TOWN_MAP_POINTER_OFFSETS, self.town_maps):
            offset = from_snes_address(rom.read_multi(pointer_offset, size=4))
            town_map.from_block(block=rom,
                                offset=offset)

    def write_town_maps_to_rom(self, rom):
        log.debug("Writing town maps")
        for pointer_offset, town_map in zip(TOWN_MAP_POINTER_OFFSETS, self.town_maps):
            offset = town_map.to_block(rom)
            rom.write_multi(pointer_offset, to_snes_address(offset), size=4)

    def read_town_map_icons_from_rom(self, rom):
        log.debug("Reading town map icons")
        graphics_offset = from_snes_address(read_asm_pointer(block=rom,
                                                             offset=TOWN_MAP_ICON_GRAPHICS_ASM_POINTER_OFFSET))
        palette_offset = from_snes_address(read_asm_pointer(block=rom,
                                                            offset=TOWN_MAP_ICON_PALETTE_ASM_POINTER_OFFSET))
        self.town_map_icons.from_block(block=rom,
                                       graphics_offset=graphics_offset,
                                       arrangement_offset=0,
                                       palette_offsets=[palette_offset])

    def write_town_map_icons_to_rom(self, rom):
        log.debug("Writing town map icons")
        graphics_offset, arrangement_offset, palette_offsets = self.town_map_icons.to_block(rom)
        write_asm_pointer(block=rom,
                          offset=TOWN_MAP_ICON_GRAPHICS_ASM_POINTER_OFFSET,
                          pointer=to_snes_address(graphics_offset))
        write_asm_pointer(block=rom,
                          offset=TOWN_MAP_ICON_PALETTE_ASM_POINTER_OFFSET,
                          pointer=to_snes_address(palette_offsets[0]))

    def read_company_logos_from_rom(self, rom):
        log.debug("Reading company logos")
        self.read_logos_from_rom(rom, self.company_logos, COMPANY_LOGO_INFOS)

    def write_company_logos_to_rom(self, rom):
        log.debug("Writing company logos")
        self.write_logos_to_rom(rom, self.company_logos, COMPANY_LOGO_INFOS)

    def read_attract_mode_logos_from_rom(self, rom):
        log.debug("Reading attract mode logos")
        self.read_logos_from_rom(rom, self.attract_mode_logos, ATTRACT_MODE_INFOS)

    def write_attract_mode_logos_to_rom(self, rom):
        log.debug("Writing attract mode logos")
        self.write_logos_to_rom(rom, self.attract_mode_logos, ATTRACT_MODE_INFOS)

    def read_gas_station_from_rom(self, rom):
        log.debug("Reading gas station logo")
        self.read_logos_from_rom(rom, [self.gas_station_logo], [GAS_STATION_INFO])

    def write_gas_station_to_rom(self, rom):
        log.debug("Writing gas station logo")
        self.write_logos_to_rom(rom, [self.gas_station_logo], [GAS_STATION_INFO])

    def read_logos_from_rom(self, rom, logos, infos):
        for info, logo in zip(infos, logos):
            graphics_offset = from_snes_address(read_asm_pointer(rom, info.graphics_asm_pointer_offsets[0]))
            arrangement_offset = from_snes_address(read_asm_pointer(rom, info.arrangement_asm_pointer_offsets[0]))
            palette_offsets = [from_snes_address(read_asm_pointer(rom, x)) for x in info.palette_asm_pointer_offsets]

            logo.from_block(block=rom,
                            graphics_offset=graphics_offset,
                            arrangement_offset=arrangement_offset,
                            palette_offsets=palette_offsets)

    def write_logos_to_rom(self, rom, logos, infos):
        for info, logo in zip(infos, logos):
            graphics_offset, arrangement_offset, palette_offsets = logo.to_block(rom)

            for asm_pointer_offset in info.graphics_asm_pointer_offsets:
                write_asm_pointer(block=rom, offset=asm_pointer_offset, pointer=to_snes_address(graphics_offset))
            for asm_pointer_offset in info.arrangement_asm_pointer_offsets:
                write_asm_pointer(block=rom, offset=asm_pointer_offset, pointer=to_snes_address(arrangement_offset))
            for offset, asm_pointer_offset in zip(palette_offsets, info.palette_asm_pointer_offsets):
                write_asm_pointer(block=rom, offset=asm_pointer_offset, pointer=to_snes_address(offset))

    def read_from_project(self, resource_open):
        self.read_town_maps_from_project(resource_open)
        self.read_town_map_icons_from_project(resource_open)
        self.read_company_logos_from_project(resource_open)
        self.read_attract_mode_logos_from_project(resource_open)
        self.read_gas_station_from_project(resource_open)

    def write_to_project(self, resource_open):
        self.write_town_maps_to_project(resource_open)
        self.write_town_map_icons_to_project(resource_open)
        self.write_company_logos_to_project(resource_open)
        self.write_attract_mode_logos_to_project(resource_open)
        self.write_gas_station_to_project(resource_open)

    def read_town_maps_from_project(self, resource_open):
        for resource_name, town_map in zip(TOWN_MAP_RESOURCE_NAMES, self.town_maps):
            log.info("- Reading {}".format(resource_name))
            with resource_open(resource_name, "png") as image_file:
                image = open_indexed_image(image_file)
                town_map.from_image(image)

    def write_town_maps_to_project(self, resource_open):
        log.debug("Writing town maps")
        for resource_name, town_map in zip(TOWN_MAP_RESOURCE_NAMES, self.town_maps):
            image = town_map.image()
            with resource_open(resource_name, "png") as image_file:
                image.save(image_file, "png")

    def read_town_map_icons_from_project(self, resource_open):
        log.info("- Reading town map icons")
        with resource_open("TownMaps/icons", "png") as image_file:
            image = open_indexed_image(image_file)
            self.town_map_icons.from_image(image=image, arrangement=TOWN_MAP_ICON_PREVIEW_ARRANGEMENT)

    def write_town_map_icons_to_project(self, resource_open):
        log.debug("Writing town map icons")
        image = self.town_map_icons.image(TOWN_MAP_ICON_PREVIEW_ARRANGEMENT)
        with resource_open("TownMaps/icons", "png") as image_file:
            image.save(image_file, "png")

    def read_company_logos_from_project(self, resource_open):
        self.read_logos_from_project(resource_open, self.company_logos, COMPANY_LOGO_INFOS)

    def write_company_logos_to_project(self, resource_open):
        log.debug("Writing company logos")
        self.write_logos_to_project(resource_open, self.company_logos, COMPANY_LOGO_INFOS)

    def read_attract_mode_logos_from_project(self, resource_open):
        self.read_logos_from_project(resource_open, self.attract_mode_logos, ATTRACT_MODE_INFOS)

    def write_attract_mode_logos_to_project(self, resource_open):
        log.debug("Writing attract mode logos")
        self.write_logos_to_project(resource_open, self.attract_mode_logos, ATTRACT_MODE_INFOS)

    def read_logos_from_project(self, resource_open, logos, infos):
        for info, logo in zip(infos, logos):
            log.info("- Reading " + info.name)
            with resource_open(info.name, "png") as image_file:
                image = open_indexed_image(image_file)
                logo.from_image(image)

    def write_logos_to_project(self, resource_open, logos, infos):
        for info, logo in zip(infos, logos):
            image = logo.image()
            with resource_open(info.name, "png") as image_file:
                image.save(image_file, "png")

    def read_gas_station_from_project(self, resource_open):
        log.info("- Reading gas station logo")
        with resource_open(GAS_STATION_INFO.name + "1", "png") as image1_file:
            image1 = open_image(image1_file)
            with resource_open(GAS_STATION_INFO.name + "2", "png") as image2_file:
                image2 = open_image(image2_file)
                with resource_open(GAS_STATION_INFO.name + "3", "png") as image3_file:
                    image3 = open_image(image3_file)
                    self.gas_station_logo.from_images([image1, image2, image3])

    def write_gas_station_to_project(self, resource_open):
        log.debug("Writing gas station logo")
        images = self.gas_station_logo.images()
        with resource_open(GAS_STATION_INFO.name + "1", "png") as image_file:
            images[0].save(image_file, "png")
        with resource_open(GAS_STATION_INFO.name + "2", "png") as image_file:
            images[1].save(image_file, "png")
        with resource_open(GAS_STATION_INFO.name + "3", "png") as image_file:
            images[2].save(image_file, "png")

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version <= 2:
            self.read_town_map_icons_from_rom(rom)
            self.write_town_map_icons_to_project(resource_open_w)

            self.read_attract_mode_logos_from_rom(rom)
            self.write_attract_mode_logos_to_project(resource_open_w)

            self.read_gas_station_from_rom(rom)
            self.write_gas_station_to_project(resource_open_w)

            self.upgrade_project(3, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
