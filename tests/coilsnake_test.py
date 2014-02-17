import os
import tempfile

from PIL import Image


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
TEST_IMAGE_DIR = os.path.join(TEST_DATA_DIR, "images")


class BaseTestCase(object):
    def test_baseline(self):
        pass


class TemporaryWritableFileTestCase(object):
    def setup(self):
        self.temporary_wo_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temporary_wo_file_name = self.temporary_wo_file.name

    def teardown(self):
        if not self.temporary_wo_file.closed:
            self.temporary_wo_file.close()
        os.remove(self.temporary_wo_file_name)


class TilesetImageTestCase(object):
    def setup(self):
        self.tile_image_01_fp = open(os.path.join(TEST_IMAGE_DIR, "tile_image_01.png"), 'r')
        self.tile_image_01 = Image.open(self.tile_image_01_fp)

    def teardown(self):
        self.tile_image_01_fp.close()
        del self.tile_image_01
