from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import yml_load, yml_dump
from coilsnake.util.eb.pointer import to_snes_address


class SkipNamingModule(EbModule):
    NAME = "Skip Names"

    def write_to_project(self, resource_open):
        out = {"Enable Skip": False,
               "Enable Summary": False,
               "Name1": "Ness",
               "Name2": "Paula",
               "Name3": "Jeff",
               "Name4": "Poo",
               "Pet": "King",
               "Food": "Steak",
               "Thing": "Rockin"}
        with resource_open("naming_skip", "yml") as f:
            yml_dump(out, f, default_flow_style=False)

    def read_from_project(self, resource_open):
        with resource_open("naming_skip", "yml") as f:
            self.data = yml_load(f)

    def write_loader_asm(self, rom, offset, s, strlen, mem_offset, byte2):
        i = 0
        for ch in s[0:strlen]:
            rom[offset:offset+5] = [0xa9, ord(ch) + 0x30, 0x8d, mem_offset + i, byte2]
            i += 1
            offset += 5
        for j in range(i, strlen):
            rom[offset:offset+5] = [0xa9, 0, 0x8d, mem_offset + i, byte2]
            i += 1
            offset += 5
        return offset

    def write_to_rom(self, rom):
        if self.data["Enable Skip"]:
            rom[0x1faae] = 0x5c
            offset = rom.allocate(size=(10 + 4 * 5 * 5 + 3 * 6 * 5))
            rom.write_multi(0x1faaf, to_snes_address(offset), 3)
            rom[offset:offset+4] = [0x48, 0x08, 0xe2, 0x20]
            offset += 4

            offset = self.write_loader_asm(rom, offset, self.data["Name1"], 5, 0xce, 0x99)
            offset = self.write_loader_asm(rom, offset, self.data["Name2"], 5, 0x2d, 0x9a)
            offset = self.write_loader_asm(rom, offset, self.data["Name3"], 5, 0x8c, 0x9a)
            offset = self.write_loader_asm(rom, offset, self.data["Name4"], 5, 0xeb, 0x9a)
            offset = self.write_loader_asm(rom, offset, self.data["Pet"],   6, 0x19, 0x98)
            offset = self.write_loader_asm(rom, offset, self.data["Food"],  6, 0x1f, 0x98)
            offset = self.write_loader_asm(rom, offset, self.data["Thing"], 6, 0x29, 0x98)

            if self.data["Enable Summary"]:
                rom[offset:offset+6] = [0x28, 0x68, 0x5c, 0xc0, 0xfa, 0xc1]
            else:
                rom[offset:offset+6] = [0x28, 0x68, 0x5c, 0x05, 0xfd, 0xc1]