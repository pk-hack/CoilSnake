from zlib import crc32
from array import array
from functools import reduce

from coilsnake.exceptions.common.exceptions import InvalidArgumentError, InvalidYmlRepresentationError
from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin


CHARACTERS = "0123456789abcdefghijklmnopqrstuv"


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
            self.from_tuple((r, g, b))

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

    def to_block(self, block, offset=0):
        block.write_multi(offset,
                          ((self.r >> 3) & 0x1f)
                          | (((self.g >> 3) & 0x1f) << 5)
                          | (((self.b >> 3) & 0x1f) << 10),
                          2)

    def from_tuple(self, rgb):
        self.used = True
        self.r, self.g, self.b = (val & 0xf8 for val in rgb)

    def tuple(self):
        return self.r, self.g, self.b

    def from_list(self, rgb_list, offset=0):
        rgbs = rgb_list[offset:offset+3]
        if not rgbs:
            rgbs = (0, 0, 0)
        self.from_tuple(rgbs)

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
            self.r &= 0xf8
            self.g &= 0xf8
            self.b &= 0xf8
        except:
            raise InvalidYmlRepresentationError("Could not parse value[{}] as an (R, G, B) color".format(yml_rep))

    def __repr__(self):
        return "#{:02x}{:02x}{:02x}".format(self.r, self.g, self.b)


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
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.from_block(block, offset)
                offset += 2

    def to_block(self, block, offset=0):
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.to_block(block, offset)
                offset += 2

    def from_image(self, image):
        self.from_list(image.getpalette()[0:(self.num_colors() * 3)])

    def to_image(self, image):
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

    def __str__(self):
        out = str()
        for subpalette in self.subpalettes:
            for color in subpalette:
                out += CHARACTERS[color.r >> 3]
                out += CHARACTERS[color.g >> 3]
                out += CHARACTERS[color.b >> 3]
        return out

    def from_string(self, string_rep):
        i = 0
        for subpalette in self.subpalettes:
            for color in subpalette:
                color.r = int(string_rep[i], 32) << 3
                i += 1
                color.g = int(string_rep[i], 32) << 3
                i += 1
                color.b = int(string_rep[i], 32) << 3
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
        subpalette_info = [x for x in subpalette_info if x[1] >= len(x[3])]

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

    def get_subpalette_for_colors(self, colors):
        for i, subpalette in enumerate(self.subpalettes):
            if colors.issubset(set(subpalette)):
                return i
        raise InvalidArgumentError("Colors do not match a subpalette")

    def get_color_id(self, rgb, subpalette_id):
        r, g, b = rgb
        r &= 0xf8
        g &= 0xf8
        b &= 0xf8
        subpalette = self.subpalettes[subpalette_id]
        for i, c in reversed(list(enumerate(subpalette))):
            if c.r == r and c.g == g and c.b == b:
                return i
        # TODO Handle this error better
        return 0

    def __getitem__(self, key):
        subpalette_number, color_number = key
        if subpalette_number < 0 or subpalette_number >= self.num_subpalettes \
                or (isinstance(color_number, int) and (color_number < 0 or color_number >= self.subpalette_length)):
            raise InvalidArgumentError("Could not get color[{},{}] from palette of size[{},{}]".format(
                subpalette_number, color_number, self.num_subpalettes, self.subpalette_length))
        return self.subpalettes[subpalette_number][color_number]

    def __setitem__(self, key, item):
        subpalette_number, color_number = key
        if subpalette_number < 0 or subpalette_number >= self.num_subpalettes \
                or (isinstance(color_number, int) and (color_number < 0 or color_number >= self.subpalette_length)):
            raise InvalidArgumentError("Could not set color[{},{}] of palette of size[{},{}]".format(
                subpalette_number, color_number, self.num_subpalettes, self.subpalette_length))

        self.subpalettes[subpalette_number][color_number] = item

    def hash(self):
        a = array('B', self.list())
        return crc32(a)


def setup_eb_palette_from_image(palette, img, tile_width, tile_height):
    num_subpalettes = palette.num_subpalettes
    subpalette_length = palette.subpalette_length

    width, height = img.size
    rgb_image = img.convert("RGB")
    rgb_image_data = rgb_image.load()
    del rgb_image

    # First, get a list of all the unique sets of colors in each tile
    color_sets = []

    for x in range(0, width, tile_width):
        for y in range(0, height, tile_height):
            new_color_set = set()

            for tile_x in range(x, x + tile_width):
                for tile_y in range(y, y+tile_height):
                    r, g, b = rgb_image_data[tile_x, tile_y]
                    r &= 0xf8
                    g &= 0xf8
                    b &= 0xf8
                    new_color_set.add((r, g, b))

            if len(new_color_set) > subpalette_length:
                raise InvalidArgumentError(
                    "Too many unique colors in the {}x{} box at ({},{}) in the image to fit into {} subpalettes,"
                    " each having {} colors".format(
                        tile_width, tile_height, x, y, num_subpalettes, subpalette_length))

            for i, color_set in enumerate(color_sets):
                if new_color_set.issubset(color_set):
                    break
                elif new_color_set.issuperset(color_set):
                    color_sets[i] = new_color_set
                    break
            else:
                color_sets.append(new_color_set)

    # Next, find a way to fit all the sets of colors into a palette
    color_sets = join_sets(color_sets, num_subpalettes, subpalette_length)
    if color_sets is None:
        raise InvalidArgumentError(
                "Too many unique colors in the image to fit into {} subpalettes, each having {} colors".format(
                    num_subpalettes, subpalette_length))

    for subpalette_id, color_set in enumerate(color_sets):
        for color_id, rgb in enumerate(color_set):
            palette[subpalette_id, color_id].from_tuple(rgb)

    return palette


def join_sets(sets, num_sets_to_output, set_length):
    if len(sets) <= num_sets_to_output:
        return sets

    for i, set1 in enumerate(sets):
        sets_in_order_of_shared_elements = [(len(set1.intersection(x)), j+i+1, x) for (j, x) in enumerate(sets[i+1:])]
        sets_in_order_of_shared_elements.sort(reverse=True)
        sets_in_order_of_shared_elements = [(j, x) for (_shared, j, x) in sets_in_order_of_shared_elements]
        for j, set2 in sets_in_order_of_shared_elements:
            combined_set = set1.union(set2)
            if len(combined_set) <= set_length:
                new_set_list = sets[:]
                new_set_list[i] = combined_set
                new_set_list.pop(j)
                result = join_sets(new_set_list, num_sets_to_output, set_length)
                if result is not None:
                    return result

    return None