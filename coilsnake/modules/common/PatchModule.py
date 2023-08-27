import os

from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.model.common.ips import IpsPatch
from coilsnake.model.common.blocks import ROM_TYPE_NAME_EARTHBOUND
from coilsnake.modules.common.GenericModule import GenericModule
from coilsnake.util.common.assets import ASSET_PATH
from coilsnake.util.common.yml import yml_load, yml_dump


IPS_DIRECTORY = os.path.join(ASSET_PATH, "ips")
REMOVED_PATCHES = {
    ROM_TYPE_NAME_EARTHBOUND: ["Battle Font Width Hack"]
}


def get_ips_directory(romtype):
    return os.path.join(IPS_DIRECTORY, romtype)


def get_ips_filename(romtype, patch_name):
    return os.path.join(IPS_DIRECTORY, romtype, patch_name + ".ips")


class PatchModule(GenericModule):
    NAME = "Patches"

    @staticmethod
    def is_compatible_with_romtype(romtype):
        return romtype != "Unknown"

    def __init__(self):
        super(PatchModule, self).__init__()
        self.patches = None

    def read_from_rom(self, rom):
        self.patches = dict()
        # Loop through all the patches for this romtype
        for ip_desc_filename in [s for s in os.listdir(get_ips_directory(rom.type)) if s.lower().endswith(".yml")]:
            with open(os.path.join(get_ips_directory(rom.type), ip_desc_filename)) as ips_desc_file:
                ips_desc = yml_load(ips_desc_file)
                ips_desc_title = ips_desc["Title"]

                if "Hidden" in ips_desc and ips_desc["Hidden"]:
                    continue
                elif ips_desc["Auto-Apply"]:
                    self.patches[ips_desc_title] = "enabled"
                else:
                    self.patches[ips_desc_title] = "disabled"

    def write_to_rom(self, rom):
        for ips_desc_filename in [s for s in os.listdir(get_ips_directory(rom.type)) if s.lower().endswith(".yml")]:
            patch_name = ips_desc_filename[:-4]
            with open(os.path.join(get_ips_directory(rom.type), ips_desc_filename)) as ips_desc_file:
                ips_desc = yml_load(ips_desc_file)
                if "Hidden" in ips_desc and ips_desc["Hidden"]:
                    continue
                elif (ips_desc["Title"] in self.patches) and (self.patches[ips_desc["Title"]].lower() == "enabled"):
                    # First, check that we can apply this
                    ranges = [tuple([int(z, 0) for z in y[1:-1].split(',')]) for y in ips_desc["Ranges"]]
                    for range in ranges:
                        if not rom.is_unallocated(range):
                            raise CoilSnakeError(
                                "Can't apply patch \"{}\" because range ({:#x},{:#x}) is not unallocated".format(
                                    ips_desc["Title"], range[0], range[1]))

                    # Now apply the patch
                    ips = IpsPatch()
                    offset = 0
                    if "Header" in ips_desc:
                        offset = ips_desc["Header"]
                    ips.load(get_ips_filename(rom.type, patch_name), offset)
                    ips.apply(rom)

                    # Mark the used ranges as used
                    for range in ranges:
                        rom.mark_allocated(range)

    def write_to_project(self, resource_open):
        with resource_open("patches", "yml", True) as f:
            yml_dump(self.patches, f, default_flow_style=False)

    def read_from_project(self, resource_open):
        with resource_open("patches", "yml", True) as f:
            self.patches = yml_load(f)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == 1:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
        elif old_version < new_version:
            self.read_from_project(resource_open_r)

            # Remove all patches that should not exist
            if rom.type in REMOVED_PATCHES:
                for patch_name in REMOVED_PATCHES[rom.type]:
                    if patch_name in self.patches:
                        del self.patches[patch_name]

            # Add in all the new patches
            for ip_desc_filename in [s for s in os.listdir(get_ips_directory(rom.type)) if s.lower().endswith(".yml")]:
                with open(os.path.join(get_ips_directory(rom.type), ip_desc_filename)) as ips_desc_file:
                    ips_desc = yml_load(ips_desc_file)
                    ips_desc_title = ips_desc["Title"]
                    ips_is_hidden = ("Hidden" in ips_desc) and ips_desc["Hidden"]

                    if (not ips_is_hidden) and (ips_desc_title not in self.patches):
                        self.patches[ips_desc_title] = "disabled"

            self.write_to_project(resource_open_w)