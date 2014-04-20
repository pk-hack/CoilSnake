import logging
from zlib import crc32
from array import array

from coilsnake.exceptions.common.exceptions import InvalidArgumentError, InvalidYmlRepresentationError
from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin


log = logging.getLogger(__name__)


class EbColor(EqualityMixin, StringRepresentationMixin):
    """A class representing a color which adheres to the EarthBound format.
    An EarthBound color is simply a grouping of three values: red, green, and blue.
    Please note that when an EarthBound color is saved to a block, each R, G, and B value loses its three least
    significant bits."""

    def __init__(self, r=None, g=None, b=None):
        if (r is None) and (g is None) and (b is None):
            self.r = self.g = self.b = 0
            self.used = False
        else:
            self.r = r
            self.g = g
            self.b = b
            self.used = True

    def __eq__(self, other):
        return ((self.r == other.r)
                and (self.g == other.g)
                and (self.b == other.b))

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.tuple())

    def from_block(self, block, offset=0):
        self.used = True
        bgr = block.read_multi(offset, 2) & 0x7FFF
        self.r = (bgr & 0x001f) * 8
        self.g = ((bgr & 0x03e0) >> 5) * 8
        self.b = (bgr >> 10) * 8
        log.debug("Read {} from offset[{:#x}]".format(self, offset))

    def to_block(self, block, offset=0):
        log.debug("Writing {} to offset[{:#x}]".format(self, offset))
        block.write_multi(offset,
                          ((self.r >> 3) & 0x1f)
                          | (((self.g >> 3) & 0x1f) << 5)
                          | (((self.b >> 3) & 0x1f) << 10),
                          2)

    def from_tuple(self, rgb):
        self.used = True
        self.r, self.g, self.b = rgb

    def tuple(self):
        return self.r, self.g, self.b

    def from_list(self, rgb_list, offset=0):
        self.used = True
        self.r = rgb_list[offset]
        self.g = rgb_list[offset + 1]
        self.b = rgb_list[offset + 2]

    def to_list(self, rgb_list, offset=0):
        rgb_list[offset] = self.r
        rgb_list[offset + 1] = self.g
        rgb_list[offset + 2] = self.b

    def list(self):
        return [self.r, self.g, self.b]

    def yml_rep(self):
        return "({:d}, {:d}, {:d})".format(self.r, self.g, self.b)

    def from_yml_rep(self, yml_rep):
        try:
            self.used = True
            self.r, self.g, self.b = map(int, yml_rep[1:-1].split(','))
        except:
            raise InvalidYmlRepresentationError("Could not parse value[{}] as an (R, G, B) color".format(yml_rep))


