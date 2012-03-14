import array
import unittest

import sys
sys.path.append('../')

import modules.eb.EbModule
import Rom

class testEbModule(unittest.TestCase):
    """
    A test class for the EbModule module
    """

    def setUp(self):
        pass

    def testDecomp(self):
        r = Rom.Rom("../romtypes.yaml")
        r.load("roms/EarthBound.smc")
        tmp = modules.eb.EbModule.decomp(r, 0x2021a8)
        onett_map = array.array('B')
        onett_map.fromlist(tmp)

        onett_map_jhack = array.array('B')
        f = open("roms/onett_map_jhack.smc", 'r')
        onett_map_jhack.fromstring(f.read())
        f.close()

        self.assertEqual(len(onett_map), len(onett_map_jhack))
        self.assertEqual(onett_map, onett_map_jhack)

    def testComp(self):
        a = array.array('B')
        f = open('roms/onett_map_jhack.smc')
        a.fromstring(f.read())
        f.close()
        udata = a.tolist()
        cdata = modules.eb.EbModule.comp(udata)
        self.assertEqual(len(cdata), 10877)

        r = Rom.Rom("../romtypes.yaml")
        r.load("roms/EB_fake_32mbit.smc")
        r.write(0x300000, cdata)

        ucdata = modules.eb.EbModule.decomp(r, 0x300000)
        self.assertEqual(len(ucdata), len(udata))
        self.assertEqual(ucdata, udata)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testEbModule))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
