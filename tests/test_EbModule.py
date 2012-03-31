import array
import unittest

import sys
sys.path.append('../')

import modules.eb.EbModule
import modules.eb.NativeComp
import Rom

class testEbModule(unittest.TestCase):
    """
    A test class for the EbModule module
    """

    def setUp(self):
        self.rom = Rom.Rom("../romtypes.yaml")
        self.rom.load("roms/EB_fake_24mbit.smc")

    def _testDecomp(self, decompFunc):
        r = Rom.Rom("../romtypes.yaml")
        r.load("roms/EarthBound.smc")
        tmp = decompFunc(r, 0x2021a8)
        onett_map = array.array('B')
        onett_map.fromlist(tmp)

        onett_map_jhack = array.array('B')
        f = open("roms/onett_map_jhack.smc", 'r')
        onett_map_jhack.fromstring(f.read())
        f.close()

        self.assertEqual(len(onett_map), len(onett_map_jhack))
        self.assertEqual(onett_map, onett_map_jhack)

    def _testComp(self, compFunc, decompFunc):
        a = array.array('B')
        f = open('roms/onett_map_jhack.smc')
        a.fromstring(f.read())
        f.close()
        udata = a.tolist()
        cdata = compFunc(udata)
        self.assertEqual(len(cdata), 10877)

        r = Rom.Rom("../romtypes.yaml")
        r.load("roms/EB_fake_32mbit.smc")
        r.write(0x300000, cdata)

        ucdata = decompFunc(r, 0x300000)
        self.assertEqual(len(ucdata), len(udata))
        self.assertEqual(ucdata, udata)

    def _testPythonComp(self):
        self._testComp(modules.eb.EbModule._comp,
                modules.eb.EbModule.decomp)

    def _testPythonDecomp(self):
        self._testDecomp(modules.eb.EbModule._decomp)

    def testNativeComp(self):
        self._testComp(modules.eb.NativeComp.comp,
                modules.eb.EbModule._decomp)

    def testNativeDecomp(self):
        self._testDecomp(modules.eb.NativeComp.decomp)

    def testDefaultComp(self):
        self._testComp(modules.eb.EbModule.comp,
                modules.eb.EbModule.decomp)

    def testDefaultDecomp(self):
        self._testDecomp(modules.eb.EbModule.decomp)

    def testPaletteIO(self):
        c = (48, 32, 16)
        modules.eb.EbModule.writePaletteColor(self.rom, 0, c)
        c2 = modules.eb.EbModule.readPaletteColor(self.rom, 0)
        self.assertEqual(c, c2)

        pal = [(176, 232, 24), (40, 152, 88), (216, 208, 136), (160, 0, 88),
                (56, 40, 96), (112, 16, 240), (112, 64, 88), (48, 88, 0), (56,
                    136, 64), (176, 104, 144), (0, 48, 224), (224, 224, 136),
                (56, 248, 168), (56, 216, 80), (184, 48, 248), (200, 112, 32)]
        modules.eb.EbModule.writePalette(self.rom, 0, pal)
        pal2 = modules.eb.EbModule.readPalette(self.rom, 0, 16)
        self.assertEqual(pal, pal2)

    def testAsmPointerIO(self):
        ptr = modules.eb.EbModule.readAsmPointer(self.rom, 0xeefb)
        self.assertEqual(ptr, 0xe14f2a)

        modules.eb.EbModule.writeAsmPointer(self.rom, 0, 0xabcdef01)
        self.assertEqual(self.rom.readList(0, 8),
                [ 0x0, 0x01, 0xef, 0x0, 0x0, 0x0, 0xcd, 0xab ])

        ptr2 = modules.eb.EbModule.readAsmPointer(self.rom, 0)
        self.assertEqual(0xabcdef01, ptr2)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testEbModule))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
