import yaml

from coilsnake.Progress import updateProgress
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.project import replace_field_in_yml
from coilsnake.util.common.yml import convert_values_to_hex_repr
from coilsnake.util.eb.pointer import from_snes_address


class MiscTablesModule(EbModule):
    NAME = "Misc Tables"
    TABLE_OFFSETS = [
        0xC3FD8D,  # Attract mode text
        0xD5F645,  # Timed Item Delivery
        0xE12F8A,  # Photographer
        0xCF8985,  # NPC Configuration Table
        0xD5EA77,  # Condiment Table
        0xD5EBAB,  # Scripted Teleport Destination Table
        0xD5F2FB,  # Hotspots Table
        0xC3F2B5,  # Playable Character Graphics Control Table
        0xD58D7A,  # PSI Names
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
        self.tables = map(lambda x: (from_snes_address(x), eb_table_from_offset(x)), self.TABLE_OFFSETS)
        self._pct = 50.0 / len(self.tables)

    def read_from_rom(self, rom):
        for offset, table in self.tables:
            table.from_block(rom, offset)
            updateProgress(self._pct)

    def write_to_rom(self, rom):
        for offset, table in self.tables:
            table.to_block(rom, offset)
            updateProgress(self._pct)

    def read_from_project(self, resource_open):
        for _, table in self.tables:
            with resource_open(table.name.lower(), "yml") as f:
                table.from_yml_file(f)
                updateProgress(self._pct)

    def write_to_project(self, resource_open):
        for _, table in self.tables:
            with resource_open(table.name.lower(), "yml") as f:
                table.to_yml_file(f)
                updateProgress(self._pct)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            updateProgress(100)
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

            with resource_open_r("timed_delivery_table", "yml") as f:
                out = yaml.load(f, Loader=yaml.CSafeLoader)
                yml_str_rep = yaml.dump(out, default_flow_style=False, Dumper=yaml.CSafeDumper)

            yml_str_rep = convert_values_to_hex_repr(yml_str_rep, "Event Flag")

            with resource_open_w("timed_delivery_table", "yml") as f:
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
            raise RuntimeError("Don't know how to upgrade from version",
                               old_version, "to", new_version)
