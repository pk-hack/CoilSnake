import os
from nose.tools import assert_equal, assert_not_equal, assert_raises

from modules import Rom
import coilsnake_test


class TestRom(coilsnake_test.CoilSnakeTestCase):
    """
    A test class for the Rom module
    """

    def setUp(self):
        self.setup_temporary_wo_file()
        self.rom = Rom.Rom()
        self.rom2 = Rom.Rom()

    def teardown(self):
        self.teardown_temporary_wo_file()
        del self.rom
        del self.rom2

    def test_empty_rom(self):
        assert_equal(self.rom.type(), "Unknown")
        assert_equal(len(self.rom), 0)

    def test_load(self):
        self.rom.load(os.path.join(self.TEST_DATA_DIR, 'roms', '1kb_null.bin'))
        assert_equal(self.rom.type(), "Unknown")
        assert_equal(len(self.rom), 1024)

    def test_invalid_load(self):
        # Attempt to load a directory
        assert_raises(IOError, self.rom.load, self.TEST_DATA_DIR)
        # Attempt to load a nonexistent file
        assert_raises(IOError, self.rom.load, os.path.join(self.TEST_DATA_DIR, "doesnotexist.bin"))
        # Attempt to load a rom in a nonexistent directory
        assert_raises(IOError, self.rom.load, os.path.join(self.TEST_DATA_DIR, "dne", "dne.bin"))

    def test_read(self):
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_rand.bin"))
        assert_equal(self.rom[0], 0x25)
        assert_equal(self.rom[1023], 0x20)
        assert_raises(IndexError, self.rom.__getitem__, 1024)

        assert_equal(self.rom[0x3e3], 0xf4)
        assert_equal(self.rom.read(0x3e3), 0xf4)
        assert_raises(ValueError, self.rom.read, -1)
        assert_raises(ValueError, self.rom.read, 1024)
        assert_raises(ValueError, self.rom.read, 9999)

        assert_equal(len(self.rom.readList(0x25c, 0)), 0)
        assert_equal(self.rom.readList(0x25c, 1).tolist(), [0xa0])
        assert_equal(self.rom.readList(0x25c, 5).tolist(),
                     [0xa0, 0x0b, 0x71, 0x5d, 0x91])
        assert_equal(self.rom.readList(1022, 2).tolist(), [0x10, 0x20])
        assert_raises(ValueError, self.rom.readList, 0, -1)
        assert_raises(ValueError, self.rom.readList, -1, 0)
        assert_raises(ValueError, self.rom.readList, -1, -1)
        assert_raises(ValueError, self.rom.readList, 1024, 0)
        assert_raises(ValueError, self.rom.readList, 1024, -1)
        assert_raises(ValueError, self.rom.readList, 1022, 3)

        assert_equal(self.rom.readMulti(0x236, 1), 0xfb)
        assert_equal(self.rom.readMulti(0x236, 2), 0xe9fb)
        assert_equal(self.rom.readMulti(0x236, 4), 0x0273e9fb)
        assert_equal(self.rom.readMulti(1022, 2), 0x2010)
        assert_raises(ValueError, self.rom.readMulti, 0, -1)
        assert_raises(ValueError, self.rom.readMulti, -1, 0)
        assert_raises(ValueError, self.rom.readMulti, -1, -1)
        assert_raises(ValueError, self.rom.readMulti, 1024, 0)
        assert_raises(ValueError, self.rom.readMulti, 1024, -1)
        assert_raises(ValueError, self.rom.readMulti, 1022, 3)

    def test_write(self):
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_rand.bin"))
        self.rom[1] = 0xaa
        assert_equal(self.rom[0], 0x25)
        assert_equal(self.rom[1], 0xaa)
        assert_equal(self.rom[2], 0x38)
        assert_raises(IndexError, self.rom.__setitem__, 1024, 0xbb)

        self.rom.write(1, 0x5b)
        assert_equal(self.rom[0], 0x25)
        assert_equal(self.rom[1], 0x5b)
        assert_equal(self.rom[2], 0x38)
        assert_raises(ValueError, self.rom.write, -1, 0)
        assert_raises(ValueError, self.rom.write, 1024, 0)

        assert_raises(OverflowError, self.rom.write, 5, 0x1234)
        assert_raises(OverflowError, self.rom.write, 5, [0x1234, 0x4, 0x99])
        assert_raises(OverflowError, self.rom.__setitem__, 5, 0x100)

        self.rom.writeMulti(0x50, 0xa01234, 3)
        assert_equal(self.rom[0x50], 0x34)
        assert_equal(self.rom[0x51], 0x12)
        assert_equal(self.rom[0x52], 0xa0)

        self.rom.writeMulti(0x50, 0xddbbcc, 2)
        assert_equal(self.rom[0x50], 0xcc)
        assert_equal(self.rom[0x51], 0xbb)
        assert_equal(self.rom[0x52], 0xa0)

        self.rom.writeMulti(0x50, 0x0b, 3)
        assert_equal(self.rom[0x50], 0x0b)
        assert_equal(self.rom[0x51], 0x00)
        assert_equal(self.rom[0x52], 0x00)

    def test_read_and_write(self):
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_null.bin"))
        self.rom2 = Rom.Rom()
        self.rom2.load(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_null_01.bin"))
        assert_not_equal(self.rom, self.rom2)
        self.rom[1] = 1
        assert_equal(self.rom, self.rom2)

    def test_save(self):
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_null.bin"))
        self.rom[0x123] = 0xfe
        self.rom.save(self.temporary_wo_file_name)
        self.rom2.load(self.temporary_wo_file_name)
        assert_equal(self.rom, self.rom2)
        assert_equal(self.rom2[0x123], 0xfe)

        # Try to save a ROM to a directory which doesn't exist
        assert_raises(IOError, self.rom.save, os.path.join(self.TEST_DATA_DIR, "dne", "a.bin"))

    def test_romtype_detection(self):
        self.rom = Rom.Rom(os.path.join(self.COILSNAKE_RESOURCES_DIR, "romtypes.yaml"))
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "EB_fake_noheader.smc"))
        assert_equal(self.rom.type(), "Earthbound")
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "EB_fake_header.smc"))
        assert_equal(self.rom.type(), "Earthbound")
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "empty.smc"))
        assert_equal(self.rom.type(), "Unknown")
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_null.bin"))
        assert_equal(self.rom.type(), "Unknown")
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "EB_fake_header.smc"))
        assert_equal(self.rom.type(), "Earthbound")