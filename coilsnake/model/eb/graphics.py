from array import array
from copy import deepcopy
import logging
from PIL import Image
from zlib import crc32

from coilsnake.exceptions.common.exceptions import InvalidArgumentError, OutOfBoundsError
from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin
from coilsnake.util.eb.graphics import read_2bpp_graphic_from_block, read_4bpp_graphic_from_block, \
    read_8bpp_graphic_from_block, read_1bpp_graphic_from_block, write_2bpp_graphic_to_block, \
    write_4bpp_graphic_to_block, write_8bpp_graphic_to_block, write_1bpp_graphic_to_block


log = logging.getLogger(__name__)

_EB_GRAPHIC_TILESET_SUPPORTED_BPP_FORMATS = frozenset([1, 2, 4, 8])


def hash_tile(tile):
    csum = 0
    for col in tile:
        csum = crc32(col, csum)
    return csum

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
            raise InvalidArgumentError("Couldn't create EbGraphicTileset with a tile_height[{}] that is not a multiple"
                                       "of 8".format(tile_height))
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
            raise NotImplementedError("Don't know how to read graphical tile data of width[{}], height[{}], "
                                      "and bpp[{}]".format(self.tile_width, self.tile_height, bpp))

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

    def block_size(self, bpp=2):
        """Returns the size required to represent this tileset in a block.
        :param bpp: The number of bits used to represent each pixel by the block representation."""
        return self.tile_height * bpp * (self.tile_width / 8) * self.num_tiles_maximum

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

    def add_tile(self, tile):
        """Adds a tile into this tileset if the tileset does not already contain it.

        :param tile: the tile to add, as a two-dimensional list
        :return: a tuple containing the tile's id in this tileset, whether the tile is stored as vertically flipped,
        and whether the tile is stored as horizontally flipped"""

        tile_hash = hash_tile(tile)
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

    def to_image(self, image, tileset, palette):
        palette.to_image(image)
        image_data = image.load()
        offset_y = 0
        for row in self.arrangement:
            offset_x = 0
            for item in row:
                tile = tileset[item.tile]
                palette_offset = item.subpalette * palette.subpalette_length
                for tile_y in xrange(tileset.tile_height):
                    for tile_x in xrange(tileset.tile_width):
                        pixel_x, pixel_y = tile_x, tile_y
                        if item.is_vertically_flipped:
                            pixel_y = tileset.tile_height - pixel_y - 1
                        if item.is_horizontally_flipped:
                            pixel_x = tileset.tile_width - pixel_x - 1
                        image_data[offset_x + tile_x, offset_y + tile_y] = tile[pixel_y][pixel_x] + palette_offset
                offset_x += tileset.tile_width
            offset_y += tileset.tile_height

    def image(self, tileset, palette):
        image = Image.new("P", (self.width * tileset.tile_width,
                                self.height * tileset.tile_height),
                          None)
        self.to_image(image, tileset, palette)
        return image

    def from_image(self, image, tileset, palette):
        if palette.num_subpalettes == 1:
            # Don't need to do any subpalette fitting because there's only one subpalette
            palette.from_image(image)
            image_data = image.load()

            tile = [array('B', [0 for i in xrange(tileset.tile_width)])
                    for j in xrange(tileset.tile_height)]

            for arrangement_y in xrange(self.height):
                image_y = arrangement_y * tileset.tile_height
                for arrangement_x in xrange(self.width):
                    image_x = arrangement_x * tileset.tile_width

                    for tile_y in xrange(tileset.tile_height):
                        image_tile_y = image_y + tile_y
                        tile_row = tile[tile_y]
                        for tile_x in xrange(tileset.tile_width):
                            tile_row[tile_x] = image_data[image_x + tile_x, image_tile_y]

                    tile_id, vflip, hflip = tileset.add_tile(tile)
                    self.arrangement[arrangement_y][arrangement_x] = EbTileArrangementItem(
                        tile=tile_id,
                        subpalette=0,
                        is_vertically_flipped=vflip,
                        is_horizontally_flipped=hflip,
                        is_priority=False)
        else:
            # TODO test/fix this code
            # Multiple subpalettes, so we have to figure out which tile should use which subpalette
            rgb_image = image.convert("RGB")
            del image
            rgb_image_data = rgb_image.load()
            del rgb_image

            for arrangement_y in range(self.height):
                for arrangement_x in range(self.width):
                    tile_colors = set()
                    for tile_pixel_y in range(tileset.tile_height):
                        for tile_pixel_x in range(tileset.tile_width):
                            r, g, b = rgb_image_data[tile_pixel_x, tile_pixel_y]
                            tile_colors.add(r & 0xf8, g & 0xf8, b & 0xf8)

                    subpalette_id = palette.add_colors_to_subpalette(tile_colors)
                    tile = [array('B', [palette.get_color_id(rgb_image_data[i, j], subpalette_id)
                                        for j in range(arrangement_y, arrangement_y + tileset.tile_height)])
                            for i in range(arrangement_x, arrangement_x + tileset.tile_width)]

                    tile_id, vflip, hflip = tileset.add_tile(tile)
                    self[arrangement_x, arrangement_y] = EbTileArrangementItem(
                        tile=tile_id,
                        subpalette=subpalette_id,
                        is_vertically_flipped=vflip,
                        is_horizontally_flipped=hflip,
                        is_priority=False)


    def __getitem__(self, key):
        x, y = key
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            raise InvalidArgumentError("Couldn't get arrangement item[{},{}] from arrangement of size[{}x{}]".format(
                x, y, self.width, self.height))
        return self.arrangement[y][x]