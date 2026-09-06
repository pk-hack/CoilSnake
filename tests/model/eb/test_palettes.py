from PIL import Image

from unittest import skip

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.palettes import EbColor, EbPalette, setup_eb_palette_from_image, join_sets
from tests.coilsnake_test import BaseTestCase, TilesetImageTestCase


class TestEbColor(BaseTestCase):
    def setUp(self):
        self.color = EbColor()

    def test_init(self):
        color2 = EbColor(r=3, g=255, b=84)
        self.assertEqual(color2.r, 3)
        self.assertEqual(color2.g, 255)
        self.assertEqual(color2.b, 84)

    def test_init_default(self):
        self.assertEqual(self.color.r, 0)
        self.assertEqual(self.color.g, 0)
        self.assertEqual(self.color.b, 0)

    def test_from_block(self):
        block = Block()
        block.from_list([0x5f, 0x0a])
        self.color.from_block(block, 0)
        self.assertEqual(self.color.r, 248)
        self.assertEqual(self.color.g, 144)
        self.assertEqual(self.color.b, 16)

    def test_to_block(self):
        block = Block()
        block.from_list([0] * 2)
        self.color.r = 248
        self.color.g = 144
        self.color.b = 16
        self.color.to_block(block, 0)
        self.assertListEqual(block.to_list(), [0x5f, 0x0a])

    def test_from_tuple(self):
        self.color.from_tuple((20, 40, 69))
        self.assertEqual(self.color.r, 20)
        self.assertEqual(self.color.g, 40)
        self.assertEqual(self.color.b, 69)

    def test_tuple(self):
        self.color.from_tuple((20, 40, 69))
        self.assertEqual(self.color.tuple(), (20, 40, 69))

    def test_from_list(self):
        self.color.from_list([20, 40, 69])
        self.assertEqual(self.color.tuple(), (16, 40, 64))

        self.color.from_list([55, 44, 33, 20, 40, 69], offset=2)
        self.assertEqual(self.color.tuple(), (32, 16, 40))

    def test_to_list(self):
        self.color.from_tuple((20, 40, 69))
        test_list = [0] * 5
        self.color.to_list(test_list)
        self.assertListEqual(test_list, [20, 40, 69, 0, 0])
        self.color.to_list(test_list, 2)
        self.assertListEqual(test_list, [20, 40, 20, 40, 69])

    def test_list(self):
        self.color.from_tuple((20, 40, 69))
        self.assertEqual(self.color.list(), [20, 40, 69])


