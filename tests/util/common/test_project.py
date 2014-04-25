import os

from nose.tools import assert_equal

from coilsnake.util.common import project
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR


class TestProject(BaseTestCase):
    """
    A test class for the Project module
    """

    def setup(self):
        self.project = project.Project()

    def test_empty_project(self):
        assert_equal(self.project.romtype, "Unknown")
        assert_equal(self.project._resources, {})

    def test_load(self):
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"))
        assert_equal(self.project.romtype, "Earthbound")
        with self.project.get_resource("eb.MapModule", "map") as f:
            assert_equal(f.name, os.path.join(TEST_DATA_DIR, "projects", "eb.MapModule_map.dat"))

        with open(os.path.join(TEST_DATA_DIR, "projects", "Dummy.snake")) as f:
            self.project.load(f)
            assert_equal(self.project.romtype, "DummyRomtype")
            assert_equal(self.project._resources, {})

    def test_load_new(self):
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "dne.snake"))
        assert_equal(self.project.romtype, "Unknown")
        assert_equal(self.project._resources, {})

        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"))
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "dne.snake"))
        assert_equal(self.project.romtype, "Unknown")
        assert_equal(self.project._resources, {})

    def test_load_with_romtype(self):
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"), "NotEarthbound")
        assert_equal(self.project.romtype, "NotEarthbound")
        assert_equal(self.project._resources, {})

        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"), "Earthbound")
        assert_equal(self.project.romtype, "Earthbound")
        with self.project.get_resource("eb.MapModule", "map") as f:
            assert_equal(f.name, os.path.join(TEST_DATA_DIR, "projects", "eb.MapModule_map.dat"))

        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"), "NotEarthbound2")
        assert_equal(self.project.romtype, "NotEarthbound2")
        assert_equal(self.project._resources, {})