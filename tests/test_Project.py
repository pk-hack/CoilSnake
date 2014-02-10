import unittest
import sys

import Project


sys.path.append('../')


class testProject(unittest.TestCase):
    """
    A test class for the Project module
    """

    def setUp(self):
        self.proj = Project.Project()

    def testEmptyProject(self):
        self.assertEqual(self.proj.type(), "Unknown")
        self.assertEqual(self.proj._resources, {})

    def testLoad(self):
        self.proj.load("projects/EB.csp")
        self.assertEqual(self.proj.type(), "Earthbound")
        f = self.proj.getResource("eb.MapModule", "map")
        self.assertEqual(f.name, "projects/eb.MapModule_map.dat")
        f.close()

        f = open("projects/Dummy.csp")
        self.proj.load(f)
        self.assertEqual(self.proj.type(), "DummyRomtype")
        self.assertEqual(self.proj._resources, {})

    def testLoadNew(self):
        self.proj.load("projects/dne.csp")
        self.assertEqual(self.proj.type(), "Unknown")
        self.assertEqual(self.proj._resources, {})

        self.proj.load("projects/EB.csp")
        self.proj.load("projects/dne.csp")
        self.assertEqual(self.proj.type(), "Unknown")
        self.assertEqual(self.proj._resources, {})

    def testLoadWithRomtype(self):
        self.proj.load("projects/EB.csp", "NotEarthbound")
        self.assertEqual(self.proj.type(), "NotEarthbound")
        self.assertEqual(self.proj._resources, {})

        self.proj.load("projects/EB.csp", "Earthbound")
        self.assertEqual(self.proj.type(), "Earthbound")
        f = self.proj.getResource("eb.MapModule", "map")
        self.assertEqual(f.name, "projects/eb.MapModule_map.dat")
        f.close()

        self.proj.load("projects/EB.csp", "NotEarthbound2")
        self.assertEqual(self.proj.type(), "NotEarthbound2")
        self.assertEqual(self.proj._resources, {})


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testProject))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
