from itertools import zip_longest
import tempfile

import os
from PIL import Image, ImageChops
from unittest import TestCase


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
TEST_IMAGE_DIR = os.path.join(TEST_DATA_DIR, "images")


def earthbound_rom_available():
    return os.path.exists(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))


class BaseTestCase(TestCase):
    def test_baseline(self):
        pass

    def assert_files_equal(self, expected, result):
        for i in zip_longest(iter(expected), iter(result)):
            self.assertEqual(i[0], i[1])


    def assert_images_equal(self, expected, result):
        self.assertIsNone(ImageChops.difference(expected, result).getbbox())

class TemporaryWritableFileTestCase(TestCase):
    def setUp(self):
        self.temporary_wo_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temporary_wo_file_name = self.temporary_wo_file.name

    def tearDown(self):
        if not self.temporary_wo_file.closed:
            self.temporary_wo_file.close()
        os.remove(self.temporary_wo_file_name)


class TilesetImageTestCase(TestCase):
    def setUp(self):
        self.tile_image_01_fp = open(os.path.join(TEST_IMAGE_DIR, "tile_image_01.png"), 'rb')
        self.tile_image_01_img = Image.open(self.tile_image_01_fp)
        self.tile_8x8_2bpp_fp = open(os.path.join(TEST_IMAGE_DIR, "tile_8x8_2bpp.png"), 'rb')
        self.tile_8x8_2bpp_img = Image.open(self.tile_8x8_2bpp_fp)
        self.tile_8x8_2bpp_2_fp = open(os.path.join(TEST_IMAGE_DIR, "tile_8x8_2bpp_2.png"), 'rb')
        self.tile_8x8_2bpp_2_img = Image.open(self.tile_8x8_2bpp_2_fp)
        self.tile_8x8_2bpp_3_fp = open(os.path.join(TEST_IMAGE_DIR, "tile_8x8_2bpp_3.png"), 'rb')
        self.tile_8x8_2bpp_3_img = Image.open(self.tile_8x8_2bpp_3_fp)
        self.tile_8x16_4bpp_fp = open(os.path.join(TEST_IMAGE_DIR, "tile_8x16_4bpp.png"), 'rb')
        self.tile_8x16_4bpp_img = Image.open(self.tile_8x16_4bpp_fp)

    def tearDown(self):
        self.tile_image_01_fp.close()
        del self.tile_image_01_img
        self.tile_8x8_2bpp_fp.close()
        del self.tile_8x8_2bpp_img
        self.tile_8x8_2bpp_2_fp.close()
        del self.tile_8x8_2bpp_2_img
        self.tile_8x8_2bpp_3_fp.close()
        del self.tile_8x8_2bpp_3_img
        self.tile_8x16_4bpp_fp.close()
        del self.tile_8x16_4bpp_img


class SpriteGroupTestCase(TestCase):
    def setUp(self):
        self.spritegroup_1_f = open(os.path.join(TEST_IMAGE_DIR, "spritegroup_16x24_1.png"), 'rb')
        self.spritegroup_1_img = Image.open(self.spritegroup_1_f)
        self.spritegroup_2_f = open(os.path.join(TEST_IMAGE_DIR, "spritegroup_16x24_2.png"), 'rb')
        self.spritegroup_2_img = Image.open(self.spritegroup_2_f)

    def tearDown(self):
        self.spritegroup_1_f.close()
        del self.spritegroup_1_img
        self.spritegroup_2_f.close()
        del self.spritegroup_2_img


class SwirlTestCase(TestCase):
    def setUp(self):
        self.swirl_1_f = open(os.path.join(TEST_IMAGE_DIR, "swirl_1.png"), 'rb')
        self.swirl_1_img = Image.open(self.swirl_1_f)

    def tearDown(self):
        self.swirl_1_f.close()
        del self.swirl_1_img
