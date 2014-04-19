import yaml

from coilsnake.Progress import updateProgress
from coilsnake.modules.common.GenericModule import GenericModule

MODULE_COMMENT = """# List all ranges which CoilSnake should not touch
# Example:
# - (0x350000, 0x350100)"""


class UsedRangeModule(GenericModule):
    NAME = 'Used Ranges'
    FILE = 'used_ranges'

    def __init__(self):
        """
            Sets the module to its default state (no used ranges).
        """
        GenericModule.__init__(self)
        self.ranges = []

    def upgrade_project(self, old_version, new_version, rom,
            resource_opener_r, resource_opener_w, resource_deleter):
        """
            Upgrades a project's used ranges module to the latest version.
        """
        if old_version == new_version:
            updateProgress(100)
            return
        if oldVersion == 3:
            self.read_from_rom(rom, False)
            self.write_to_project(resource_opener_w, False)
        self.upgrade_project(
            old_version + 1,
            new_version,
            rom,
            resource_opener_r,
            resource_opener_w,
            resource_deleter)

    def write_to_project(self, resource_opener):
        """
            Writes an empty module file, ready to be filled by the user.
        """
        with resource_opener(self.FILE, 'yml') as f:
            f.write(MODULE_COMMENT)
        updateProgress(50)

    def read_from_project(self, resourceOpener):
        """
            Reads a user-written list of ranges that shouldn't be touched.
        """
        with resourceOpener(self.FILE, 'yml') as f:
            ranges = yaml.load(f, Loader=yaml.CSafeLoader)
            if not ranges:
                self.ranges = []
            else:
                self.ranges = map(
                    lambda y: tuple(map(lambda z: int(z, 0),
                                        y[1:-1].split(','))),
                    ranges)
        updateProgress(50)

    def read_from_rom(self, rom, u=True):
        """
            Clears the used ranges list, since used ranges should be
            user-specified.
        """
        self.ranges = []
        if u:
            updateProgress(50)

    def write_to_rom(self, rom, u=True):
        """
            Makes a note of all the ranges which shouldn't be modified when
            writing.
        """
        for r in self.ranges:
            rom.mark_allocated(r)
        if u:
            updateProgress(50)
