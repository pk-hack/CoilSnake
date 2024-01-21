import logging
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import yml_load
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address, AsmPointerReference, XlPointerReference

log = logging.getLogger(__name__)


class ExpandedTablesModule(EbModule):
    NAME = "Expanded Tables"
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
    }

    FREE_RANGES = [
        # psi names
        (from_snes_address(0xD58D7A), from_snes_address(0xD58F23 - 1)),
        # npc config table
        (from_snes_address(0xCF8985), from_snes_address(0xCFF2B5 - 1))
    ]


    def __init__(self):
        super(ExpandedTablesModule, self).__init__()
        self.tables = dict()
        for table_offset in ExpandedTablesModule.TABLE_OFFSETS:
            self.tables[table_offset] = eb_table_from_offset(table_offset)

    def read_from_rom(self, rom):
        for offset, table in self.tables.items():
            table.from_block(rom, from_snes_address(offset))

    def write_to_rom(self, rom):
        for offset, table in self.tables.items():
            new_table_offset = rom.allocate(size=table.size)
            table.to_block(rom, new_table_offset)
            log.info("Writing table @ " + hex(to_snes_address(new_table_offset)))
            for pointer in self.TABLE_OFFSETS[offset]:
                if pointer.validate_structure(rom):
                    pointer.write(rom, to_snes_address(new_table_offset))
                else:
                    log.warn("Table relocation at %#x failed structure check - skipping...", pointer.offset)

    def read_from_project(self, resource_open):
        for table in self.tables.values():
            with resource_open(table.name.lower(), "yml", True) as f:
                yml_rep = yml_load(f)
                num_rows = len(yml_rep)
                table.recreate(num_rows=num_rows)
                table.from_yml_rep(yml_rep)

    def write_to_project(self, resource_open):
        for table in self.tables.values():
            with resource_open(table.name.lower(), "yml", True) as f:
                table.to_yml_file(f)
