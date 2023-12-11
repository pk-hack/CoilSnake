import logging

from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import convert_values_to_hex_repr, replace_field_in_yml, yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address

log = logging.getLogger(__name__)


class MiscTablesModule(EbModule):
    NAME = "Miscellaneous Tables"
    TABLE_OFFSETS = [
        0xC3FD8D,  # Attract mode text
        0xD5F645,  # Timed Item Delivery
        0xE12F8A,  # Photographer
        0xD5EA77,  # Condiment Table
        0xD5EBAB,  # Scripted Teleport Destination Table
        0xD5F2FB,  # Hotspots Table
        0xC3F2B5,  # Playable Character Graphics Control Table
        0xD58A50,  # PSI Abilities
        0xD57B68,  # Battle Actions Table
        0xD5EA5B,  # Statistic Growth Variables
        0xD58F49,  # Level-up EXP Table
        0xD5F5F5,  # Initial Stats Table
        0xD57880,  # PSI Teleport Destination Table
        0xD57AAE,  # Phone Contacts Table
        0xD576B2,  # Store Inventory Table
        0xD5F4BB,  # Timed Item Transformations
        0xD5F4CF,  # Don't Care
        0xD55000,  # Item Data
        0xC23109,  # Consolation Item
        0xC3E250,  # Windows
    ]

    def __init__(self):
        super(MiscTablesModule, self).__init__()
        self.tables = [(from_snes_address(x), eb_table_from_offset(x)) for x in self.TABLE_OFFSETS]

    def read_from_rom(self, rom):
        for offset, table in self.tables:
            table.from_block(rom, offset)

    def write_to_rom(self, rom):
        for offset, table in self.tables:
            table.to_block(rom, offset)

    def read_from_project(self, resource_open):
        for _, table in self.tables:
            with resource_open(table.name.lower(), "yml", True) as f:
                log.debug("Reading {}.yml".format(table.name.lower()))
                table.from_yml_file(f)

    def write_to_project(self, resource_open):
        for _, table in self.tables:
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
