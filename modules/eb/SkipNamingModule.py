import EbModule
from modules.Progress import updateProgress

import yaml


class SkipNamingModule(EbModule.EbModule):
    NAME = "Skip Names"

    def write_to_project(self, resourceOpener):
        out = {"Enable Skip": False,
               "Enable Summary": False,
               "Name1": "Ness",
               "Name2": "Paula",
               "Name3": "Jeff",
               "Name4": "Poo",
               "Pet": "King",
               "Food": "Steak",
               "Thing": "Rockin"}
        with resourceOpener("naming_skip", "yml") as f:
            yaml.dump(out, f, default_flow_style=False,
                      Dumper=yaml.CSafeDumper)
        updateProgress(50)

    def read_from_project(self, resourceOpener):
        with resourceOpener("naming_skip", "yml") as f:
            self._data = yaml.load(f, Loader=yaml.CSafeLoader)
        updateProgress(50)

    def writeLoaderAsm(self, rom, loc, s, strlen, memLoc, byte2):
        i = 0
        for ch in s[0:strlen]:
            rom.write(loc, [0xa9, ord(ch) + 0x30, 0x8d, memLoc + i, byte2])
            i += 1
            loc += 5
        for j in range(i, strlen):
            rom.write(loc, [0xa9, 0, 0x8d, memLoc + i, byte2])
            i += 1
            loc += 5
        return loc

    def write_to_rom(self, rom):
        if self._data["Enable Skip"]:
            rom[0x1faae] = 0x5c
            loc = rom.getFreeLoc(10 + 4 * 5 * 5 + 3 * 6 * 5)
            rom.writeMulti(0x1faaf, EbModule.toSnesAddr(loc), 3)
            rom.write(loc, [0x48, 0x08, 0xe2, 0x20])
            loc += 4

            loc = self.writeLoaderAsm(rom, loc, self._data["Name1"], 5, 0xce,
                                      0x99)
            loc = self.writeLoaderAsm(rom, loc, self._data["Name2"], 5, 0x2d,
                                      0x9a)
            loc = self.writeLoaderAsm(rom, loc, self._data["Name3"], 5, 0x8c,
                                      0x9a)
            loc = self.writeLoaderAsm(rom, loc, self._data["Name4"], 5, 0xeb,
                                      0x9a)
            loc = self.writeLoaderAsm(
                rom,
                loc,
                self._data["Pet"],
                6,
                0x19,
                0x98)
            loc = self.writeLoaderAsm(rom, loc, self._data["Food"], 6, 0x1f,
                                      0x98)
            loc = self.writeLoaderAsm(rom, loc, self._data["Thing"], 6, 0x29,
                                      0x98)

            if self._data["Enable Summary"]:
                rom.write(loc, [0x28, 0x68, 0x5c, 0xc0, 0xfa, 0xc1])
            else:
                rom.write(loc, [0x28, 0x68, 0x5c, 0x05, 0xfd, 0xc1])
        updateProgress(50)
