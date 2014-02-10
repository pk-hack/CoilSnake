from nose.tools import assert_equal, assert_not_equal, assert_raises, assert_list_equal
import os

from coilsnake.data import DataBlock, AllocatableDataBlock, Rom2
import coilsnake_test
from coilsnake.error import FileAccessError, OutOfBoundsError, InvalidArgumentError, ValueNotUnsignedByteError


class TestDataBlock(coilsnake_test.CoilSnakeTestCase):
    def setup(self):
        self.data_block = DataBlock()

    def teardown(self):
        del self.data_block

    def test_empty(self):
        assert_equal(len(self.data_block), 0)
        assert_equal(len(self.data_block.data), 0)

    def test_from_file(self):
        self.data_block.from_file(os.path.join(self.TEST_DATA_DIR, 'roms', '1kb_null.bin'))
        assert_equal(len(self.data_block), 1024)
        assert_list_equal(self.data_block.to_list(), [0]*1024)

    def test_from_file_unhappy(self):
        # Attempt to load a directory
        assert_raises(FileAccessError, self.data_block.from_file, self.TEST_DATA_DIR)
        # Attempt to load a nonexistent file
        assert_raises(FileAccessError, self.data_block.from_file, os.path.join(self.TEST_DATA_DIR, "doesnotexist.bin"))
        # Attempt to load a file in a nonexistent directory
        assert_raises(FileAccessError, self.data_block.from_file, os.path.join(self.TEST_DATA_DIR, "dne", "dne.bin"))

    def test_from_list(self):
        self.data_block.from_list([0, 1, 2, 3, 4, 5])
        assert_equal(len(self.data_block), 6)
        assert_list_equal(self.data_block.to_list(), [0, 1, 2, 3, 4, 5])

        self.data_block.from_list([])
        assert_equal(len(self.data_block), 0)
        assert_list_equal(self.data_block.to_list(), [])

        self.data_block.from_list([69])
        assert_equal(len(self.data_block), 1)
        assert_list_equal(self.data_block.to_list(), [69])
    
    def test_getitem(self):
        self.data_block.from_file(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_rand.bin"))

        assert_equal(self.data_block[0], 0x25)
        assert_equal(self.data_block[1023], 0x20)
        assert_equal(self.data_block[0x3e3], 0xf4)
        assert_equal(self.data_block[1023], self.data_block[-1])

        assert_raises(OutOfBoundsError, self.data_block.__getitem__, 1024)
        assert_raises(OutOfBoundsError, self.data_block.__getitem__, 9999)

    def test_getitem_slice(self):
        self.data_block.from_file(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_rand.bin"))

        assert_list_equal(self.data_block[0:0], [])
        assert_list_equal(self.data_block[0x25c:0x25c], [])
        assert_list_equal(self.data_block[0x25c:0x25d], [0xa0])
        assert_list_equal(self.data_block[0x25c:0x25c+5], [0xa0, 0x0b, 0x71, 0x5d, 0x91])
        assert_list_equal(self.data_block[0x25c:0x25c+5], [0xa0, 0x0b, 0x71, 0x5d, 0x91])
        assert_list_equal(self.data_block[1022:1024], [0x10, 0x20])

        assert_raises(InvalidArgumentError, self.data_block.__getitem__, slice(0, -1))
        assert_raises(OutOfBoundsError, self.data_block.__getitem__, slice(-2, -1))
        assert_raises(InvalidArgumentError, self.data_block.__getitem__, slice(1024, 0))
        assert_raises(InvalidArgumentError, self.data_block.__getitem__, slice(1024, -1))
        assert_raises(InvalidArgumentError, self.data_block.__getitem__, slice(1022, 3))

    def test_setitem(self):
        self.data_block.from_file(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_rand.bin"))

        self.data_block[1] = 0xaa
        assert_equal(self.data_block[0], 0x25)
        assert_equal(self.data_block[1], 0xaa)
        assert_equal(self.data_block[2], 0x38)
        assert_raises(OutOfBoundsError, self.data_block.__setitem__, 1024, 0xbb)

        assert_raises(ValueNotUnsignedByteError, self.data_block.__setitem__, 5, 0x1234)
        assert_raises(ValueNotUnsignedByteError, self.data_block.__setitem__, 0, 0x100)
        assert_raises(ValueNotUnsignedByteError, self.data_block.__setitem__, 1, -1)

    def test_setitem_slice(self):
        self.data_block.from_file(os.path.join(self.TEST_DATA_DIR, "roms", "1kb_rand.bin"))

        assert_list_equal(self.data_block[0:3], [0x25, 0x20, 0x38])
        self.data_block[0:3] = [0xeb, 0x15, 0x66]
        assert_list_equal(self.data_block[0:3], [0xeb, 0x15, 0x66])
        self.data_block[0:1024] = [5] * 1024
        assert_equal(self.data_block[0:1024], [5] * 1024)

        assert_raises(InvalidArgumentError, self.data_block.__setitem__, slice(5, 0), [])
        assert_raises(InvalidArgumentError, self.data_block.__setitem__, slice(55, 55), [])
        assert_raises(OutOfBoundsError, self.data_block.__setitem__, slice(-1, 2), [])
        assert_raises(OutOfBoundsError, self.data_block.__setitem__, slice(1, 1025), [0] * 1024)
        assert_raises(OutOfBoundsError, self.data_block.__setitem__, slice(1024, 1025), [1])
        assert_raises(InvalidArgumentError, self.data_block.__setitem__, slice(0, 1), [])
        assert_raises(InvalidArgumentError, self.data_block.__setitem__, slice(0, 1), [1, 2, 3])
        assert_raises(InvalidArgumentError, self.data_block.__setitem__, slice(0, 5), [1, 2])

    def test_read_multi(self):
        self.data_block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])

        assert_equal(self.data_block.read_multi(0, 4), 0x1544a103)
        assert_equal(self.data_block.read_multi(1, 4), 0x921544a1)
        assert_equal(self.data_block.read_multi(1, 1), 0xa1)
        assert_equal(self.data_block.read_multi(1, 2), 0x44a1)
        assert_equal(self.data_block.read_multi(2, 3), 0x921544)
        assert_equal(self.data_block.read_multi(5, 1), 0x65)
        assert_equal(self.data_block.read_multi(0, 0), 0)
        assert_equal(self.data_block.read_multi(5, 0), 0)

        assert_raises(InvalidArgumentError, self.data_block.read_multi, 0, -1)
        assert_raises(InvalidArgumentError, self.data_block.read_multi, 0, -99)
        assert_raises(OutOfBoundsError, self.data_block.read_multi, -1, 3)
        assert_raises(OutOfBoundsError, self.data_block.read_multi, 7, 1)
        assert_raises(OutOfBoundsError, self.data_block.read_multi, 5, 2)
        assert_raises(OutOfBoundsError, self.data_block.read_multi, 0, 7)

    def test_write_multi(self):
        self.data_block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])

        self.data_block.write_multi(0, 0, 0)
        assert_list_equal(self.data_block.to_list(), [0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])
        self.data_block.write_multi(0, 0xff, 1)
        assert_list_equal(self.data_block.to_list(), [0xff, 0xa1, 0x44, 0x15, 0x92, 0x65])
        self.data_block.write_multi(1, 0xa1b2, 2)
        assert_list_equal(self.data_block.to_list(), [0xff, 0xb2, 0xa1, 0x15, 0x92, 0x65])
        self.data_block.write_multi(2, 0x100000f, 4)
        assert_list_equal(self.data_block.to_list(), [0xff, 0xb2, 0x0f, 0x00, 0x00, 0x01])

        assert_raises(InvalidArgumentError, self.data_block.write_multi, 0, 0, -1)
        assert_raises(OutOfBoundsError, self.data_block.write_multi, -1, 0, 1)
        assert_raises(OutOfBoundsError, self.data_block.write_multi, -1, 0, 1)
        assert_raises(OutOfBoundsError, self.data_block.write_multi, 0, 0, 7)
        assert_raises(OutOfBoundsError, self.data_block.write_multi, 1, 0, 6)
        assert_raises(OutOfBoundsError, self.data_block.write_multi, 3, 0, 4)

    def test_len(self):
        self.data_block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])
        assert_equal(len(self.data_block), 6)
        self.data_block.from_list([])
        assert_equal(len(self.data_block), 0)


class TestAllocatableTestDataBlock(TestDataBlock):
    def setup(self):
        self.data_block = AllocatableDataBlock()