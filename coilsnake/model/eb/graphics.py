from array import array
from copy import deepcopy

from PIL import Image

from coilsnake.exceptions.common.exceptions import InvalidArgumentError, OutOfBoundsError, InvalidUserDataError
from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.palettes import EbPalette, EbColor
from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin
from coilsnake.util.eb.graphics import read_2bpp_graphic_from_block, read_4bpp_graphic_from_block, \
    read_8bpp_graphic_from_block, read_1bpp_graphic_from_block, write_2bpp_graphic_to_block, \
    write_4bpp_graphic_to_block, write_8bpp_graphic_to_block, write_1bpp_graphic_to_block, hash_tile


_EB_GRAPHIC_TILESET_SUPPORTED_BPP_FORMATS = frozenset([1, 2, 4, 8])


class EbGraphicTileset(EqualityMixin):
    """A class representing a set of graphical tiles which adhere to the common EarthBound format.
    A graphic tileset is an ordered collection of graphical tiles. A graphical tile can be thought of as a
    two-dimensional array of numerical values. These numerical values each represent a color as an index in a palette.
    Palettes themselves are stored separately from graphical tilesets."""

    def __init__(self, num_tiles, tile_width=8, tile_height=8):
        """Creates a new EbGraphicTileset.
        :param num_tiles: the number of tiles in this tileset
        :param tile_width: width in pixels of each of the tileset's individual tiles
        :param tile_height: height in pixels of each of the tileset's individual tiles"""
        if num_tiles <= 0:
            raise InvalidArgumentError("Couldn't create EbGraphicTileset with invalid num_tiles[{}]".format(num_tiles))
        self.num_tiles_maximum = num_tiles

        if tile_width <= 0:
            raise InvalidArgumentError("Couldn't create EbGraphicTileset with invalid tile_width[{}]".format(
                tile_width))
        elif (tile_width % 8) != 0:
            raise InvalidArgumentError(("Couldn't create EbGraphicTileset with a tile_height[{}] that is not a "
                                        "multiple of 8").format(tile_height))
        self.tile_width = tile_width

        if tile_height <= 0:
            raise InvalidArgumentError("Couldn't create EbGraphicTileset with invalid tile height[{}]".format(
                tile_height))
        self.tile_height = tile_height

        self.tiles = []
        self._num_tiles_used = 0
        self._used_tiles = dict()

    def from_block(self, block, offset=0, bpp=2):
        """Reads in a tileset from the specified offset in the block.
        :param bpp: The number of bits used to represent each pixel by the block representation."""
        if bpp not in _EB_GRAPHIC_TILESET_SUPPORTED_BPP_FORMATS:
            raise NotImplementedError("Don't know how to read graphical tile data of bpp[{}]".format(bpp))
        elif (bpp != 1) and (self.tile_height != 8):
            raise NotImplementedError(("Don't know how to read graphical tile data of width[{}], height[{}], "
                                      "and bpp[{}]").format(self.tile_width, self.tile_height, bpp))

        self._num_tiles_used = 0
        self._used_tiles = dict()
        self.tiles = [[[0 for x in range(self.tile_width)] for y in range(self.tile_height)]
                      for n in range(self.num_tiles_maximum)]
        for tile in self.tiles:
            try:
                if bpp == 2:
                    offset += read_2bpp_graphic_from_block(source=block, target=tile, offset=offset)
                elif bpp == 4:
                    offset += read_4bpp_graphic_from_block(source=block, target=tile, offset=offset)
                elif bpp == 8:
                    offset += read_8bpp_graphic_from_block(source=block, target=tile, offset=offset)
                else:  # bpp == 1
                    for x in range(0, self.tile_width, 8):
                        offset += read_1bpp_graphic_from_block(source=block, target=tile, offset=offset,
                                                               x=x, height=self.tile_height)
                self._num_tiles_used += 1
            except OutOfBoundsError:
                break  # Stop if we begin to read past the end of the block

    def to_block(self, block, offset=0, bpp=2):
        """Writes this tileset to the specified offset in the block.
        :param bpp: The number of bits used to represent each pixel by the block representation."""
        if bpp not in _EB_GRAPHIC_TILESET_SUPPORTED_BPP_FORMATS:
            raise NotImplementedError("Don't know how to read graphical tile data of bpp[{}]".format(bpp))
        elif (bpp != 1) and (self.tile_height != 8):
            raise NotImplementedError("Don't know how to write image data of width[{}], height[{}], and bpp[{}]"
                                      .format(self.tile_width, self.tile_height, bpp))

        for tile in self.tiles:
            if bpp == 2:
                offset += write_2bpp_graphic_to_block(source=tile, target=block, offset=offset)
            elif bpp == 4:
                offset += write_4bpp_graphic_to_block(source=tile, target=block, offset=offset)
            elif bpp == 8:
                offset += write_8bpp_graphic_to_block(source=tile, target=block, offset=offset)
            else:  # bpp == 1
                for x in range(0, self.tile_width, 8):
                    offset += write_1bpp_graphic_to_block(source=tile, target=block, offset=offset,
                                                          x=x, height=self.tile_height)

    @staticmethod
    def tiles_from_parameters(block_size, tile_width=8, tile_height=8, bpp=2):
        """Returns the number of tiles that can be represented in a block with the given parameters.
        :param block_size: the size required to represent this tileset in a block.
        :param tile_width: width in pixels of each of the tileset's individual tiles
        :param tile_height: height in pixels of each of the tileset's individual tiles
        :param bpp: The number of bits used to represent each pixel by the block representation."""
        return block_size // (tile_height * bpp * (tile_width // 8))

    @staticmethod
    def block_size_from_parameters(num_tiles, tile_width=8, tile_height=8, bpp=2):
        """Returns the number of blocks needed to represent graphics with the given parameters.
        :param num_tiles: the number of tiles in this tileset
        :param tile_width: width in pixels of each of the tileset's individual tiles
        :param tile_height: height in pixels of each of the tileset's individual tiles
        :param bpp: The number of bits used to represent each pixel by the block representation."""
        return tile_height * bpp * (tile_width // 8) * num_tiles

    def block_size(self, bpp=2, trimmed=False):
        """Returns the size required to represent this tileset in a block.
        :param bpp: The number of bits used to represent each pixel by the block representation.
        :param trimmed: When True, trim the size to number of tiles in use; otherwise to the maximum"""
        return self.block_size_from_parameters(self._num_tiles_used if trimmed else self.num_tiles_maximum, self.tile_width, self.tile_height, bpp)

    def from_image(self, image, arrangement, palette):
        """Reads in a tileset from an image, given a known arrangement and palette which were used to construct the
        image. This function assumes that the arrangement is simple and does not make use of the horizontal or
        vertical flip flags.

        :param image: the image representation of the tileset to be read rendered using the arrangement and palette
        :param arrangement: the known arrangement which describes how the image is rendered
        :param palette: the known arrangement which describes how the image is rendered"""
        image_data = image.load()
        already_read_tiles = set()
        self.tiles = [[[0 for x in range(self.tile_width)] for y in range(self.tile_height)]
                      for n in range(self.num_tiles_maximum)]
        for y in range(arrangement.height):
            for x in range(arrangement.width):
                arrangement_item = arrangement[x, y]
                if arrangement_item.tile not in already_read_tiles:
                    tile = self.tiles[arrangement_item.tile]
                    image_x = x * self.tile_width
                    image_y = y * self.tile_height
                    for tile_y, tile_row in enumerate(tile):
                        for tile_x in range(self.tile_width):
                            tile_row[tile_x] = image_data[image_x + tile_x, image_y] % palette.subpalette_length
                        image_y += 1
                    already_read_tiles.add(arrangement_item.tile)

    def add_tile(self, tile, no_flip=False, dedup=True):
        """Adds a tile into this tileset if the tileset does not already contain it.

        :param tile: the tile to add, as a two-dimensional list
        :param no_flip: don't store any flips of this tile
        :return: a tuple containing the tile's id in this tileset, whether the tile is stored as vertically flipped,
        and whether the tile is stored as horizontally flipped"""

        tile_hash = hash_tile(tile)

        if dedup:
            try:
                tile_id, vflip, hflip = self._used_tiles[tile_hash]
                return tile_id, vflip, hflip
            except KeyError:
                pass

        # The tile does not already exist in this tileset, so add it
        if self._num_tiles_used >= self.num_tiles_maximum:
            # Error, not enough room for a new tile
            return 0, False, False

        tile_copy = deepcopy(tile)
        tile_id = self._num_tiles_used
        self.tiles.append(tile_copy)
        self._num_tiles_used += 1

        if no_flip or not dedup:
            self._used_tiles[tile_hash] = tile_id, False, False
            return tile_id, False, False

        # The tile will be stored as horizontally flipped
        self._used_tiles[tile_hash] = tile_id, False, True

        tile_copy.reverse()
        # Verically flipped tile
        self._used_tiles[hash_tile(tile_copy)] = tile_id, True, True

        for row in tile_copy:
            row.reverse()
        # Vertically and horizontally flipped tile
        self._used_tiles[hash_tile(tile_copy)] = tile_id, True, False

        tile_copy.reverse()
        # Horizontally flipped tile
        self._used_tiles[hash_tile(tile_copy)] = tile_id, False, False

        return tile_id, False, True

    def clear_tile(self, tile_id, color=0):
        tile = [[color for x in range(self.tile_width)] for y in range(self.tile_height)]
        self.tiles[tile_id] = tile

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and (self.num_tiles_maximum == other.num_tiles_maximum)
                and (self.tile_width == other.tile_width)
                and (self.tile_height == other.tile_height)
                and (self.tiles == other.tiles))

    def __getitem__(self, key):
        return self.tiles[key]


