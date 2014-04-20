from coilsnake.modules.common.GenericModule import GenericModule


class LunarIpsCompatibilityModule(GenericModule):
    NAME = "Lunar IPS Compatibility"

    def write_to_rom(self, rom):
        last_offset = rom.size - 1
        if rom.is_unallocated((last_offset, last_offset)):
            rom.mark_allocated((last_offset, last_offset))
            rom[last_offset] = 0xC5