class EbPalette(EqualityMixin):
    """A class representing a palette which adheres to the common EarthBound format.
    An EarthBound palette is composed of one or more subpalettes.
    Each subpalette is composed of one or more EbColors."""

    def __init__(self, num_subpalettes, subpalette_length, rgb_list=None):
        """Creates a new EbPalette.
        :param num_subpalettes: the number of subpalettes within the palette.
        :param subpalette_length: the number of colors within each subpalette."""
        if num_subpalettes <= 0:
            raise InvalidArgumentError("Couldn't create EbPalette with invalid num_subpalettes[{}]".format(
                num_subpalettes))
        self.num_subpalettes = num_subpalettes
        if subpalette_length <= 0:
            raise InvalidArgumentError("Couldn't create EbPalette with invalid subpalette_length[{}]".format(
                subpalette_length))
        self.subpalette_length = subpalette_length

        self.subpalettes = [[EbColor() for j in range(self.subpalette_length)] for i in range(self.num_subpalettes)]

        if rgb_list is not None:
            self.from_list(rgb_list)

    def num_colors(self):
        return self.num_subpalettes * self.subpalette_length

    def block_size(self):
        return 2 * self.num_colors()

    def from_list(self, rgb_list):
        i = 0
        for j in range(self.num_subpalettes):
            for k in range(self.subpalette_length):
                self[j, k].from_list(rgb_list=rgb_list, offset=i)
                i += 3

    def list(self):
        return reduce(lambda x, y: x.__add__(y.list()), reduce(lambda x, y: x.__add__(y), self.subpalettes, []), [])

    def get_subpalette(self, subpalette_num):
        subpalette = EbPalette(num_subpalettes=1, subpalette_length=self.subpalette_length)
        for i in range(self.subpalette_length):
            subpalette[0, i].from_tuple(self[subpalette_num, i].tuple())
        return subpalette

    def from_block(self, block, offset=0):
        log.debug("Reading a EbPalette of size[{}x{}] from offset[{:#x}]".format(self.num_subpalettes,
                                                                                 self.subpalette_length, offset))
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.from_block(block, offset)
                offset += 2

    def to_block(self, block, offset=0):
        log.debug("Writing a EbPalette of size[{}x{}] to offset[{:#x}]".format(self.num_subpalettes,
                                                                               self.subpalette_length, offset))
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.to_block(block, offset)
                offset += 2

    def from_image(self, image):
        log.debug("Reading a EbPalette of size[{}x{}] from an image with palette data of length[{}]".format(
            self.num_subpalettes, self.subpalette_length, len(image.getpalette())))
        self.from_list(image.getpalette()[0:(self.num_colors() * 3)])

    def to_image(self, image):
        log.debug("Writing an EbPalette of size[{}x{}] to an image".format(self.num_subpalettes,
                                                                           self.subpalette_length))
        color_list = self.list()
        # Some programs do not know how to interpret an image with a two-color palette, so pad the palette
        if self.num_colors() == 2:
            color_list += (0, 248, 248) * 2
        image.putpalette(color_list)

    def yml_rep(self):
        return [inner.yml_rep()
                for outer in self.subpalettes
                for inner in outer]

    def from_yml_rep(self, yml_rep):
        if not (isinstance(yml_rep, list) and all(isinstance(x, str) for x in yml_rep)):
            raise InvalidYmlRepresentationError("Could not parse value[{}] as a list of (R, G, B) colors"
                                                .format(yml_rep))
        elif len(yml_rep) != self.num_subpalettes * self.subpalette_length:
            raise InvalidYmlRepresentationError("Expected a list of {} colors, but got only {} colors"
                                                .format(len(yml_rep), self.num_subpalettes * self.subpalette_length))

        i = 0
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.from_yml_rep(yml_rep[i])
                i += 1

    def add_colors_to_subpalette(self, colors):
        if type(colors) == list:
            colors = set(colors)

        if len(colors) > self.subpalette_length:
            # TODO Handle this error better
            return 0

        subpalette_info = [(len(colors & set(subpalette)),  # number of shared colors
                            sum([(not color.used) for color in subpalette]),  # number of unused colors in palette
                            i,
                            colors - set(subpalette),  # set of colors not in palette
                            ) for i, subpalette in enumerate(self.subpalettes)]
        subpalette_info = filter(lambda x: x[1] >= len(x[3]), subpalette_info)

        if len(subpalette_info) == 0:
            # Not enough room to put these colors in a subpalette
            # TODO Handle this error better.
            return 0

        subpalette_info.sort(reverse=True)
        num_shared_colors, num_unused_colors, subpalette_id, new_colors = subpalette_info[0]
        subpalette = self.subpalettes[subpalette_id]
        for new_color in new_colors:
            for i in range(self.subpalette_length):
                if not subpalette[i].used:
                    subpalette[i].from_tuple(new_color.tuple())
                    break

        return subpalette_id

    def get_color_id(self, rgb, subpalette_id):
        r, g, b = rgb
        color = EbColor(r=r, g=g, b=b)
        for i, c in enumerate(self.subpalettes[subpalette_id]):
            if color == c:
                return i
        # TODO Handle this error better
        return 0

    def __getitem__(self, key):
        subpalette_number, color_number = key
        if subpalette_number < 0 or color_number < 0 or subpalette_number >= self.num_subpalettes \
                or color_number >= self.subpalette_length:
            raise InvalidArgumentError("Could not get color[{},{}] from palette of size[{},{}]".format(
                subpalette_number, color_number, self.num_subpalettes, self.subpalette_length))
        return self.subpalettes[subpalette_number][color_number]

    def hash(self):
        a = array('B', self.list())
        return crc32(a)