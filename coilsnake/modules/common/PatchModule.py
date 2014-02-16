import os
import yaml

from coilsnake.Progress import updateProgress
from coilsnake.Ips import Ips
from coilsnake.modules.common.GenericModule import GenericModule


IPS_DIRECTORY = os.path.join(os.path.dirname(__file__), "resources", "ips")


def get_ips_directory(romtype):
    return os.path.join(IPS_DIRECTORY, romtype)


class PatchModule(GenericModule):
    NAME = "Patches"

    def upgrade_project(self, oldVersion, newVersion, rom, resourceOpenerR,
                        resourceOpenerW, resourceDeleter):
        global updateProgress
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion == 1:
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

    def read_from_rom(self, rom):

        self._patches = dict()
        # Loop through all the patches for this romtype
        for ipsDescFname in [s for s in os.listdir(get_ips_directory(rom.type)) if s.lower().endswith(".yml")]:
            patchName = ipsDescFname[:-4]
            ips = Ips()
            ips.load(os.path.join(get_ips_directory(rom.type), patchName + '.ips'))
            with open(os.path.join(get_ips_directory(rom.type), ipsDescFname)) as ipsDescFile:
                ipsDesc = yaml.load(ipsDescFile, Loader=yaml.CSafeLoader)
                if ipsDesc["Auto-Apply"]:
                    self._patches[ipsDesc["Title"]] = "enabled"
                else:
                    self._patches[ipsDesc["Title"]] = "disabled"
        updateProgress(50)

    def write_to_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        for ipsDescFname in [s for s in os.listdir(get_ips_directory(rom.type)) if s.lower().endswith(".yml")]:
            patchName = ipsDescFname[:-4]
            with open(os.path.join(get_ips_directory(rom.type), ipsDescFname)) as ipsDescFile:
                ipsDesc = yaml.load(ipsDescFile, Loader=yaml.CSafeLoader)
                if ((ipsDesc["Title"] in self._patches) and
                        (self._patches[ipsDesc["Title"]].lower() == "enabled")):
                    ranges = map(lambda y: tuple(map(lambda z: int(z, 0),
                                                     y[1:-1].split(','))), ipsDesc["Ranges"])

                    # First, check that we can apply this
                    for range in ranges:
                        if not rom.is_unallocated(range):
                            # Range is not free, can't apply
                            raise RuntimeError("Can't apply patch \"" +
                                               ipsDesc["Title"] + "\", range (" +
                                               hex(range[0]) + "," + hex(range[1]) +
                                               ") is not free")
                    # Now apply the patch
                    patchName = ipsDescFname[:-4]
                    ips = Ips()
                    offset = 0
                    if "Header" in ipsDesc:
                        offset = ipsDesc["Header"]
                    ips.load(
                        'resources/ips/' +
                        rom.type + '/' + patchName + '.ips',
                        offset)
                    ips.apply(rom)
                    # Mark the used ranges as used
                    for range in ranges:
                        rom.mark_allocated(range)
        updateProgress(50)

    def write_to_project(self, resourceOpener):
        with resourceOpener("patches", "yml") as f:
            yaml.dump(self._patches, f, default_flow_style=False,
                      Dumper=yaml.CSafeDumper)
        updateProgress(50)

    def read_from_project(self, resourceOpener):
        with resourceOpener("patches", "yml") as f:
            self._patches = yaml.load(f, Loader=yaml.CSafeLoader)
        updateProgress(50)
