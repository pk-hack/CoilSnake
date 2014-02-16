import logging
from PIL import Image

from coilsnake.exceptions import InvalidArgumentError, OutOfBoundsError
from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin
from coilsnake.util.eb.graphics import read_2bpp_graphic_from_block, read_4bpp_graphic_from_block, \
    read_8bpp_graphic_from_block, read_1bpp_graphic_from_block, write_2bpp_graphic_to_block, write_4bpp_graphic_to_block, \
    write_8bpp_graphic_to_block, write_1bpp_graphic_to_block


log = logging.getLogger(__name__)

_EB_GRAPHIC_TILESET_SUPPORTED_BPP_FORMATS = frozenset([1, 2, 4, 8])


class EbGraphicTileset(EqualityMixin):
    """A class representing a set of graphical tiles which adhere to the common EarthBound format."""
    def __init__(self, num_tiles, tile_width=8, tile_height=8):
        """Creates a new EbGraphicTileset.
        :param num_tiles: the number of tiles in this tileset
        :param tile_width: width in pixels of each of the tileset's individual tiles
        :param tile_height: height in pixels of each of the tileset's individual tiles"""
        if num_tiles <= 0:
            raise InvalidArgumentError("Couldn't create EbGraphicTileset with invalid number of tiles: {}".format(
                num_tiles))
        self.num_tiles_maximum = num_tiles

        if tile_width <= 0:
            raise InvalidArgumentError("Couldn't create EbGraphicTileset with invalid tile width[{}]".format(tile_width))
        elif (tile_width % 8) != 0:
            raise NotImplementedError("Don't know how to create an EbGraphicTileset with a tile height[{}] which is "
                                      "not a multiple of 8".format(tile_height))
        self.tile_width = tile_width

        if tile_height <= 0:
            raise InvalidArgumentError("Couldn't create EbGraphicTileset with invalid tile height[{}]".format(
                tile_height))
        self.tile_height = tile_height

        self.tiles = [[[0 for x in range(self.tile_width)] for y in range(self.tile_height)]
                      for n in range(self.num_tiles_maximum)]
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
        for tile in self.tiles:
            try:
                if bpp == 2:
                    offset += read_2bpp_graphic_from_block(source=block, target=tile, offset=offset)
                elif bpp == 4:
                    offset += read_4bpp_graphic_from_block(source=block, target=tile, offset=offset)
                elif bpp == 8:
                    offset += read_8bpp_graphic_from_block(source=block, target=tile, offset=offset)
                else: # bpp == 1
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
            else: # bpp == 1
                for x in range(0, self.tile_width, 8):
                    offset += write_1bpp_graphic_to_block(source=tile, target=block, offset=offset,
                                                          x=x, height=self.tile_height)

    def block_size(self, bpp=2):
        """Returns the size required to represent this tileset in a block.
        :param bpp: The number of bits used to represent each pixel by the block representation."""
        if bpp != 1:
            return 8 * bpp * self.num_tiles_maximum
        else:
            return self.tile_height * (self.tile_width / 2)

    def from_image(self, image, arrangement, palette):
        """Reads in a tileset from an image, given a known arrangement and palette which were used to construct the
        image.

        TODO support the arrangement flip flags in this function

        :param image: the image representation of the tileset to be read rendered using the arrangement and palette
        :param arrangement: the known arrangement which describes how the image is rendered
        :param palette: the known arrangement which describes how the image is rendered"""
        image_data = image.load()
        already_read_tiles = set()
        for y in range(arrangement.height):
            for x in range(arrangement.width):
                arrangement_item = arrangement[x, y]
                if arrangement_item.tile not in already_read_tiles:
                    tile = self.tiles[arrangement_item.tile]
                    image_x = x*self.tile_width
                    image_y = y * self.tile_height
                    for tile_y, tile_row in enumerate(tile):
                        for tile_x in range(self.tile_width):
                            tile_row[tile_x] = image_data[image_x + tile_x, image_y] % palette.subpalette_length
                        image_y += 1
                    already_read_tiles.add(arrangement_item.tile)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and (self.num_tiles_maximum == other.num_tiles_maximum)
                and (self.tile_size == other.tile_size)
                and (self.bpp == other.bpp)
                and (self.tiles == other.tiles))

    def __getitem__(self, key):
        return self.tiles[key]


