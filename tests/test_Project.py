import os
from nose.tools import assert_equal, assert_not_equal, assert_raises

from coilsnake import Project
import coilsnake_test


class testProject(coilsnake_test.CoilSnakeTestCase):
    """
    A test class for the Project module
    """

    def setUp(self):
        self.proj = Project.Project()

    def testEmptyProject(self):
        assert_equal(self.proj.type(), "Unknown")
        assert_equal(self.proj._resources, {})

    def testLoad(self):
        self.proj.load(os.path.join(self.TEST_DATA_DIR, "projects", "EB.snake"))
        assert_equal(self.proj.type(), "Earthbound")
        with self.proj.getResource("eb.MapModule", "map") as f:
            assert_equal(f.name, os.path.join(self.TEST_DATA_DIR, "projects", "eb.MapModule_map.dat"))

        with open(os.path.join(self.TEST_DATA_DIR, "projects", "Dummy.snake")) as f:
            self.proj.load(f)
            assert_equal(self.proj.type(), "DummyRomtype")
            assert_equal(self.proj._resources, {})

    def testLoadNew(self):
        self.proj.load(os.path.join(self.TEST_DATA_DIR, "projects", "dne.snake"))
        assert_equal(self.proj.type(), "Unknown")
        assert_equal(self.proj._resources, {})

        self.proj.load(os.path.join(self.TEST_DATA_DIR, "projects", "EB.snake"))
        self.proj.load(os.path.join(self.TEST_DATA_DIR, "projects", "dne.snake"))
        assert_equal(self.proj.type(), "Unknown")
        assert_equal(self.proj._resources, {})

    def testLoadWithRomtype(self):
        self.proj.load(os.path.join(self.TEST_DATA_DIR, "projects", "EB.snake"), "NotEarthbound")
        assert_equal(self.proj.type(), "NotEarthbound")
        assert_equal(self.proj._resources, {})

        self.proj.load(os.path.join(self.TEST_DATA_DIR, "projects", "EB.snake"), "Earthbound")
        assert_equal(self.proj.type(), "Earthbound")
        with self.proj.getResource("eb.MapModule", "map") as f:
            assert_equal(f.name, os.path.join(self.TEST_DATA_DIR, "projects", "eb.MapModule_map.dat"))

        self.proj.load(os.path.join(self.TEST_DATA_DIR, "projects", "EB.snake"), "NotEarthbound2")
        assert_equal(self.proj.type(), "NotEarthbound2")
        assert_equal(self.proj._resources, {})