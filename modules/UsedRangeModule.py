from GenericModule import GenericModule
from modules.Progress import updateProgress

import yaml


class UsedRangeModule(GenericModule):
    _name = "Used Ranges"

    def upgradeProject(self, oldVersion, newVersion, rom, resourceOpenerR,
                       resourceOpenerW, resourceDeleter):
        global updateProgress
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion == 3:
            tmp = updateProgress
            updateProgress = lambda x: None
            self.readFromRom(rom)
            self.writeToProject(resourceOpenerW)
            updateProgress = tmp
            self.upgradeProject(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)
        else:
            self.upgradeProject(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)

    def writeToProject(self, resourceOpener):
        with resourceOpener("used_ranges", "yml") as f:
            f.write(
                "# List all ranges which CoilSnake should not touch\n"
                + "# Example:\n"
                + "# - (0x350000, 0x350100)")
        updateProgress(50)

    def readFromProject(self, resourceOpener):
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

    def readFromRom(self, rom):
        self._ranges = {"Ranges": []}
        updateProgress(50)

    def writeToRom(self, rom):
        for r in self._ranges:
            rom.markRangeAsNotFree(r)
        updateProgress(50)