class EbTileArrangementItem(EqualityMixin, StringRepresentationMixin):
    def __init__(self, tile=0, subpalette=0, is_vertically_flipped=False, is_horizontally_flipped=False,
                 is_priority=False):
        self.tile = tile
        self.subpalette = subpalette
        self.is_vertically_flipped = is_vertically_flipped
        self.is_horizontally_flipped = is_horizontally_flipped
        self.is_priority = is_priority
        self.check_validity()

    def check_validity(self):
        if self.tile < 0 or self.tile > 0x3ff:
            raise InvalidArgumentError("Invalid tile[{}]".format(self.tile))
        if self.subpalette < 0 or self.subpalette > 7:
            raise InvalidArgumentError("Invalid subpalette[{}]".format(self.subpalette))

    def from_block(self, block, offset=0):
        data = block.read_multi(offset, 2)
        self.is_vertically_flipped = (data & 0x8000) != 0
        self.is_horizontally_flipped = (data & 0x4000) != 0
        self.is_priority = (data & 0x2000) != 0
        self.subpalette = (data & 0x1c00) >> 10
        self.tile = data & 0x3ff

    def to_block(self, block, offset=0):
        self.check_validity()
        block.write_multi(offset,
                          ((self.is_vertically_flipped << 15)
                           | (self.is_horizontally_flipped << 14)
                           | (self.is_priority << 13)
                           | (self.subpalette << 10)
                           | self.tile),
                          2)