class TestEbPalette(BaseTestCase, TilesetImageTestCase):
    def setUp(self):
        super(TestEbPalette, self).setUp()
        self.palette = EbPalette(2, 3)

    def test_init(self):
        self.assertEqual(self.palette.num_subpalettes, 2)
        self.assertEqual(self.palette.subpalette_length, 3)

    def test_init_invalid(self):
        self.assertRaises(InvalidArgumentError, EbPalette, 0, 1)
        self.assertRaises(InvalidArgumentError, EbPalette, -1, 1)
        self.assertRaises(InvalidArgumentError, EbPalette, 1, 0)
        self.assertRaises(InvalidArgumentError, EbPalette, 1, -1)
        self.assertRaises(InvalidArgumentError, EbPalette, 0, 0)
        self.assertRaises(InvalidArgumentError, EbPalette, -1, -1)

    def test_num_colors(self):
        self.assertEqual(self.palette.num_colors(), 6)

    def test_getitem(self):
        self.assertEqual(self.palette[0, 0].tuple(), (0, 0, 0))
        self.assertEqual(self.palette[0, 1].tuple(), (0, 0, 0))
        self.palette[0, 1].from_tuple((8, 16, 32))
        self.assertEqual(self.palette[0, 0].tuple(), (0, 0, 0))
        self.assertEqual(self.palette[0, 1].tuple(), (8, 16, 32))

    def test_getitem_invalid(self):
        self.assertRaises(InvalidArgumentError, self.palette.__getitem__, (-1, 0))
        self.assertRaises(InvalidArgumentError, self.palette.__getitem__, (0, -1))
        self.assertRaises(InvalidArgumentError, self.palette.__getitem__, (-1, -1))
        self.assertRaises(InvalidArgumentError, self.palette.__getitem__, (2, 0))
        self.assertRaises(InvalidArgumentError, self.palette.__getitem__, (0, 3))
        self.assertRaises(InvalidArgumentError, self.palette.__getitem__, (2, 3))

    def test_from_list(self):
        self.palette.from_list([
            0, 0, 0, 40, 8, 72, 80, 88, 48,
            248, 0, 0, 80, 56, 40, 16, 136, 136
        ])
        self.assertEqual(self.palette[0, 0].tuple(), (0, 0, 0))
        self.assertEqual(self.palette[0, 1].tuple(), (40, 8, 72))
        self.assertEqual(self.palette[0, 2].tuple(), (80, 88, 48))
        self.assertEqual(self.palette[1, 0].tuple(), (248, 0, 0))
        self.assertEqual(self.palette[1, 1].tuple(), (80, 56, 40))
        self.assertEqual(self.palette[1, 2].tuple(), (16, 136, 136))

    def test_to_list(self):
        self.palette[0, 0].from_tuple((0, 0, 0))
        self.palette[0, 1].from_tuple((40, 8, 72))
        self.palette[0, 2].from_tuple((80, 88, 48))
        self.palette[1, 0].from_tuple((248, 0, 0))
        self.palette[1, 1].from_tuple((80, 56, 40))
        self.palette[1, 2].from_tuple((16, 136, 136))
        self.assertListEqual(self.palette.list(), [0, 0, 0, 40, 8, 72, 80, 88, 48,
                                                248, 0, 0, 80, 56, 40, 16, 136, 136])

    def test_from_block(self):
        block = Block()
        block.from_list([0, 0, 37, 36, 106, 25,
                         31, 0, 234, 20, 34, 70])
        self.palette.from_block(block)
        self.assertListEqual(self.palette.list(), [
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
        self.assertListEqual(block[0:14].to_list(), [0xff, 0, 0, 37, 36, 106, 25,
                                                  31, 0, 234, 20, 34, 70, 0xff])

    def test_from_image(self):
        self.palette.from_image(self.tile_image_01_img)
        self.assertListEqual(self.palette.list(),
                          [0x00, 0x00, 0x00,
                           0x08, 0x00, 0xf8,
                           0xf8, 0x00, 0x00,
                           0x00, 0xf8, 0x18,
                           0xc0, 0xf8, 0x00,
                           0xf8, 0xf8, 0xf8])

    def test_to_image(self):
        image = Image.new('P', (10, 10))
        self.palette[0, 0].from_tuple((0, 0, 0))
        self.palette[0, 1].from_tuple((40, 8, 72))
        self.palette[0, 2].from_tuple((80, 88, 48))
        self.palette[1, 0].from_tuple((248, 0, 0))
        self.palette[1, 1].from_tuple((80, 56, 40))
        self.palette[1, 2].from_tuple((16, 136, 136))
        self.palette.to_image(image)
        self.assertListEqual(image.getpalette()[0:(self.palette.num_colors() * 3)],
                          [0, 0, 0, 40, 8, 72, 80, 88, 48,
                           248, 0, 0, 80, 56, 40, 16, 136, 136])
        del image

    def test_add_colors_to_subpalette_single_color(self):
        self.palette.add_colors_to_subpalette([EbColor(r=64, g=32, b=16)])

        self.assertEqual(self.palette[1, 0].tuple(), (64, 32, 16))
        self.assertTrue(self.palette[1, 0].used)
        for i in range(self.palette.num_subpalettes):
            for j in range(self.palette.subpalette_length):
                if (i, j) not in [(1, 0)]:
                    self.assertFalse(self.palette[i, j].used)

    def test_add_colors_to_subpalette_shared_colors(self):
        self.palette.add_colors_to_subpalette([EbColor(r=64, g=32, b=16)])
        self.palette.add_colors_to_subpalette([EbColor(r=64, g=32, b=16), EbColor(r=128, g=0, b=16)])

        self.assertEqual(self.palette[1, 0].tuple(), (64, 32, 16))
        self.assertTrue(self.palette[1, 0].used)
        self.assertEqual(self.palette[1, 1].tuple(), (128, 0, 16))
        self.assertTrue(self.palette[1, 1].used)
        for i in range(self.palette.num_subpalettes):
            for j in range(self.palette.subpalette_length):
                if (i, j) not in [(1, 0), (1, 1)]:
                    self.assertFalse(self.palette[i, j].used)

    def test_add_colors_to_subpalette_shared_colors2(self):
        self.palette.add_colors_to_subpalette([EbColor(r=64, g=32, b=16)])
        self.palette.add_colors_to_subpalette([EbColor(r=64, g=32, b=16),
                                               EbColor(r=128, g=0, b=16)])
        self.palette.add_colors_to_subpalette([EbColor(r=64, g=32, b=16),
                                               EbColor(r=16, g=32, b=64),
                                               EbColor(r=32, g=32, b=32)])

        self.assertEqual(self.palette[1, 0].tuple(), (64, 32, 16))
        self.assertTrue(self.palette[1, 0].used)
        self.assertEqual(self.palette[1, 1].tuple(), (128, 0, 16))
        self.assertTrue(self.palette[1, 1].used)
        self.assertFalse(self.palette[1, 2].used)

        self.assertEqual(set([self.palette[0, x].tuple() for x in range(self.palette.subpalette_length)]),
                     set([(64, 32, 16), (16, 32, 64), (32, 32, 32)]))
        self.assertEqual([self.palette[0, x].used for x in range(self.palette.subpalette_length)].count(True), 3)


class TestCreateEbPaletteFromImage(BaseTestCase, TilesetImageTestCase):
    @skip("Forcibly disabled for some reason")
    def test_8x8_2colors_1subpaletteof2(self):
        return
        eb_palette = EbPalette(num_subpalettes=1, subpalette_length=2)
        setup_eb_palette_from_image(eb_palette, self.tile_8x8_2bpp_img, 8, 8)
        self.assertEqual(eb_palette.num_subpalettes, 1)
        self.assertEqual(eb_palette.subpalette_length, 2)
        self.assertEqual(eb_palette[0, 0].tuple(), (0xf8, 0xf8, 0xf8))
        self.assertEqual(eb_palette[0, 1].tuple(), (0, 0, 0))

    @skip("Forcibly disabled for some reason")
    def test_extra_colors(self):
        return
        eb_palette = EbPalette(num_subpalettes=3, subpalette_length=4)
        setup_eb_palette_from_image(eb_palette, self.tile_8x8_2bpp_img, 8, 8)
        self.assertEqual(eb_palette.num_subpalettes, 3)
        self.assertEqual(eb_palette.subpalette_length, 4)
        self.assertEqual(eb_palette[0, 0].tuple(), (0xf8, 0xf8, 0xf8))
        self.assertEqual(eb_palette[0, 1].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[0, 2].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[0, 3].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[1, 0].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[1, 1].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[1, 2].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[1, 3].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[2, 0].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[2, 1].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[2, 2].tuple(), (0, 0, 0))
        self.assertEqual(eb_palette[2, 3].tuple(), (0, 0, 0))

    @skip("Forcibly disabled for some reason")
    def test_8x8_5colors_2subpalettesof4(self):
        return
        eb_palette = EbPalette(num_subpalettes=2, subpalette_length=4)
        setup_eb_palette_from_image(eb_palette, self.tile_8x8_2bpp_3_img, 8, 8)
        self.assertEqual(eb_palette.num_subpalettes, 2)
        self.assertEqual(eb_palette.subpalette_length, 4)

        self.assertSetEqual({eb_palette[1, i] for i in range(4)},
                         {EbColor(24, 0, 248), EbColor(0, 248, 24), EbColor(152, 0, 248), EbColor(248, 144, 0)})
        self.assertSetEqual({eb_palette[0, i] for i in range(4)},
                         {EbColor(24, 0, 248), EbColor(0, 248, 24), EbColor(216, 248, 0), EbColor(152, 0, 248)})


    def test_cant_fit_colors(self):
        eb_palette = EbPalette(num_subpalettes=2, subpalette_length=1)
        with self.assertRaises(InvalidArgumentError):
            setup_eb_palette_from_image(eb_palette, self.tile_8x8_2bpp_img, 8, 8)

    def test_cant_fit_colors_2(self):
        eb_palette = EbPalette(num_subpalettes=1, subpalette_length=4)
        with self.assertRaises(InvalidArgumentError):
            setup_eb_palette_from_image(eb_palette, self.tile_8x8_2bpp_3_img, 8, 8)


class JoinSetsTestCase(BaseTestCase):
    def test_join_sets(self):
        # print("Blah")
        result = join_sets([set([1, 2, 3]), set([3, 4, 5]), set([2, 6])], 2, 4)
        self.assertListEqual(result, [set([1, 2, 3, 6]), set([3, 4, 5])])

        result = join_sets([set([1, 2])], 3, 4)
        self.assertListEqual(result, [set([1, 2])])
