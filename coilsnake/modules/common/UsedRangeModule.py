import logging

from coilsnake.exceptions.common.exceptions import InvalidYmlRepresentationError
from coilsnake.modules.common.GenericModule import GenericModule
from coilsnake.util.common.yml import yml_load


log = logging.getLogger(__name__)

MODULE_COMMENT = """# List all ranges which CoilSnake should not touch
# Example:
# - (0x350000, 0x350100)"""


def range_from_string(s):
    try:
        start, end = s[1:-1].split(',')
    except Exception as e:
        raise InvalidYmlRepresentationError(
            "Range \"{}\" is invalid. Must be in the format of \"(start,end)\".".format(s))

    if not start or not end:
        raise InvalidYmlRepresentationError(
            "Range \"{}\" is invalid. Must be in the format of \"(start,end)\".".format(s))

    start = start.strip()
    try:
        start = int(start, 0)
    except ValueError:
        raise InvalidYmlRepresentationError(
            ("Value \"{}\" in range \"{}\" is invalid. It must be either a hexidecimal "
             "or decimal number.").format(start, s))

    end = end.strip()
    try:
        end = int(end, 0)
    except ValueError:
        raise InvalidYmlRepresentationError(
            ("Value \"{}\" in used range \"{}\" is invalid. It must be either a hexidecimal "
             "or decimal number.").format(end, s))

    return start, end


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
            Writes an empty file, ready to be filled by the user.
        """
        with resource_opener(self.FILE, 'yml', True) as f:
            f.write(MODULE_COMMENT)

    def read_from_project(self, resource_open):
        """
            Reads a user-written list of ranges that shouldn't be touched.
        """
        with resource_open(self.FILE, 'yml', True) as f:
            ranges = yml_load(f)
            if not ranges:
                self.ranges = []
            elif type(ranges) != list:
                raise InvalidYmlRepresentationError("used_range files is invalid. Must be a list of ranges.")
            else:
                self.ranges = []
                for entry in ranges:
                    self.ranges.append(range_from_string(entry))

    def read_from_rom(self, rom):
        """
            Clears the used ranges list, since used ranges should be
            user-specified.
        """
        self.ranges = []

    def write_to_rom(self, rom):
        """
            Makes a note of all the ranges which shouldn't be modified when
            writing.
        """
        for used_range in self.ranges:
            for unallocated_range in rom.get_unallocated_portions_of_range(used_range):
                log.debug("Marking range [{:#x},{:#x}] as allocated".format(
                    unallocated_range[0], unallocated_range[1]))
                rom.mark_allocated(unallocated_range)
        return