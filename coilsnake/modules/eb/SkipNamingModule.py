import logging
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import yml_load, yml_dump
from coilsnake.util.eb.pointer import to_snes_address
from coilsnake.util.eb.text import standard_text_to_byte_list
from coilsnake.exceptions.common.exceptions import CoilSnakeUserError

log = logging.getLogger(__name__)

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
        with resource_open("naming_skip", "yml", True) as f:
            yml_dump(out, f, default_flow_style=False)

    def read_from_project(self, resource_open):
        with resource_open("naming_skip", "yml", True) as f:
            self.data = yml_load(f)

    def write_loader_asm(self, rom, offset, s, strlen, mem_offset, byte2):
        i = 0
        byte_list = standard_text_to_byte_list(s, strlen, False)
        for byte in byte_list:
            rom[offset:offset+5] = [0xa9, byte, 0x8d, mem_offset + i, byte2]
            i += 1
            offset += 5
        return offset

    def write_to_rom(self, rom):
        if self.data["Enable Skip"]:
            # this fixes the naming screen music playing briefly when skip naming is on
            # it works by changing the jump from @CHANGE_TO_NAMING_SCREEN_MUSIC to @UNKNOWN18 (which normally runs directly after the music change)
            # https://github.com/Herringway/ebsrc/blob/87f514cb4b77fa3193bcb122ea51f5de5cfdd9cf/src/intro/file_select_menu_loop.asm#L101
            # Verify the code structure first:
            if rom[0x1f8f0] == 0xD0 and rom[0x1f8f1] == 0x09:
                rom[0x1f8f1] = 0x10
            else:
                log.warn("Unable to apply naming screen music bypass due to existing ASM changes")

            offset = rom.allocate(size=(10 + 4 * 5 * 5 + 3 * 6 * 5))
            # Patch ASM to "JML newCode"
            if bytes(rom.to_array()[0x1faae:0x1fab2]) != b'\xa9\x07\x00\x18':
                raise CoilSnakeUserError("Naming ASM has already been patched - unable to apply naming skip")
            rom[0x1faae] = 0x5c
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