class EbTileArrangement(EqualityMixin):
    """A class representing an image formed by an arrangement of tile-based graphics with a certain palette."""

    def __init__(self, width, height):
        """Creates a new EbTileArrangement.
        :param width: the width of the arrangement in tiles
        :param height: the height of the arrangement in tiles"""
        if width <= 0:
            raise InvalidArgumentError("Couldn't create EbTileArrangement with invalid width[{}]".format(width))
        self.width = width
        if height <= 0:
            raise InvalidArgumentError("Couldn't create EbTileArrangement with invalid height[{}]".format(height))
        self.height = height
        self.arrangement = [[EbTileArrangementItem() for x in range(self.width)] for y in range(self.height)]

    def from_block(self, block, offset=0):
        for row in self.arrangement:
            for item in row:
                item.from_block(block, offset)
                offset += 2

    def to_block(self, block, offset=0):
        for row in self.arrangement:
            for item in row:
                item.to_block(block, offset)
                offset += 2

    def block_size(self):
        return 2 * sum([len(x) for x in self.arrangement])

    def to_image(self, image, tileset, palette, ignore_subpalettes=False):
        palette.to_image(image)
        image_data = image.load()
        offset_y = 0
        for row in self.arrangement:
            offset_x = 0
            for item in row:
                tile = tileset[item.tile]
                if ignore_subpalettes:
                    palette_offset = 0
                else:
                    palette_offset = item.subpalette*palette.subpalette_length
                for tile_y in range(tileset.tile_height):
                    for tile_x in range(tileset.tile_width):
                        pixel_x, pixel_y = tile_x, tile_y
                        if item.is_vertically_flipped:
                            pixel_y = tileset.tile_height - pixel_y - 1
                        if item.is_horizontally_flipped:
                            pixel_x = tileset.tile_width - pixel_x - 1
                        image_data[offset_x + tile_x, offset_y + tile_y] = tile[pixel_y][pixel_x] + palette_offset
                offset_x += tileset.tile_width
            offset_y += tileset.tile_height

    def image(self, tileset, palette, ignore_subpalettes=False):
        image = Image.new("P", (self.width * tileset.tile_width,
                                self.height * tileset.tile_height),
                          None)
        self.to_image(image, tileset, palette, ignore_subpalettes)
        return image

    def from_image(self, image, tileset, palette, no_flip=False, dedup=True, is_animation=False):
        if palette.num_subpalettes == 1:
            self._from_image_with_single_subpalette(image, tileset, palette, no_flip, dedup, is_animation)
        else:
            # Multiple subpalettes, so we have to figure out which tile should use which subpalette
            palette.from_image(image)
            rgb_image = image.convert("RGB")
            del(image)
            rgb_image_data = rgb_image.load()
            del rgb_image

            tile = [array('B', [0] * tileset.tile_width) for i in range(tileset.tile_height)]

            for arrangement_y in range(self.height):
                image_y = arrangement_y * tileset.tile_height
                for arrangement_x in range(self.width):
                    image_x = arrangement_x * tileset.tile_width

                    tile_colors = set()
                    for tile_y in range(tileset.tile_height):
                        image_tile_y = image_y + tile_y
                        for tile_x in range(tileset.tile_width):
                            r, g, b = rgb_image_data[image_x + tile_x, image_tile_y]
                            tile_colors.add(EbColor(r=r & 0xf8, g=g & 0xf8, b=b & 0xf8))

                    try:
                        subpalette_id = palette.get_subpalette_for_colors(tile_colors)
                    except InvalidArgumentError as e:
                        raise InvalidUserDataError(
                            "Could not fit all colors in {}x{} square at ({},{}) into a single {}-color subpalette\nColors: {}\nPalette: {}".format(
                                tileset.tile_width, tileset.tile_height, image_x, image_y, palette.subpalette_length,
                                list(tile_colors), palette.subpalettes
                            ))

                    for tile_y in range(tileset.tile_height):
                        image_tile_y = image_y + tile_y
                        for tile_x in range(tileset.tile_width):
                            image_tile_x = image_x + tile_x
                            tile[tile_y][tile_x] = palette.get_color_id(rgb_image_data[image_tile_x, image_tile_y],
                                                                        subpalette_id)

                    tile_id, vflip, hflip = tileset.add_tile(tile, no_flip, dedup)
                    arrangement_item = self.arrangement[arrangement_y][arrangement_x]
                    arrangement_item.tile = tile_id
                    arrangement_item.subpalette = subpalette_id
                    arrangement_item.is_vertically_flipped = vflip
                    arrangement_item.is_horizontally_flipped = hflip
                    arrangement_item.is_priority = is_animation

    def _from_image_with_single_subpalette(self, image, tileset, palette, no_flip=False, dedup=True, is_animation=False):
        # Don't need to do any subpalette fitting because there's only one subpalette
        palette.from_image(image)
        image_data = image.load()

        tile = [array('B', [0] * tileset.tile_width) for i in range(tileset.tile_height)]

        for arrangement_y in range(self.height):
            image_y = arrangement_y * tileset.tile_height
            for arrangement_x in range(self.width):
                image_x = arrangement_x * tileset.tile_width

                for tile_y in range(tileset.tile_height):
                    image_tile_y = image_y + tile_y
                    tile_row = tile[tile_y]
                    for tile_x in range(tileset.tile_width):
                        tile_row[tile_x] = image_data[image_x + tile_x, image_tile_y]

                tile_id, vflip, hflip = tileset.add_tile(tile, no_flip, dedup)
                arrangement_item = self.arrangement[arrangement_y][arrangement_x]
                arrangement_item.tile = tile_id
                arrangement_item.subpalette = 0
                arrangement_item.is_vertically_flipped = vflip
                arrangement_item.is_horizontally_flipped = hflip
                arrangement_item.is_priority = is_animation

    def __getitem__(self, key):
        x, y = key
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            raise InvalidArgumentError("Couldn't get arrangement item[{},{}] from arrangement of size[{}x{}]".format(
                x, y, self.width, self.height))
        return self.arrangement[y][x]


