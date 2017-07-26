from array import array

from PIL import Image

from coilsnake.model.common.table import EnumeratedLittleEndianIntegerTableEntry, RowTableEntry, \
    LittleEndianIntegerTableEntry
from coilsnake.util.common.helper import grouped
from coilsnake.util.eb.graphics import read_4bpp_graphic_from_block, write_4bpp_graphic_to_block, hash_tile
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


BATTLE_SPRITE_SIZES = [(0, 0), (32, 32), (64, 32), (32, 64), (64, 64), (128, 64), (128, 128)]


class EbBattleSprite(object):
    def __init__(self):
        self.sprite = None
        self.width = None
        self.height = None

    def block_size(self):
        return (self.width // 32) * (self.height // 32) * 4 * 4 * 32

    def from_block(self, block, offset=0, size=0):
        width, height = BATTLE_SPRITE_SIZES[size]
        if (self.width != width) or (self.height != height):
            self.width = width
            self.height = height
            self.sprite = [array('B', [0] * self.width) for y in range(self.height)]

        for q in range(0, height // 32):
            for r in range(0, width // 32):
                for a in range(0, 4):
                    for j in range(0, 4):
                        offset += read_4bpp_graphic_from_block(
                            target=self.sprite,
                            source=block,
                            offset=offset,
                            x=(j + r * 4) * 8,
                            y=(a + q * 4) * 8
                        )

    def to_block(self, block, offset=0):
        for q in range(0, self.height // 32):
            for r in range(0, self.width // 32):
                for a in range(0, 4):
                    for j in range(0, 4):
                        offset += write_4bpp_graphic_to_block(
                            source=self.sprite,
                            target=block,
                            offset=offset,
                            x=(j + r * 4) * 8,
                            y=(a + q * 4) * 8
                        )

    def image(self, palette):
        image = Image.new("P", (self.width, self.height), None)
        palette.to_image(image)

        image_data = image.load()
        for y in range(0, self.height):
            for x in range(0, self.width):
                image_data[x, y] = self.sprite[y][x]

        return image

    def from_image(self, image):
        if (self.width, self.height) != image.size:
            self.width, self.height = image.size
            self.sprite = [array('B', [0] * self.width) for y in range(self.height)]

        image_data = image.load()
        for y in range(self.height):
            for x in range(0, self.width):
                self.sprite[y][x] = image_data[x, y]

    def size(self):
        return BATTLE_SPRITE_SIZES.index((self.width, self.height))

    def __getitem__(self, key):
        x, y = key
        return self.sprite[y][x]

    def hash(self):
        return hash_tile(self.sprite)


class EbRegularSprite(object):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.data = None

    def __eq__(self, other):
        return ((self.width == other.width)
                and (self.height == other.height)
                and (self.data == other.data))
    
    __hash__ = None

    def from_block(self, block, width, height, offset=0):
        self.width = width
        self.height = height
        self.data = [array('B', [0] * self.width) for i in range(self.height)]
        for i in range(self.height // 8):
            for j in range(self.width // 8):
                offset += read_4bpp_graphic_from_block(target=self.data, source=block, offset=offset, x=j*8, y=i*8)

    def to_block(self, block, offset=0):
        for i in range(self.height // 8):
            for j in range(self.width // 8):
                offset += write_4bpp_graphic_to_block(source=self.data, target=block, offset=offset, x=j*8, y=i*8)

    def draw(self, image, x, y):
        image_data = image.load()
        for dx in range(self.width):
            for dy in range(self.height):
                image_data[x + dx, y + dy] = self.data[dy][dx]

    def from_image(self, image, x, y, width, height):
        self.width = width
        self.height = height
        self.data = [array('B', [0] * self.width) for i in range(self.height)]
        image_data = image.load()
        for dx in range(self.width):
            for dy in range(self.height):
                self.data[dy][dx] = image_data[x + dx, y + dy]

    def flip_horizontally(self):
        for row in self.data:
            row.reverse()

    def block_size(self):
        return (self.width // 8) * (self.height // 8) * 32

    def hash(self):
        return hash_tile(self.data)

    def flipped_hash(self):
        self.flip_horizontally()
        h = self.hash()
        self.flip_horizontally()
        return h


SPRITE_SIZES = ["16x16", "16x16 2", "24x16", "32x16", "48x16", "16x24", "24x24", "16x32", "32x32", "48x32", "24x40",
                "16x48", "32x48", "48x48", "64x48", "64x64", "64x80"]
SpriteGroupSizeTableEntry = EnumeratedLittleEndianIntegerTableEntry.create("Size", 1, SPRITE_SIZES)
SpriteGroupCollisionNSWidthEntry = LittleEndianIntegerTableEntry.create("North/South Collision Width", 1)
SpriteGroupCollisionNSHeightEntry = LittleEndianIntegerTableEntry.create("North/South Collision Height", 1)
SpriteGroupCollisionEWWidthEntry = LittleEndianIntegerTableEntry.create("East/West Collision Width", 1)
SpriteGroupCollisionEWHeightEntry = LittleEndianIntegerTableEntry.create("East/West Collision Height", 1)

SpriteGroupHeaderTableEntry = RowTableEntry.from_schema(
    name="Sprite Group Header Table Entry",
    schema=[LittleEndianIntegerTableEntry.create("Height", 1),
            LittleEndianIntegerTableEntry.create("Width", 1),
            SpriteGroupSizeTableEntry,
            LittleEndianIntegerTableEntry.create("Palette", 1),
            SpriteGroupCollisionNSWidthEntry,
            SpriteGroupCollisionNSHeightEntry,
            SpriteGroupCollisionEWWidthEntry,
            SpriteGroupCollisionEWHeightEntry,
            LittleEndianIntegerTableEntry.create("Bank", 1)])


class SpriteGroup(object):
    # The order in which sprite directions are compiled to form a sprite group, based on examining the game data.
    # The order is: S, N, W, E, NW, SW, SE, NE
    SPRITE_COMPILATION_ORDER = [2, 4, 1, 3, 8, 7, 6, 5]

    def __init__(self, num_sprites):
        self.width = 0
        self.height = 0
        self.palette = 0
        self.size = 0
        self.collision_ns_w = 0
        self.collision_ns_h = 0
        self.collision_ew_w = 0
        self.collision_ew_h = 0
        self.num_sprites = max(0, num_sprites)
        self.sprites = None

        # For writing to block
        self.bank = 0
        self.sprite_pointers = None

    def block_size(self):
        return 9 + self.num_sprites * 2

    def from_block(self, rom, offset):
        header_data = SpriteGroupHeaderTableEntry.from_block(rom, offset)
        self.height = header_data[0]
        self.width = header_data[1] >> 4
        self.size = header_data[2]
        self.palette = (header_data[3] >> 1) & 0x7
        self.collision_ns_w = header_data[4]
        self.collision_ns_h = header_data[5]
        self.collision_ew_w = header_data[6]
        self.collision_ew_h = header_data[7]
        bank = header_data[8] << 16

        self.sprites = [[EbRegularSprite(), False] for i in range(self.num_sprites)]
        i = offset + 9
        for spff in self.sprites:
            ptr = bank | rom.read_multi(i, 2)
            spff[1] = (ptr & 2) != 0
            spff[0].from_block(rom, self.width * 8, self.height * 8, from_snes_address(ptr & 0xfffffc))
            if (ptr & 1) != 0:
                spff[0].flip_horizontally()
            i += 2

    def to_block(self, block, offset=0):
        header_data = [
            self.height,
            self.width << 4,
            self.size,
            self.palette << 1,
            self.collision_ns_w,
            self.collision_ns_h,
            self.collision_ew_w,
            self.collision_ew_h,
            self.bank
        ]
        SpriteGroupHeaderTableEntry.to_block(block=block, offset=offset, value=header_data)
        for i, sprite_pointer in enumerate(self.sprite_pointers):
            block.write_multi(key=offset + 9 + 2 * i,
                              item=sprite_pointer,
                              size=2)

    def calculate_unique_sprites(self):
        unique_sprites = dict()
        unique_sprite_usages = [None] * self.num_sprites

        sprite_pairs = enumerate(grouped([x[0] for x in self.sprites], 2))
        sprite_pairs = [x for _, x in sorted(zip(SpriteGroup.SPRITE_COMPILATION_ORDER, sprite_pairs))]

        for i, (sprite_1, sprite_2) in sprite_pairs:
            sprite_1_i = i*2
            sprite_2_i = i*2 + 1

            sprite_1_hash = sprite_1.hash()
            sprite_1_used = sprite_1_hash in unique_sprites

            sprite_1_flipped_hash = sprite_1.flipped_hash()
            sprite_1_flipped_used = sprite_1_flipped_hash in unique_sprites

            sprite_2_hash = sprite_2.hash()
            sprite_2_used = sprite_2_hash in unique_sprites

            sprite_2_flipped_hash = sprite_2.flipped_hash()
            sprite_2_flipped_used = sprite_2_flipped_hash in unique_sprites

            if sprite_1_hash == sprite_2_hash:
                if sprite_1_flipped_used:
                    unique_sprite_usages[sprite_1_i] = (sprite_1_flipped_hash, True)
                    unique_sprite_usages[sprite_2_i] = (sprite_1_flipped_hash, True)
                else:
                    if not sprite_1_used:
                        unique_sprites[sprite_1_hash] = sprite_1
                    unique_sprite_usages[sprite_1_i] = (sprite_1_hash, False)
                    unique_sprite_usages[sprite_2_i] = (sprite_1_hash, False)
            elif sprite_1_flipped_hash == sprite_2_hash:
                if sprite_1_flipped_used:
                    unique_sprite_usages[sprite_1_i] = (sprite_1_flipped_hash, True)
                    unique_sprite_usages[sprite_2_i] = (sprite_1_flipped_hash, False)
                else:
                    if not sprite_1_used:
                        unique_sprites[sprite_1_hash] = sprite_1
                    unique_sprite_usages[sprite_1_i] = (sprite_1_hash, False)
                    unique_sprite_usages[sprite_2_i] = (sprite_1_hash, True)
            elif sprite_1_used:
                unique_sprite_usages[sprite_1_i] = (sprite_1_hash, False)
                if not sprite_2_used:
                    unique_sprites[sprite_2_hash] = sprite_2
                unique_sprite_usages[sprite_2_i] = (sprite_2_hash, False)
            elif sprite_1_flipped_used:
                unique_sprite_usages[sprite_1_i] = (sprite_1_flipped_hash, True)
                if not sprite_2_flipped_used:
                    sprite_2.flip_horizontally()
                    unique_sprites[sprite_2_flipped_hash] = sprite_2
                unique_sprite_usages[sprite_2_i] = (sprite_2_flipped_hash, True)
            elif sprite_2_used:
                unique_sprites[sprite_1_hash] = sprite_1
                unique_sprite_usages[sprite_1_i] = (sprite_1_hash, False)
                unique_sprite_usages[sprite_2_i] = (sprite_2_hash, False)
            elif sprite_2_flipped_used:
                sprite_1.flip_horizontally()
                unique_sprites[sprite_1_flipped_hash] = sprite_1
                unique_sprite_usages[sprite_1_i] = (sprite_1_flipped_hash, True)
                unique_sprite_usages[sprite_2_i] = (sprite_2_flipped_hash, True)
            else:
                unique_sprites[sprite_1_hash] = sprite_1
                unique_sprites[sprite_2_hash] = sprite_2
                unique_sprite_usages[sprite_1_i] = (sprite_1_hash, False)
                unique_sprite_usages[sprite_2_i] = (sprite_2_hash, False)

        if self.num_sprites % 2 == 1:
            sprite_i = self.num_sprites - 1
            sprite = self.sprites[-1][0]
            sprite_hash = sprite.hash()

            if sprite_hash in unique_sprites:
                unique_sprite_usages[sprite_i] = (sprite_hash, False)
            else:
                sprite_flipped_hash = sprite.flipped_hash()
                if sprite_flipped_hash not in unique_sprites:
                    unique_sprites[sprite_hash] = sprite
                    unique_sprite_usages[sprite_i] = (sprite_hash, False)
                else:
                    unique_sprite_usages[sprite_i] = (sprite_flipped_hash, True)

        return unique_sprites, unique_sprite_usages

    def write_sprites_to_free(self, rom):
        if self.num_sprites == 0:
            self.sprite_pointers = []
            return

        unique_sprites, unique_sprite_usages = self.calculate_unique_sprites()

        # Find a free area
        offset = rom.allocate(size=sum([x.block_size() for x in unique_sprites.values()]),
                              can_write_to=(lambda y: (y & 0xf) == 0))
        self.bank = to_snes_address(offset) >> 16
        offset_start = offset & 0xffff

        # Write each sprite
        sprite_offsets = dict()
        for i, (sprite_hash, sprite) in enumerate(sorted(unique_sprites.items())):
            sprite.to_block(rom, offset)
            sprite_offsets[sprite_hash] = offset
            offset += sprite.block_size()

        # Get the pointers for each sprite in the group
        self.sprite_pointers = [None] * self.num_sprites
        for i, (sprite_hash, is_mirrored) in enumerate(unique_sprite_usages):
            self.sprite_pointers[i] = (sprite_offsets[sprite_hash] & 0xffff) | is_mirrored | (self.sprites[i][1] << 1)

    def image(self, palette):
        # Image will be a 4x4 grid of sprites
        image = Image.new("P", (self.width * 8 * 4, self.height * 8 * 4), 0)
        palette.to_image(image)

        # Draw the sprites
        x = 0
        y = 0
        for sprite, swim_flag in self.sprites:
            sprite.draw(image, x * sprite.width, y * sprite.height)
            x += 1
            if x >= 4:
                y += 1
                x = 0
        return image

    def from_image(self, image):
        if not self.sprites and self.num_sprites is not None:
            self.sprites = [[EbRegularSprite(), False] for i in range(self.num_sprites)]

        sprite_width, sprite_height = image.size
        sprite_width //= 4
        sprite_height //= 4
        self.width, self.height = sprite_width // 8, sprite_height // 8

        x = 0
        y = 0
        for sprite, swim_flag in self.sprites:
            sprite.from_image(image, x * sprite_width, y * sprite_height, sprite_width, sprite_height)
            x += 1
            if x >= 4:
                y += 1
                x = 0

    def yml_rep(self):
        return {SpriteGroupSizeTableEntry.name: SpriteGroupSizeTableEntry.to_yml_rep(self.size),
                SpriteGroupCollisionNSWidthEntry.name:
                    SpriteGroupCollisionNSWidthEntry.to_yml_rep(self.collision_ns_w),
                SpriteGroupCollisionNSHeightEntry.name:
                    SpriteGroupCollisionNSHeightEntry.to_yml_rep(self.collision_ns_h),
                SpriteGroupCollisionEWWidthEntry.name:
                    SpriteGroupCollisionEWWidthEntry.to_yml_rep(self.collision_ew_w),
                SpriteGroupCollisionEWHeightEntry.name:
                    SpriteGroupCollisionEWHeightEntry.to_yml_rep(self.collision_ew_h),
                'Swim Flags': [a_x[1] for a_x in self.sprites],
                'Length': self.num_sprites}

    def from_yml_rep(self, yml_rep):
        self.num_sprites = yml_rep['Length']
        self.sprites = [[EbRegularSprite(), False] for i in range(self.num_sprites)]
        self.size = SpriteGroupSizeTableEntry.from_yml_rep(yml_rep['Size'])
        self.collision_ns_w = SpriteGroupCollisionNSWidthEntry.from_yml_rep(
            yml_rep[SpriteGroupCollisionNSWidthEntry.name])
        self.collision_ns_h = SpriteGroupCollisionNSHeightEntry.from_yml_rep(
            yml_rep[SpriteGroupCollisionNSHeightEntry.name])
        self.collision_ew_w = SpriteGroupCollisionEWWidthEntry.from_yml_rep(
            yml_rep[SpriteGroupCollisionEWWidthEntry.name])
        self.collision_ew_h = SpriteGroupCollisionEWHeightEntry.from_yml_rep(
            yml_rep[SpriteGroupCollisionEWHeightEntry.name])
        swim_flags = yml_rep['Swim Flags']
        i = 0
        try:
            for spff in self.sprites:
                spff[1] = swim_flags[i]
                i += 1
        except IndexError:
            pass