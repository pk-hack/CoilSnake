import logging

from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import (convert_values_to_hex_repr,
                                       replace_field_in_yml, yml_dump,
                                       yml_load)
from coilsnake.util.eb.pointer import (AsmPointerReference, XlPointerReference,
                                       from_snes_address, to_snes_address)

log = logging.getLogger(__name__)

# we're going to calculate FREE_RANGES at runtime instead of hardcoding it.
# makes the code easier to maintain.
def build_free_ranges(table_offsets):
    ranges = []
    for offset, patches in table_offsets.items():
        if patches:
            # `offset` is the location of an expandable table.
            # Mark the space it originally took up as a free range
            table = eb_table_from_offset(offset)
            ranges.append((from_snes_address(offset), from_snes_address(offset+table.size-1)))
    return ranges


class MiscTablesModule(EbModule):
    NAME = "Misc Tables"
    # Key: offset
    # Value: a list of PointerReference-like objects to apply patches to expand the table,
    #        or a falsy value. A falsy value will be considered an unexpandable table.
    TABLE_OFFSETS = {
        0xD58D7A: [  # PSI NAMES
            AsmPointerReference(0x1c423)
        ],
        0xCF8985: [  # NPC Configuration Table
            AsmPointerReference(0x023E5), # in func C0222B/ Load NPCs
            XlPointerReference(0x0C32E), # in func C0C30C
            AsmPointerReference(0x131CA), # in func C13187/Talk to
            AsmPointerReference(0x1327F), # in func C1323B/Check NPC
            AsmPointerReference(0x1332F), # in func C1323B/Check NPC
            XlPointerReference(0x1AD77), # in func C1AD42
            AsmPointerReference(0x1B20B), # in func C1AF74/Use overworld item
            AsmPointerReference(0x464C1), # in func C464B5/Create prepared NPC
            AsmPointerReference(0x46831), # in func C4681A
            AsmPointerReference(0x46930), # in func C46914
        ],
        0xC3FD8D: False,  # Attract mode text
        0xD5F645: False,  # Timed Item Delivery
        0xE12F8A: False,  # Photographer
        0xD5EA77: False,  # Condiment Table
        0xD5EBAB: False,  # Scripted Teleport Destination Table
        0xD5F2FB: False,  # Hotspots Table
        0xC3F2B5: False,  # Playable Character Graphics Control Table
        0xD58A50: False,  # PSI Abilities
        0xD57B68: False,  # Battle Actions Table
        0xD5EA5B: False,  # Statistic Growth Variables
        0xD58F49: False,  # Level-up EXP Table
        0xD5F5F5: False,  # Initial Stats Table
        0xD57880: False,  # PSI Teleport Destination Table
        0xD57AAE: False,  # Phone Contacts Table
        0xD576B2: False,  # Store Inventory Table
        0xD5F4BB: False,  # Timed Item Transformations
        0xD5F4CF: False,  # Don't Care
        0xD55000: False,  # Item Data
        0xC23109: False,  # Consolation Item
        0xC3E250: False,  # Windows
    }

    FREE_RANGES = build_free_ranges(TABLE_OFFSETS)

    def __init__(self):
        super(MiscTablesModule, self).__init__()
        self.tables = dict()
        for table_offset in MiscTablesModule.TABLE_OFFSETS:
            self.tables[table_offset] = eb_table_from_offset(table_offset)

    def read_from_rom(self, rom):
        for offset, table in self.tables.items():
            table.from_block(rom, from_snes_address(offset))

    def write_to_rom(self, rom):
        for offset, table in self.tables.items():
            # unexpanded tables should remain in place
            if self.TABLE_OFFSETS[offset]:
                new_table_offset = rom.allocate(size=table.size)
            else:
                new_table_offset = from_snes_address(offset)
            
            table.to_block(rom, new_table_offset)
            log.info("Writing table '{}' @ ".format(table.name) + hex(to_snes_address(new_table_offset)))
            # Write pointers for expansion, only if there is a list of pointers. Otherwise consider it unexpanded
            if self.TABLE_OFFSETS[offset]:
                for pointer in self.TABLE_OFFSETS[offset]:
                    if pointer.validate_structure(rom):
                        pointer.write(rom, to_snes_address(new_table_offset))
                    else:
                        log.warn("Table relocation at %#x failed structure check - skipping...", pointer.offset)

    def read_from_project(self, resource_open):
        for offset, table in self.tables.items():
            with resource_open(table.name.lower(), "yml", True) as f:
                if self.TABLE_OFFSETS[offset]:
                    # expanded table - recreate it with our new number of rows
                    log.debug("Reading {}.yml as an expanded table".format(table.name.lower()))
                    yml_rep = yml_load(f)
                    num_rows = len(yml_rep)
                    table.recreate(num_rows=num_rows)
                    table.from_yml_rep(yml_rep)
                else:
                    # unexpanded table - standard process
                    table.from_yml_file(f)

    def write_to_project(self, resource_open):
        for table in self.tables.values():
            with resource_open(table.name.lower(), "yml", True) as f:
                table.to_yml_file(f)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version == 3:
            replace_field_in_yml(resource_name="item_configuration_table",
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                key="Effect",
                                new_key="Action")
            replace_field_in_yml(resource_name="psi_ability_table",
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                key="Effect",
                                new_key="Action")
            replace_field_in_yml(resource_name="psi_ability_table",
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                key="PSI Name",
                                value_map={0: None,
                                            1: 0,
                                            2: 1,
                                            3: 2,
                                            4: 3,
                                            5: 4,
                                            6: 5,
                                            7: 6,
                                            8: 7,
                                            9: 8,
                                            10: 9,
                                            11: 10,
                                            12: 11,
                                            13: 12,
                                            14: 13,
                                            15: 14,
                                            16: 15,
                                            17: 16})

            resource_delete("cmd_window_text")
            resource_delete("psi_anim_palettes")
            resource_delete("sound_stone_palette")

            self.upgrade_project(old_version=old_version + 1,
                                new_version=new_version,
                                rom=rom,
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                resource_delete=resource_delete)
        elif old_version == 2:
            replace_field_in_yml(resource_name="timed_delivery_table",
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                key="Suitable Area Text Pointer",
                                new_key="Delivery Success Text Pointer")
            replace_field_in_yml(resource_name="timed_delivery_table",
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                key="Unsuitable Area Text Pointer",
                                new_key="Delivery Failure Text Pointer")

            with resource_open_r("timed_delivery_table", "yml", True) as f:
                out = yml_load(f)
                yml_str_rep = yml_dump(out, default_flow_style=False)

            yml_str_rep = convert_values_to_hex_repr(yml_str_rep, "Event Flag")

            with resource_open_w("timed_delivery_table", "yml", True) as f:
                f.write(yml_str_rep)

            self.upgrade_project(old_version=old_version + 1,
                                new_version=new_version,
                                rom=rom,
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                resource_delete=resource_delete)
        elif old_version == 1:
            replace_field_in_yml(resource_name="psi_ability_table",
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                key="Target",
                                new_key="Usability Outside of Battle",
                                value_map={"Nobody": "Other",
                                            "Enemies": "Unusable",
                                            "Allies": "Usable"})
            replace_field_in_yml(resource_name="battle_action_table",
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                key="Direction",
                                value_map={"Party": "Enemy",
                                            "Enemy": "Party"})

            self.upgrade_project(old_version=old_version + 1,
                                new_version=new_version,
                                rom=rom,
                                resource_open_r=resource_open_r,
                                resource_open_w=resource_open_w,
                                resource_delete=resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