class EbCompressedGraphic(object):
    def __init__(self, num_tiles, tile_width, tile_height, bpp, arrangement_width, arrangement_height,
                 num_palettes, num_subpalettes, subpalette_length, compressed_palettes=True):
        self.bpp = bpp
        self.compressed_palettes = compressed_palettes

        self.graphics = EbGraphicTileset(num_tiles=num_tiles, tile_width=tile_width, tile_height=tile_height)
        if arrangement_width and arrangement_height:
            self.arrangement = EbTileArrangement(width=arrangement_width, height=arrangement_height)
        else:
            self.arrangement = None
        self.palettes = [EbPalette(num_subpalettes=num_subpalettes, subpalette_length=subpalette_length)
                         for x in range(num_palettes)]

    def from_block(self, block, graphics_offset, arrangement_offset, palette_offsets):
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(block=block, offset=graphics_offset)
            self.graphics.from_block(block=compressed_block, offset=0, bpp=self.bpp)

        if self.arrangement:
            with EbCompressibleBlock() as compressed_block:
                compressed_block.from_compressed_block(block=block, offset=arrangement_offset)
                self.arrangement.from_block(block=compressed_block, offset=0)

        for i, palette_offset in enumerate(palette_offsets):
            if self.compressed_palettes:
                with EbCompressibleBlock() as compressed_block:
                    compressed_block.from_compressed_block(block=block, offset=palette_offset)
                    self.palettes[i].from_block(block=compressed_block, offset=0)
            else:
                self.palettes[i].from_block(block=block, offset=palette_offset)

    def to_block(self, block):
        with EbCompressibleBlock(self.graphics.block_size(bpp=self.bpp)) as compressed_block:
            self.graphics.to_block(block=compressed_block, offset=0, bpp=self.bpp)
            compressed_block.compress()
            graphics_offset = block.allocate(data=compressed_block)

        if self.arrangement:
            with EbCompressibleBlock(self.arrangement.block_size()) as compressed_block:
                self.arrangement.to_block(block=compressed_block, offset=0)
                compressed_block.compress()
                arrangement_offset = block.allocate(data=compressed_block)
        else:
            arrangement_offset = None

        palette_offsets = []
        for i, palette in enumerate(self.palettes):
            with EbCompressibleBlock(palette.block_size()) as compressed_block:
                palette.to_block(block=compressed_block, offset=0)
                if self.compressed_palettes:
                    compressed_block.compress()
                palette_offset = block.allocate(data=compressed_block)
                palette_offsets.append(palette_offset)

        return graphics_offset, arrangement_offset, palette_offsets

    def images(self, arrangement=None):
        if not arrangement:
            arrangement = self.arrangement
        return [arrangement.image(self.graphics, palette) for palette in self.palettes]

    def image(self, arrangement=None):
        return self.images(arrangement=arrangement)[0]

    def from_images(self, images, arrangement=None):
        if arrangement:
            self.palettes[0].from_image(images[0])
            self.graphics.from_image(images[0], arrangement, self.palettes[0])
        else:
            self.arrangement.from_image(images[0], self.graphics, self.palettes[0])

        for i, palette in enumerate(self.palettes[1:]):
            palette.from_image(images[i + 1])

    def from_image(self, image, arrangement=None):
        self.from_images(images=[image], arrangement=arrangement)


