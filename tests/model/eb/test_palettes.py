from PIL import Image

from nose.tools import assert_equal, assert_list_equal, assert_raises

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.palettes import EbColor, EbPalette
from tests.coilsnake_test import BaseTestCase, TilesetImageTestCase


class TestEbColor(BaseTestCase):
    def setup(self):
        self.color = EbColor()

    def test_init(self):
        color2 = EbColor(r=3, g=255, b=84)
        assert_equal(color2.r, 3)
        assert_equal(color2.g, 255)
        assert_equal(color2.b, 84)

    def test_init_default(self):
        assert_equal(self.color.r, 0)
        assert_equal(self.color.g, 0)
        assert_equal(self.color.b, 0)

    def test_from_block(self):
        block = Block()
        block.from_list([0x5f, 0x0a])
        self.color.from_block(block, 0)
        assert_equal(self.color.r, 248)
        assert_equal(self.color.g, 144)
        assert_equal(self.color.b, 16)

    def test_to_block(self):
        block = Block()
        block.from_list([0] * 2)
        self.color.r = 248
        self.color.g = 144
        self.color.b = 16
        self.color.to_block(block, 0)
        assert_list_equal(block.to_list(), [0x5f, 0x0a])

    def test_from_tuple(self):
        self.color.from_tuple((20, 40, 69))
        assert_equal(self.color.r, 20)
        assert_equal(self.color.g, 40)
        assert_equal(self.color.b, 69)

    def test_tuple(self):
        self.color.from_tuple((20, 40, 69))
        assert_equal(self.color.tuple(), (20, 40, 69))

    def test_from_list(self):
        self.color.from_list([20, 40, 69])
        assert_equal(self.color.tuple(), (20, 40, 69))

        self.color.from_list([55, 44, 33, 20, 40, 69], offset=2)
        assert_equal(self.color.tuple(), (33, 20, 40))

    def test_to_list(self):
        self.color.from_tuple((20, 40, 69))
        test_list = [0] * 5
        self.color.to_list(test_list)
        assert_list_equal(test_list, [20, 40, 69, 0, 0])
        self.color.to_list(test_list, 2)
        assert_list_equal(test_list, [20, 40, 20, 40, 69])

    def test_list(self):
        self.color.from_tuple((20, 40, 69))
        assert_equal(self.color.list(), [20, 40, 69])


class TestEbPalette(BaseTestCase, TilesetImageTestCase):
    def setup(self):
        super(TestEbPalette, self).setup()
        self.palette = EbPalette(2, 3)

    def test_init(self):
        assert_equal(self.palette.num_subpalettes, 2)
        assert_equal(self.palette.subpalette_length, 3)

    def test_init_invalid(self):
        assert_raises(InvalidArgumentError, EbPalette, 0, 1)
        assert_raises(InvalidArgumentError, EbPalette, -1, 1)
        assert_raises(InvalidArgumentError, EbPalette, 1, 0)
        assert_raises(InvalidArgumentError, EbPalette, 1, -1)
        assert_raises(InvalidArgumentError, EbPalette, 0, 0)
        assert_raises(InvalidArgumentError, EbPalette, -1, -1)

    def test_num_colors(self):
        assert_equal(self.palette.num_colors(), 6)

    def test_getitem(self):
        assert_equal(self.palette[0, 0].tuple(), (0, 0, 0))
        assert_equal(self.palette[0, 1].tuple(), (0, 0, 0))
        self.palette[0, 1].from_tuple((8, 16, 32))
        assert_equal(self.palette[0, 0].tuple(), (0, 0, 0))
        assert_equal(self.palette[0, 1].tuple(), (8, 16, 32))

    def test_getitem_invalid(self):
        assert_raises(InvalidArgumentError, self.palette.__getitem__, (-1, 0))
        assert_raises(InvalidArgumentError, self.palette.__getitem__, (0, -1))
        assert_raises(InvalidArgumentError, self.palette.__getitem__, (-1, -1))
        assert_raises(InvalidArgumentError, self.palette.__getitem__, (2, 0))
        assert_raises(InvalidArgumentError, self.palette.__getitem__, (0, 3))
        assert_raises(InvalidArgumentError, self.palette.__getitem__, (2, 3))

    def test_from_list(self):
        self.palette.from_list([
            0, 0, 0, 40, 8, 72, 80, 88, 48,
            248, 0, 0, 80, 56, 40, 16, 136, 136
        ])
        assert_equal(self.palette[0, 0].tuple(), (0, 0, 0))
        assert_equal(self.palette[0, 1].tuple(), (40, 8, 72))
        assert_equal(self.palette[0, 2].tuple(), (80, 88, 48))
        assert_equal(self.palette[1, 0].tuple(), (248, 0, 0))
        assert_equal(self.palette[1, 1].tuple(), (80, 56, 40))
        assert_equal(self.palette[1, 2].tuple(), (16, 136, 136))

    def test_to_list(self):
        self.palette[0, 0].from_tuple((0, 0, 0))
        self.palette[0, 1].from_tuple((40, 8, 72))
        self.palette[0, 2].from_tuple((80, 88, 48))
        self.palette[1, 0].from_tuple((248, 0, 0))
        self.palette[1, 1].from_tuple((80, 56, 40))
        self.palette[1, 2].from_tuple((16, 136, 136))
        assert_list_equal(self.palette.list(), [0, 0, 0, 40, 8, 72, 80, 88, 48,
                                                248, 0, 0, 80, 56, 40, 16, 136, 136])

    def test_from_block(self):
        block = Block()
        block.from_list([0, 0, 37, 36, 106, 25,
                         31, 0, 234, 20, 34, 70])
        self.palette.from_block(block)
        assert_list_equal(self.palette.list(), [
            0, 0, 0, 40, 8, 72, 80, 88, 48,
            248, 0, 0, 80, 56, 40, 16, 136, 136
        ])

    def test_to_block(self):
        self.palette.from_list([
            0, 0, 0, 40, 8, 72, 80, 88, 48,
            248, 0, 0, 80, 56, 40, 16, 136, 136
        ])
        block = Block()
        block.from_list([0xff] * 50)
        self.palette.to_block(block, offset=1)
        assert_list_equal(block[0:14].to_list(), [0xff, 0, 0, 37, 36, 106, 25,
                                                  31, 0, 234, 20, 34, 70, 0xff])

    def test_from_image(self):
        self.palette.from_image(self.tile_image_01_img)
        assert_list_equal(self.palette.list(),
                          [0x00, 0x00, 0x00, 0x0c, 0x00, 0xff, 0xff, 0x00, 0x00,
                           0x00, 0xff, 0x18, 0xc6, 0xff, 0x00, 0xff, 0xff, 0xff])

    def test_to_image(self):
        image = Image.new('P', (10, 10))
        self.palette[0, 0].from_tuple((0, 0, 0))
        self.palette[0, 1].from_tuple((40, 8, 72))
        self.palette[0, 2].from_tuple((80, 88, 48))
        self.palette[1, 0].from_tuple((248, 0, 0))
        self.palette[1, 1].from_tuple((80, 56, 40))
        self.palette[1, 2].from_tuple((16, 136, 136))
        self.palette.to_image(image)
        assert_list_equal(image.getpalette()[0:(self.palette.num_colors() * 3)],
                          [0, 0, 0, 40, 8, 72, 80, 88, 48,
                           248, 0, 0, 80, 56, 40, 16, 136, 136])
        del image