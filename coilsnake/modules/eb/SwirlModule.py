import logging

from coilsnake.exceptions.common.exceptions import CoilSnakeTraceableError
from coilsnake.model.common.ips import IpsPatch
from coilsnake.model.eb.swirls import Swirl, write_swirl_frames
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.common.PatchModule import get_ips_filename
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.common.yml import yml_dump, yml_load
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


SWIRL_TABLE_DEFAULT_OFFSET = 0xCEDD41
SWIRL_ANIMATION_POINTER_TABLE_DEFAULT_OFFSET = 0xCEDC45
SWIRL_ANIMATION_POINTER_TABLE_BASE = 0xCE0000

RELOCATED_SWIRL_ANIMATION_POINTER_TABLE_POINTERS = ((0x4aa8f, 0), (0x4aa95, 2), (0x4aadc, 0), (0x4aae4, 2))

log = logging.getLogger(__name__)


# Relocates the animation pointer table and makes it into a 4-byte pointer table instead of a 2-byte one
def apply_relocation_patch(rom):
    ips = IpsPatch()
    ips.load(get_ips_filename(rom.type, "swirl_relocate"), 0x200)
    ips.apply(rom)

def test_swirl_relocated(rom):
    ips = IpsPatch()
    ips.load(get_ips_filename(rom.type, "swirl_relocate"), 0x200)
    return ips.is_applied(rom)

class SwirlModule(EbModule):
    NAME = "Swirls"
    FREE_RANGES = [(0xE6914, 0xEDD40)]  # Swirl frame data and animation pointer table

    def __init__(self):
        super(SwirlModule, self).__init__()
        self.swirl_table = eb_table_from_offset(
            offset=SWIRL_TABLE_DEFAULT_OFFSET
        )
        self.pointer_table = eb_table_from_offset(
            offset=SWIRL_ANIMATION_POINTER_TABLE_DEFAULT_OFFSET
        )
        self.swirls = []

    def read_from_rom(self, rom):
        self.swirl_table.from_block(
            rom, offset=from_snes_address(SWIRL_TABLE_DEFAULT_OFFSET))

        if test_swirl_relocated(rom):
            # Calculate total number of animations from the swirl table
            total_animations = 0        
            for i in range(self.swirl_table.num_rows):
                total_animations += self.swirl_table[i][2]

            # Read in the offset of the relocated animation table
            offset = rom.read_multi(RELOCATED_SWIRL_ANIMATION_POINTER_TABLE_POINTERS[0][0], 3)

            # Pointer size is now 4, so read in 4 bytes at a time
            all_animation_pointers = [
                from_snes_address(rom.read_multi(from_snes_address(offset + (i * 4)), 4))
                for i in range(total_animations)
            ]
        else:
            self.pointer_table.from_block(
                rom, offset=from_snes_address(SWIRL_ANIMATION_POINTER_TABLE_DEFAULT_OFFSET))

            all_animation_pointers = [
                from_snes_address(self.pointer_table[i][0] | SWIRL_ANIMATION_POINTER_TABLE_BASE)
                for i in range(self.pointer_table.num_rows)
            ]

        self.swirls = [None] * self.swirl_table.num_rows
        for i in range(self.swirl_table.num_rows):
            speed = self.swirl_table[i][0]
            first_animation = self.swirl_table[i][1]
            number_of_animations = self.swirl_table[i][2]

            animation_pointers = all_animation_pointers[first_animation:first_animation+number_of_animations]
            self.swirls[i] = Swirl(speed=speed)
            self.swirls[i].frames_from_block(rom, animation_pointers)

    def write_to_rom(self, rom):
        if not test_swirl_relocated(rom):
            apply_relocation_patch(rom)

        # Write frames and populate swirl table
        frame_hashes = {}
        animation_pointers = []
        animation_pointers_index = 0
        for i, swirl in enumerate(self.swirls):
            num_frames = len(swirl.frames)

            self.swirl_table[i] = [swirl.speed, animation_pointers_index, num_frames]

            frame_offsets = write_swirl_frames(rom, swirl, frame_hashes)
            animation_pointers += frame_offsets
            animation_pointers_index += num_frames

        # Allocate animation pointer table
        animation_pointer_table_offset = rom.allocate(size=4 * len(animation_pointers))
        for offset, pointer_delta in RELOCATED_SWIRL_ANIMATION_POINTER_TABLE_POINTERS:
            rom.write_multi(offset, to_snes_address(animation_pointer_table_offset + pointer_delta), 3)

        # Write animation pointer table
        for animation_pointer in animation_pointers:
            rom.write_multi(animation_pointer_table_offset, to_snes_address(animation_pointer), 4)
            animation_pointer_table_offset += 4

        # Write swirls table
        self.swirl_table.to_block(
            rom, offset=from_snes_address(SWIRL_TABLE_DEFAULT_OFFSET))

    def read_from_project(self, resource_open):
        with resource_open("Swirls/swirls", "yml", True) as f:
            swirl_data = yml_load(f)

        self.swirls = [Swirl() for i in range(self.swirl_table.num_rows)]
        for swirl_id, swirl in enumerate(self.swirls):
            log.debug("Reading Swirl #{}".format(swirl_id))
            speed = swirl_data[swirl_id]["speed"]
            num_frames = swirl_data[swirl_id]["frames"]

            swirl.speed = speed
            for frame_id in range(num_frames):
                with resource_open("Swirls/{}/{}".format(swirl_id, str(frame_id).zfill(3)), "png") as f:
                    image = open_indexed_image(f)
                    try:
                        swirl.add_frame_from_image(image)
                    except Exception as e:
                        message = "Encountered error while reading frame #{} of swirl #{}".format(frame_id, swirl_id)
                        raise CoilSnakeTraceableError(message, e)

    def write_to_project(self, resource_open):
        swirl_data = {}
        for i, swirl in enumerate(self.swirls):
            swirl_data[i] = {"speed": swirl.speed, "frames": len(swirl.frames)}
            for j, frame in enumerate(swirl.frames):
                with resource_open("Swirls/{}/{}".format(i, str(j).zfill(3)), "png") as f:
                    image = frame.image()
                    image.save(f, "png")
        with resource_open("Swirls/swirls", "yml", True) as f:
            yml_dump(swirl_data, f, default_flow_style=False)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version <= 6:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
            self.upgrade_project(
                7,
                new_version,
                rom,
                resource_open_r,
                resource_open_w,
                resource_delete)
        else:
            self.upgrade_project(
                old_version + 1,
                new_version,
                rom,
                resource_open_r,
                resource_open_w,
                resource_delete)