class EbCompanyLogo(EbCompressedGraphic):
    def __init__(self):
        super(EbCompanyLogo, self).__init__(
            num_tiles=256,
            tile_width=8,
            tile_height=8,
            bpp=2,
            arrangement_width=32,
            arrangement_height=28,
            num_palettes=1,
            num_subpalettes=5,
            subpalette_length=4
        )

    def from_block(self, block, graphics_offset, arrangement_offset, palette_offsets):
        super(EbCompanyLogo, self).from_block(block, graphics_offset, arrangement_offset, palette_offsets)

        # The first color of every subpalette after subpalette 0 is ignored and drawn as the first color subpalette 0
        #  instead
        c = self.palettes[0][0, 0].tuple()
        for i in range(1, self.palettes[0].subpalette_length):
            self.palettes[0][i, 0].from_tuple(c)

    def from_images(self, images, arrangement=None):
        self.palettes[0].from_image(images[0])
        # Set all first colors of each subpalette to the image's first color
        c = self.palettes[0][0, 0].tuple()
        for i in range(1, self.palettes[0].subpalette_length):
            self.palettes[0][i, 0].from_tuple(c)

        super(EbCompanyLogo, self).from_images(images, arrangement)


class EbAttractModeLogo(EbCompressedGraphic):
    def __init__(self):
        super(EbAttractModeLogo, self).__init__(
            num_tiles=256,
            tile_width=8,
            tile_height=8,
            bpp=2,
            arrangement_width=32,
            arrangement_height=32,
            num_palettes=1,
            num_subpalettes=1,
            subpalette_length=4
        )


