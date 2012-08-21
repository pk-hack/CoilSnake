import os
import unittest

import sys
sys.path.append('../')

from modules import Rom

class testRom(unittest.TestCase):
    """
    A test class for the Rom module
    """

    def setUp(self):
        self.rom = Rom.Rom()
        self.rom2 = Rom.Rom()

    def testEmptyRom(self):
        self.assertEqual(self.rom.type(),"Unknown")
        self.assertEqual(len(self.rom), 0)

    def testLoad(self):
        self.rom.load("roms/1kb_null.bin")
        self.assertEqual(self.rom.type(),"Unknown")
        self.assertEqual(len(self.rom), 1024)

    def testInvalidLoad(self):
        # Attempt to load a directory
        self.assertRaises(IOError, self.rom.load, "tests")
        # Attempt to load a nonexistent file
        self.assertRaises(IOError, self.rom.load, "doesnotexist.bin")
        # Attempt to load a rom in a nonexistent directory
        self.assertRaises(IOError, self.rom.load, "dne/dne.bin")

    def testRead(self):
        self.rom.load("roms/1kb_rand.bin")
        self.assertEqual(self.rom[0], 0x25)
        self.assertEqual(self.rom[1023], 0x20)
        self.assertRaises(IndexError, self.rom.__getitem__, 1024)

        self.assertEqual(self.rom[0x3e3], 0xf4)
        self.assertEqual(self.rom.read(0x3e3), 0xf4)
        self.assertRaises(ValueError, self.rom.read, -1)
        self.assertRaises(ValueError, self.rom.read, 1024)
        self.assertRaises(ValueError, self.rom.read, 9999)

        self.assertEqual(len(self.rom.readList(0x25c, 0)), 0)
        self.assertEqual(self.rom.readList(0x25c, 1).tolist(), [ 0xa0 ])
        self.assertEqual(self.rom.readList(0x25c, 5).tolist(),
                [ 0xa0, 0x0b, 0x71, 0x5d, 0x91 ])
        self.assertEqual(self.rom.readList(1022, 2).tolist(), [ 0x10, 0x20 ])
        self.assertRaises(ValueError, self.rom.readList, 0, -1)
        self.assertRaises(ValueError, self.rom.readList, -1, 0)
        self.assertRaises(ValueError, self.rom.readList, -1, -1)
        self.assertRaises(ValueError, self.rom.readList, 1024, 0)
        self.assertRaises(ValueError, self.rom.readList, 1024, -1)
        self.assertRaises(ValueError, self.rom.readList, 1022, 3)

        self.assertEqual(self.rom.readMulti(0x236,1), 0xfb)
        self.assertEqual(self.rom.readMulti(0x236,2), 0xe9fb)
        self.assertEqual(self.rom.readMulti(0x236,4), 0x0273e9fb)
        self.assertEqual(self.rom.readMulti(1022,2), 0x2010)
        self.assertRaises(ValueError, self.rom.readMulti, 0, -1)
        self.assertRaises(ValueError, self.rom.readMulti, -1, 0)
        self.assertRaises(ValueError, self.rom.readMulti, -1, -1)
        self.assertRaises(ValueError, self.rom.readMulti, 1024, 0)
        self.assertRaises(ValueError, self.rom.readMulti, 1024, -1)
        self.assertRaises(ValueError, self.rom.readMulti, 1022, 3)

    def testWrite(self):
        self.rom.load("roms/1kb_rand.bin")
        self.rom[1] = 0xaa
        self.assertEqual(self.rom[0], 0x25)
        self.assertEqual(self.rom[1], 0xaa)
        self.assertEqual(self.rom[2], 0x38)
        self.assertRaises(IndexError, self.rom.__setitem__, 1024, 0xbb)

        self.rom.write(1, 0x5b)
        self.assertEqual(self.rom[0], 0x25)
        self.assertEqual(self.rom[1], 0x5b)
        self.assertEqual(self.rom[2], 0x38)
        self.assertRaises(ValueError, self.rom.write, -1, 0)
        self.assertRaises(ValueError, self.rom.write, 1024, 0)

        self.assertRaises(OverflowError, self.rom.write, 5, 0x1234)
        self.assertRaises(OverflowError, self.rom.write, 5, [0x1234, 0x4, 0x99])
        self.assertRaises(OverflowError, self.rom.__setitem__, 5, 0x100)

        self.rom.writeMulti(0x50, 0xa01234, 3)
        self.assertEqual(self.rom[0x50], 0x34)
        self.assertEqual(self.rom[0x51], 0x12)
        self.assertEqual(self.rom[0x52], 0xa0)

        self.rom.writeMulti(0x50, 0xddbbcc, 2)
        self.assertEqual(self.rom[0x50], 0xcc)
        self.assertEqual(self.rom[0x51], 0xbb)
        self.assertEqual(self.rom[0x52], 0xa0)

        self.rom.writeMulti(0x50, 0x0b, 3)
        self.assertEqual(self.rom[0x50], 0x0b)
        self.assertEqual(self.rom[0x51], 0x00)
        self.assertEqual(self.rom[0x52], 0x00) 

    def testRW(self):
        self.rom.load("roms/1kb_null.bin")
        self.rom2 = Rom.Rom()
        self.rom2.load("roms/1kb_null_01.bin")
        self.assertNotEqual(self.rom, self.rom2)
        self.rom[1] = 1
        self.assertEqual(self.rom, self.rom2)

    def testSave(self):
        if os.path.exists("roms/temp.bin"):
            os.remove("roms/temp.bin")
        self.rom.load("roms/1kb_null.bin")
        self.rom[0x123] = 0xfe
        self.rom.save("roms/temp.bin")
        self.rom2.load("roms/temp.bin")
        self.assertEqual(self.rom, self.rom2)
        self.assertEqual(self.rom2[0x123], 0xfe)
        os.remove("roms/temp.bin")

        self.assertRaises(IOError, self.rom.save, "dne/a.bin")

    def testRomtypes(self):
        self.rom = Rom.Rom("../romtypes.yaml")
        self.rom.load("roms/EB_fake_noheader.smc")
        self.assertEqual(self.rom.type(), "Earthbound")
        self.rom.load("roms/EB_fake_header.smc")
        self.assertEqual(self.rom.type(), "Earthbound")
        self.rom.load("roms/empty.smc")
        self.assertEqual(self.rom.type(), "Unknown")
        self.rom.load("roms/1kb_null.bin")
        self.assertEqual(self.rom.type(), "Unknown")
        self.rom.load("roms/EB_fake_header.smc")
        self.assertEqual(self.rom.type(), "Earthbound")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testRom))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
