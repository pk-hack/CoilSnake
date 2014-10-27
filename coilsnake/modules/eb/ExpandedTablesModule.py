import logging
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import yml_load
from coilsnake.util.eb.pointer import write_asm_pointer, from_snes_address, to_snes_address


class AsmPointer(object):
    def __init__(self, offset):
        self.offset = offset

    def write(self, rom, address):
        log.info("Writing pointer at " + hex(self.offset))
        write_asm_pointer(rom, self.offset, address)


log = logging.getLogger(__name__)


class ExpandedTablesModule(EbModule):
    NAME = "Expanded Tables"
    TABLE_OFFSETS = {
        0xD58D7A: [  # PSI NAMES
            AsmPointer(0x1c423)
        ]
    }

    def __init__(self):
        super(ExpandedTablesModule, self).__init__()
        self.tables = dict()
        for table_offset in ExpandedTablesModule.TABLE_OFFSETS:
            self.tables[table_offset] = eb_table_from_offset(table_offset)

    def read_from_rom(self, rom):
        for offset, table in self.tables.iteritems():
            table.from_block(rom, from_snes_address(offset))

    def write_to_rom(self, rom):
        for offset, table in self.tables.iteritems():
            new_table_offset = rom.allocate(size=table.size)
            table.to_block(rom, new_table_offset)
            log.info("Writing table @ " + hex(new_table_offset))
            for pointer in self.TABLE_OFFSETS[offset]:
                pointer.write(rom, to_snes_address(new_table_offset))

    def read_from_project(self, resource_open):
        for table in self.tables.itervalues():
            with resource_open(table.name.lower(), "yml") as f:
                yml_rep = yml_load(f)
                num_rows = len(yml_rep)
                table.recreate(num_rows=num_rows)
                table.from_yml_rep(yml_rep)

    def write_to_project(self, resource_open):
        for table in self.tables.itervalues():
            with resource_open(table.name.lower(), "yml") as f:
                table.to_yml_file(f)