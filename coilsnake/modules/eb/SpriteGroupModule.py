from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.sprites import SpriteGroup, SPRITE_SIZES
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.common.yml import replace_field_in_yml, yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address, AsmPointerReference


GROUP_POINTER_TABLE_OFFSET = 0xef133f
PALETTE_TABLE_OFFSET = 0xc30000


class SpriteGroupModule(EbModule):
    NAME = "Sprite Groups"
    FREE_RANGES = [(0x2f1a7f, 0x2f4a3f),
                   (0x110000, 0x11ffff),
                   (0x120000, 0x12ffff),
                   (0x130000, 0x13ffff),
                   (0x140000, 0x14ffff),
                   (0x150000, 0x154fff)]
    SPRITE_GROUP_TABLE_REFERENCES = [
        AsmPointerReference(0x001DF9),
        AsmPointerReference(0x001E79),
        AsmPointerReference(0x001FE0),
        AsmPointerReference(0x007A8B),
        AsmPointerReference(0x04B1D0),
    ]

    def __init__(self):
        super(SpriteGroupModule, self).__init__()
        self.group_pointer_table = eb_table_from_offset(offset=GROUP_POINTER_TABLE_OFFSET)
        self.palette_table = eb_table_from_offset(offset=PALETTE_TABLE_OFFSET)
        self.groups = None

    def read_from_rom(self, rom):
        self.group_pointer_table.from_block(rom, from_snes_address(GROUP_POINTER_TABLE_OFFSET))
        self.palette_table.from_block(rom, from_snes_address(PALETTE_TABLE_OFFSET))

        # Load the sprite groups
        self.groups = []
        for i in range(self.group_pointer_table.num_rows):
            # Note: this assumes that the SPT is written contiguously
            num_sprites = 8
            # Assume that the last group only has 8 sprites
            if i < self.group_pointer_table.num_rows - 1:
                num_sprites = (self.group_pointer_table[i + 1][0] - self.group_pointer_table[i][0] - 9) // 2

            group = SpriteGroup(num_sprites)
            group.from_block(rom, from_snes_address(self.group_pointer_table[i][0]))
            self.groups.append(group)

    def write_to_project(self, resource_open):
        # Write the palettes
        with resource_open("sprite_group_palettes", "yml", True) as f:
            self.palette_table.to_yml_file(f)

        out = {}
        for i, group in enumerate(self.groups):
            out[i] = group.yml_rep()
            image = group.image(self.palette_table[group.palette][0])
            with resource_open("SpriteGroups/" + str(i).zfill(3), 'png') as image_file:
                image.save(image_file, 'png', transparency=0)
            del image
        with resource_open("sprite_groups", "yml", True) as f:
            yml_dump(out, f)

    def read_from_project(self, resource_open):
        with resource_open("sprite_group_palettes", "yml", True) as f:
            self.palette_table.from_yml_file(f)

        with resource_open("sprite_groups", "yml", True) as f:
            input = yml_load(f)
            num_groups = len(input)
            self.groups = []
            for i in range(num_groups):
                group = SpriteGroup(16)
                group.from_yml_rep(input[i])

                palette = EbPalette(1, 16)

                with resource_open("SpriteGroups/" + str(i).zfill(3), "png") as f2:
                    image = open_indexed_image(f2)
                    group.from_image(image)
                    palette.from_image(image)
                    del image

                self.groups.append(group)

                # Assign the palette number to the sprite
                for j in range(8):
                    if palette.list() == self.palette_table[j][0].list():
                        group.palette = j
                        break
                else:
                    raise CoilSnakeError("Sprite Group #" + str(i).zfill(3) + " uses an invalid palette")

    def write_to_rom(self, rom):
        self.group_pointer_table.recreate(num_rows=len(self.groups))
        with Block(size=sum(x.block_size() for x in self.groups)) as block:
            offset = 0
            # Write all the groups to the block, and sprites to rom
            for i, group in enumerate(self.groups):
                group.write_sprites_to_free(rom)
                group.to_block(block, offset)
                self.group_pointer_table[i] = [offset]
                offset += group.block_size()
            # Write the block to rom and correct the group pointers
            address = to_snes_address(rom.allocate(data=block))
            for i in range(self.group_pointer_table.num_rows):
                self.group_pointer_table[i][0] += address

        new_table_offset = rom.allocate(size=len(block))
        # Perform table relocation
        for pointer in self.SPRITE_GROUP_TABLE_REFERENCES:
            pointer.write(rom, to_snes_address(new_table_offset))
        # Write new table data
        self.group_pointer_table.to_block(block=rom, offset=new_table_offset)
        self.palette_table.to_block(block=rom, offset=from_snes_address(PALETTE_TABLE_OFFSET))

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version == 4:
            with resource_open_r("sprite_groups", "yml", True) as f:
                data = yml_load(f)
                for i in data:
                    entry = data[i]
                    collision_settings = entry["Collision Settings"]
                    entry["North/South Collision Width"] = collision_settings[0]
                    entry["North/South Collision Height"] = collision_settings[1]
                    entry["East/West Collision Width"] = collision_settings[2]
                    entry["East/West Collision Height"] = collision_settings[3]
                    del entry["Collision Settings"]
            with resource_open_w("sprite_groups", "yml", True) as f:
                yml_dump(data, f)
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        elif old_version == 2:
            replace_field_in_yml(resource_name="sprite_groups",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Unknown A",
                                 new_key="Size",
                                 value_map=dict(enumerate(SPRITE_SIZES)))
            replace_field_in_yml(resource_name="sprite_groups",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Unknown B",
                                 new_key="Collision Settings")
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
