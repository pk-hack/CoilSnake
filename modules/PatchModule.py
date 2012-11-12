from GenericModule import GenericModule
from modules.Progress import updateProgress
from modules.Ips import Ips

import os
import yaml

class PatchModule(GenericModule):
    _name = "Patches"
    def upgradeProject(self, oldVersion, newVersion, rom, resourceOpenerR,
            resourceOpenerW):
        global updateProgress
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion == 2:
            self.upgradeProject(oldVersion+1, newVersion, rom, resourceOpenerR,
                                        resourceOpenerW)
        elif oldVersion == 1:
            tmp = updateProgress
            updateProgress = lambda x: None
            self.readFromRom(rom)
            self.writeToProject(resourceOpenerW)
            updateProgress = tmp
            self.upgradeProject(oldVersion+1, newVersion, rom, resourceOpenerR,
                    resourceOpenerW)
        else:
            raise RuntimeException("Don't know how to upgrade from version",
                    oldVersion, "to", newVersion)
    def readFromRom(self, rom):
        self._patches = dict()
        # Loop through all the patches for this romtyp
        for ipsDescFname in [s for s in os.listdir(
            'ips/' + rom.type()) if s.lower().endswith(".yml")]:
            patchName = ipsDescFname[:-4]
            ips = Ips()
            ips.load('ips/' + rom.type() + '/' + patchName + '.ips')
            with open('ips/' + rom.type() + '/' + ipsDescFname) as ipsDescFile:
                ipsDesc = yaml.load(ipsDescFile, Loader=yaml.CSafeLoader)
                if ipsDesc["Auto-Apply"]:
                    self._patches[ipsDesc["Title"]] = "enabled"
                else:
                    self._patches[ipsDesc["Title"]] = "disabled"
        updateProgress(50)
    def writeToRom(self, rom):
        for ipsDescFname in [s for s in os.listdir(
            'ips/' + rom.type()) if s.lower().endswith(".yml")]:
            patchName = ipsDescFname[:-4]
            with open('ips/' + rom.type() + '/' + ipsDescFname) as ipsDescFile:
                ipsDesc = yaml.load(ipsDescFile, Loader=yaml.CSafeLoader)
                if ((ipsDesc["Title"] in self._patches) and
                        (self._patches[ipsDesc["Title"]].lower() == "enabled")):
                    ranges = map(lambda y: tuple(map(lambda z: int(z, 0),
                        y[1:-1].split(','))), ipsDesc["Ranges"])

                    # First, check that we can apply this
                    for range in ranges:
                        if not rom.isRangeFree(range):
                            # Range is not free, can't apply
                            raise RuntimeError("Can't apply patch \"" +
                                ipsDesc["Title"] + "\", range (" +
                                hex(range[0]) + "," +  hex(range[1]) +
                                ") is not free")
                    # Now apply the patch
                    patchName = ipsDescFname[:-4]
                    ips = Ips()
                    offset = 0
                    if "Header" in ipsDesc:
                        offset = ipsDesc["Header"]
                    ips.load('ips/' + rom.type() + '/' + patchName + '.ips',
                            offset)
                    ips.apply(rom)
                    # Mark the used ranges as used
                    for range in ranges:
                        rom.markRangeAsNotFree(range)
        updateProgress(50)
    def writeToProject(self, resourceOpener):
        with resourceOpener("patches", "yml") as f:
            yaml.dump(self._patches, f, default_flow_style=False,
                    Dumper=yaml.CSafeDumper)
        updateProgress(50)
    def readFromProject(self, resourceOpener):
        with resourceOpener("patches", "yml") as f:
            self._patches = yaml.load(f, Loader=yaml.CSafeLoader)
        updateProgress(50)
