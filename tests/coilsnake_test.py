import os
import tempfile

from PIL import Image
import mock


class CoilSnakeTestCase(object):
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")

    def setup_mock(self):
        self.mock = mock.Mock()

    def setup_temporary_wo_file(self):
        self.temporary_wo_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temporary_wo_file_name = self.temporary_wo_file.name

    def teardown_temporary_wo_file(self):
        if not self.temporary_wo_file.closed:
            self.temporary_wo_file.close()
        os.remove(self.temporary_wo_file_name)

    def setup_image(self):
        self.image = Image.open(os.path.join(self.TEST_DATA_DIR, "images", "tile_image_01.png"))

    def teardown_image(self):
        del self.image