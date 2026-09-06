import os

from coilsnake.util.common import project
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR


class TestProject(BaseTestCase):
    """
    A test class for the Project module
    """

    def setUp(self):
        self.project = project.Project()

    def test_empty_project(self):
        self.assertEqual(self.project.romtype, "Unknown")
        self.assertEqual(self.project._resources, {})

    def test_load(self):
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"))
        self.assertEqual(self.project.romtype, "Earthbound")
        with self.project.get_resource("eb.MapModule", "map") as f:
            self.assertEqual(f.name, os.path.join(TEST_DATA_DIR, "projects", "eb.MapModule_map.dat"))

        with open(os.path.join(TEST_DATA_DIR, "projects", "Dummy.snake")) as f:
            self.project.load(f)
            self.assertEqual(self.project.romtype, "DummyRomtype")
            self.assertEqual(self.project._resources, {})

    def test_load_new(self):
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "dne.snake"))
        self.assertEqual(self.project.romtype, "Unknown")
        self.assertEqual(self.project._resources, {})

        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"))
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "dne.snake"))
        self.assertEqual(self.project.romtype, "Unknown")
        self.assertEqual(self.project._resources, {})

    def test_load_with_romtype(self):
        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"), "NotEarthbound")
        self.assertEqual(self.project.romtype, "NotEarthbound")
        self.assertEqual(self.project._resources, {})

        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"), "Earthbound")
        self.assertEqual(self.project.romtype, "Earthbound")
        with self.project.get_resource("eb.MapModule", "map") as f:
            self.assertEqual(f.name, os.path.join(TEST_DATA_DIR, "projects", "eb.MapModule_map.dat"))

        self.project.load(os.path.join(TEST_DATA_DIR, "projects", "EB.snake"), "NotEarthbound2")
        self.assertEqual(self.project.romtype, "NotEarthbound2")
        self.assertEqual(self.project._resources, {})
