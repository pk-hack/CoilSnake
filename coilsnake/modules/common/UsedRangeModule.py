from coilsnake.modules.common.GenericModule import GenericModule
from coilsnake.util.common.yml import yml_load

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
        super(UsedRangeModule, self).__init__()
        self.ranges = []

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        """
            Upgrades a project's used ranges module to the latest version.
        """
        if old_version == new_version:
            return
        if old_version == 3:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
        self.upgrade_project(
            old_version + 1,
            new_version,
            rom,
            resource_open_r,
            resource_open_w,
            resource_delete)

    def write_to_project(self, resource_opener):
        """
            Writes an empty module file, ready to be filled by the user.
        """
        with resource_opener(self.FILE, 'yml') as f:
            f.write(MODULE_COMMENT)

    def read_from_project(self, resourceOpener):
        """
            Reads a user-written list of ranges that shouldn't be touched.
        """
        with resourceOpener(self.FILE, 'yml') as f:
            ranges = yml_load(f)
            if not ranges:
                self.ranges = []
            else:
                self.ranges = [tuple([int(z, 0) for z in y[1:-1].split(',')]) for y in ranges]

    def read_from_rom(self, rom, u=True):
        """
            Clears the used ranges list, since used ranges should be
            user-specified.
        """
        self.ranges = []

    def write_to_rom(self, rom, u=True):
        """
            Makes a note of all the ranges which shouldn't be modified when
            writing.
        """
        for r in self.ranges:
            rom.mark_allocated(r)
