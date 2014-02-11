import yaml

from coilsnake.Progress import updateProgress
from coilsnake.modules.GenericModule import GenericModule


class UsedRangeModule(GenericModule):
    NAME = "Used Ranges"

    def upgrade_project(self, oldVersion, newVersion, rom, resourceOpenerR,
                        resourceOpenerW, resourceDeleter):
        global updateProgress
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion == 3:
            tmp = updateProgress
            updateProgress = lambda x: None
            self.read_from_rom(rom)
            self.write_to_project(resourceOpenerW)
            updateProgress = tmp
            self.upgrade_project(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)
        else:
            self.upgrade_project(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)

    def write_to_project(self, resourceOpener):
        with resourceOpener("used_ranges", "yml") as f:
            f.write(
                "# List all ranges which CoilSnake should not touch\n"
                + "# Example:\n"
                + "# - (0x350000, 0x350100)")
        updateProgress(50)

    def read_from_project(self, resourceOpener):
        with resourceOpener("used_ranges", "yml") as f:
            ranges = yaml.load(f, Loader=yaml.CSafeLoader)
            if ranges is None:
                self._ranges = []
            else:
                self._ranges = map(
                    lambda y: tuple(map(lambda z: int(z, 0),
                                        y[1:-1].split(','))),
                    ranges)
        updateProgress(50)

    def read_from_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        self._ranges = {"Ranges": []}
        updateProgress(50)

    def write_to_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        for r in self._ranges:
            rom.mark_allocated(r)
        updateProgress(50)