class EbGasStationLogo(EbCompressedGraphic):
    def __init__(self):
        super(EbGasStationLogo, self).__init__(
            num_tiles=632,
            tile_width=8,
            tile_height=8,
            bpp=8,
            arrangement_width=32,
            arrangement_height=32,
            num_palettes=3,
            num_subpalettes=1,
            subpalette_length=256
        )


class EbTownMap(EbCompressedGraphic):
    def __init__(self):
        super(EbTownMap, self).__init__(
            num_tiles=768,
            tile_width=8,
            tile_height=8,
            bpp=4,
            arrangement_width=32,
            arrangement_height=28,
            num_palettes=1,
            num_subpalettes=2,
            subpalette_length=16
        )

    def from_block(self, block, offset):
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(block=block, offset=offset)
            self.palettes[0].from_block(block=compressed_block, offset=0)
            self.arrangement.from_block(block=compressed_block, offset=self.palettes[0].block_size())
            self.graphics.from_block(block=compressed_block,
                                     offset=self.palettes[0].block_size() + 2048,
                                     bpp=self.bpp)

    def to_block(self, rom):
        # Arrangement space is 2048 bytes long since it's 32x32x2 in VRAM
        with EbCompressibleBlock(size=self.palettes[0].block_size() + 2048 + self.graphics.block_size(bpp=self.bpp)) \
                as compressed_block:
            self.palettes[0].to_block(block=compressed_block, offset=0)
            self.arrangement.to_block(block=compressed_block, offset=self.palettes[0].block_size())
            self.graphics.to_block(block=compressed_block,
                                   offset=self.palettes[0].block_size() + 2048,
                                   bpp=self.bpp)
            compressed_block.compress()
            return rom.allocate(data=compressed_block)

    def from_images(self, images, arrangement=None):
        # The game has problems if you try to use color 0 of subpal 1 directly after using color 0 of subpal 0
        self.palettes[0][1, 0].r = 0
        self.palettes[0][1, 0].g = 0
        self.palettes[0][1, 0].b = 0
        self.palettes[0][1, 0].used = True

        super(EbTownMap, self).from_images(images, arrangement)


class EbTownMapIcons(EbCompressedGraphic):
    def __init__(self):
        super(EbTownMapIcons, self).__init__(
            num_tiles=288,
            tile_width=8,
            tile_height=8,
            bpp=4,
            arrangement_width=0,
            arrangement_height=0,
            num_palettes=1,
            num_subpalettes=2,
            subpalette_length=16,
            compressed_palettes=False
        )

class EbCastGraphic(EbCompressedGraphic):
    def __init__(self, name, num_8x8_tiles):
        super(EbCastGraphic, self).__init__(
            num_tiles=num_8x8_tiles,
            tile_width=8,
            tile_height=8,
            bpp=2,
            arrangement_width=0,
            arrangement_height=0,
            num_palettes=1,
            num_subpalettes=1,
            subpalette_length=4,
            compressed_palettes=False
        )

        self.name = name
        self.saved_arrangement = None

    def path(self):
        return 'Cast/{}'.format(self.name)

    def cast_arrangement(self):
        if self.saved_arrangement == None:
            tiles = self.graphics.num_tiles_maximum
            arrangement_height = 2
            arrangement_width = tiles // arrangement_height
            layout_width  = 16
            layout_height = tiles // layout_width
            self.saved_arrangement = EbTileArrangement(arrangement_width, arrangement_height)
            line1 = []
            line2 = []

            for i in range(0, layout_height, 2):
                for j in range(layout_width * i, layout_width * (i + 1)):
                    line1.append(EbTileArrangementItem(j))
                    line2.append(EbTileArrangementItem(j + layout_width))

            self.saved_arrangement.arrangement = [line1, line2]

        return self.saved_arrangement

class EbCastNameGraphic(EbCastGraphic):
    def __init__(self):
        super(EbCastNameGraphic, self).__init__(
            name='NameGraphic',
            num_8x8_tiles=672
        )

class EbCastMiscGraphic(EbCastGraphic):
    def __init__(self):
        super(EbCastMiscGraphic, self).__init__(
            name='MiscGraphic',
            num_8x8_tiles=64
        )