class EbColor(EqualityMixin, StringRepresentationMixin):
    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b

    def from_block(self, block, offset=0):
        bgr = block.read_multi(offset, 2) & 0x7FFF
        self.r = (bgr & 0x001f) * 8
        self.g = ((bgr & 0x03e0) >> 5) * 8
        self.b = (bgr >> 10) * 8

    def to_block(self, block, offset=0):
        block.write_multi(offset,
                          ((self.r >> 3) & 0x1f)
                          | (((self.g >> 3) & 0x1f) << 5)
                          | (((self.b >> 3) & 0x1f) << 10),
                          2)

    def from_tuple(self, rgb):
        self.r, self.b, self.g = rgb

    def tuple(self):
        return self.r, self.b, self.g

    __tuple__ = tuple

    def from_list(self, rgb_list, offset=0):
        self.r = rgb_list[offset]
        self.g = rgb_list[offset+1]
        self.b = rgb_list[offset+2]

    def to_list(self, rgb_list, offset=0):
        rgb_list[offset] = self.r
        rgb_list[offset+1] = self.g
        rgb_list[offset+2] = self.b

    def list(self):
        return [self.r, self.g, self.b]


class EbPalette(EqualityMixin):
    """A class representing a palette which adheres to the common EarthBound format."""
    def __init__(self, num_subpalettes, subpalette_length):
        """Creates a new EbPalette.
        :param num_subpalettes: the number of subpalettes within the palette.
        :param subpalette_length: the number of colors within each subpalette."""
        if num_subpalettes <= 0:
            raise InvalidArgumentError("Couldn't create EbPalette with invalid number of subpalettes: {}".format(
                num_subpalettes))
        self.num_subpalettes = num_subpalettes
        if subpalette_length <= 0:
            raise InvalidArgumentError("Couldn't create EbPalette with invalid colors per subpalette: {}".format(
                subpalette_length))
        self.subpalette_length = subpalette_length

        self.subpalettes = [[EbColor() for j in range(self.subpalette_length)] for i in range(self.num_subpalettes)]

    def num_colors(self):
        return self.num_subpalettes * self.subpalette_length

    def from_block(self, block, offset=0):
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.from_block(block, offset)
                offset += 2

    def to_block(self, block, offset=0):
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.to_block(block, offset)
                offset += 2

    def from_list(self, rgb_list):
        i = 0
        for j in range(self.num_subpalettes):
            for k in range(self.subpalette_length):
                self[j, k].from_list(rgb_list=rgb_list, offset=i)
                i += 3

    def list(self):
        return reduce(lambda x, y: x.__add__(y.list()), reduce(lambda x, y: x.__add__(y), self.subpalettes, []), [])

    def from_image(self, image):
        log.debug("Reading palette of len[{}] from image for pal of size {},{}".format(
            len(image.getpalette()), self.num_subpalettes, self.subpalette_length))
        self.from_list(image.getpalette()[0:(self.num_colors() * 3)])

    def to_image(self, image):
        color_list = self.list()
        # Some programs do not know how to interpret an image with a two-color palette, so pad the palette
        if self.num_colors() == 2:
            color_list += (255, 0, 0) * 2
        image.putpalette(color_list)

    def __getitem__(self, key):
        subpalette_number, color_number = key
        return self.subpalettes[subpalette_number][color_number]


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
            raise InvalidArgumentError("Couldn't create EbTileImage with invalid width[{}]".format(width))
        self.width = width
        if height <= 0:
            raise InvalidArgumentError("Couldn't create EbTileImage with invalid height[{}]".format(height))
        self.height = height
        self.arrangement = [[EbTileArrangementItem() for x in range(self.width)] for y in range(self.height)]

    def from_block(self, block, offset=0):
        for row in self.arrangement:
            for item in row:
                item.from_block(block, offset)
                offset += 2

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

    def __getitem__(self, key):
        x, y = key
        return self.arrangement[y][x]