import os

from nose.tools import assert_equal, assert_not_equal, assert_raises, assert_list_equal, assert_false, assert_true, \
    assert_is_instance
from nose.tools.nontrivial import raises

from coilsnake.model.common.blocks import Block, AllocatableBlock, Rom, ROM_TYPE_NAME_UNKNOWN
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR
from coilsnake.exceptions.common.exceptions import FileAccessError, OutOfBoundsError, InvalidArgumentError, \
    CouldNotAllocateError, NotEnoughUnallocatedSpaceError


class TestBlock(BaseTestCase):
    def setup(self):
        self.block = Block()

    def teardown(self):
        del self.block

    def test_baseline(self):
        pass

    def test_empty(self):
        assert_equal(len(self.block), 0)
        assert_equal(len(self.block.data), 0)

    def test_from_file(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_null.bin"))
        assert_equal(len(self.block), 1024)
        assert_list_equal(self.block.to_list(), [0] * 1024)

    def test_from_file_unhappy(self):
        # Attempt to load a directory
        assert_raises(FileAccessError, self.block.from_file, TEST_DATA_DIR)
        # Attempt to load a nonexistent file
        assert_raises(FileAccessError, self.block.from_file, os.path.join(TEST_DATA_DIR, "doesnotexist.bin"))
        # Attempt to load a file in a nonexistent directory
        assert_raises(FileAccessError, self.block.from_file, os.path.join(TEST_DATA_DIR, "dne", "dne.bin"))

    def test_from_list(self):
        self.block.from_list([0, 1, 2, 3, 4, 5])
        assert_equal(len(self.block), 6)
        assert_list_equal(self.block.to_list(), [0, 1, 2, 3, 4, 5])

        self.block.from_list([])
        assert_equal(len(self.block), 0)
        assert_list_equal(self.block.to_list(), [])

        self.block.from_list([69])
        assert_equal(len(self.block), 1)
        assert_list_equal(self.block.to_list(), [69])

    def test_getitem(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        assert_equal(self.block[0], 0x25)
        assert_equal(self.block[1023], 0x20)
        assert_equal(self.block[0x3e3], 0xf4)
        assert_equal(self.block[1023], self.block[-1])

        assert_raises(OutOfBoundsError, self.block.__getitem__, 1024)
        assert_raises(OutOfBoundsError, self.block.__getitem__, 9999)

    def test_getitem_slice(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        assert_is_instance(self.block[0:1], Block)

        assert_list_equal(self.block[0:0].to_list(), [])
        assert_list_equal(self.block[0x25c:0x25c].to_list(), [])
        assert_list_equal(self.block[0x25c:0x25d].to_list(), [0xa0])
        assert_list_equal(self.block[0x25c:0x25c + 5].to_list(), [0xa0, 0x0b, 0x71, 0x5d, 0x91])
        assert_list_equal(self.block[0x25c:0x25c + 5].to_list(), [0xa0, 0x0b, 0x71, 0x5d, 0x91])
        assert_list_equal(self.block[1022:1024].to_list(), [0x10, 0x20])

        assert_raises(InvalidArgumentError, self.block.__getitem__, slice(0, -1))
        assert_raises(OutOfBoundsError, self.block.__getitem__, slice(-2, -1))
        assert_raises(InvalidArgumentError, self.block.__getitem__, slice(1024, 0))
        assert_raises(InvalidArgumentError, self.block.__getitem__, slice(1024, -1))
        assert_raises(InvalidArgumentError, self.block.__getitem__, slice(1022, 3))

    def test_setitem(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        self.block[1] = 0xaa
        assert_equal(self.block[0], 0x25)
        assert_equal(self.block[1], 0xaa)
        assert_equal(self.block[2], 0x38)
        assert_raises(OutOfBoundsError, self.block.__setitem__, 1024, 0xbb)

        assert_raises(InvalidArgumentError, self.block.__setitem__, 5, 0x1234)
        assert_raises(InvalidArgumentError, self.block.__setitem__, 0, 0x100)
        assert_raises(InvalidArgumentError, self.block.__setitem__, 1, -1)

    def test_setitem_slice(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        assert_list_equal(self.block[0:3].to_list(), [0x25, 0x20, 0x38])
        self.block[0:3] = [0xeb, 0x15, 0x66]
        assert_list_equal(self.block[0:3].to_list(), [0xeb, 0x15, 0x66])
        self.block[0:1024] = [5] * 1024
        assert_equal(self.block[0:1024].to_list(), [5] * 1024)

        assert_raises(InvalidArgumentError, self.block.__setitem__, slice(5, 0), [])
        assert_raises(InvalidArgumentError, self.block.__setitem__, slice(55, 55), [])
        assert_raises(OutOfBoundsError, self.block.__setitem__, slice(-1, 2), [])
        assert_raises(OutOfBoundsError, self.block.__setitem__, slice(1, 1025), [0] * 1024)
        assert_raises(OutOfBoundsError, self.block.__setitem__, slice(1024, 1025), [1])
        assert_raises(InvalidArgumentError, self.block.__setitem__, slice(0, 1), [])
        assert_raises(InvalidArgumentError, self.block.__setitem__, slice(0, 1), [1, 2, 3])
        assert_raises(InvalidArgumentError, self.block.__setitem__, slice(0, 5), [1, 2])

    def test_read_multi(self):
        self.block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])

        assert_equal(self.block.read_multi(0, 4), 0x1544a103)
        assert_equal(self.block.read_multi(1, 4), 0x921544a1)
        assert_equal(self.block.read_multi(1, 1), 0xa1)
        assert_equal(self.block.read_multi(1, 2), 0x44a1)
        assert_equal(self.block.read_multi(2, 3), 0x921544)
        assert_equal(self.block.read_multi(3, 3), 0x659215)
        assert_equal(self.block.read_multi(5, 1), 0x65)
        assert_equal(self.block.read_multi(0, 0), 0)
        assert_equal(self.block.read_multi(5, 0), 0)

        assert_raises(InvalidArgumentError, self.block.read_multi, 0, -1)
        assert_raises(InvalidArgumentError, self.block.read_multi, 0, -99)
        assert_raises(OutOfBoundsError, self.block.read_multi, -1, 3)
        assert_raises(OutOfBoundsError, self.block.read_multi, 7, 1)
        assert_raises(OutOfBoundsError, self.block.read_multi, 5, 2)
        assert_raises(OutOfBoundsError, self.block.read_multi, 0, 7)

    def test_write_multi(self):
        self.block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])

        self.block.write_multi(0, 0, 0)
        assert_list_equal(self.block.to_list(), [0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])
        self.block.write_multi(0, 0xff, 1)
        assert_list_equal(self.block.to_list(), [0xff, 0xa1, 0x44, 0x15, 0x92, 0x65])
        self.block.write_multi(1, 0xa1b2, 2)
        assert_list_equal(self.block.to_list(), [0xff, 0xb2, 0xa1, 0x15, 0x92, 0x65])
        self.block.write_multi(2, 0x100000f, 4)
        assert_list_equal(self.block.to_list(), [0xff, 0xb2, 0x0f, 0x00, 0x00, 0x01])

        assert_raises(InvalidArgumentError, self.block.write_multi, 0, 0, -1)
        assert_raises(OutOfBoundsError, self.block.write_multi, -1, 0, 1)
        assert_raises(OutOfBoundsError, self.block.write_multi, -1, 0, 1)
        assert_raises(OutOfBoundsError, self.block.write_multi, 0, 0, 7)
        assert_raises(OutOfBoundsError, self.block.write_multi, 1, 0, 6)
        assert_raises(OutOfBoundsError, self.block.write_multi, 3, 0, 4)

    def test_len(self):
        self.block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])
        assert_equal(len(self.block), 6)
        self.block.from_list([])
        assert_equal(len(self.block), 0)


class TestAllocatableBlock(TestBlock):
    def setup(self):
        self.block = AllocatableBlock()

    def test_getitem_slice_type(self):
        self.block.from_list([0] * 10)
        assert_is_instance(self.block[0:1], Block)

    def test_deallocate(self):
        self.block.from_list([0] * 10)
        assert_raises(InvalidArgumentError, self.block.deallocate, (1, 0))
        assert_raises(InvalidArgumentError, self.block.deallocate, (8, 2))
        assert_raises(OutOfBoundsError, self.block.deallocate, (-1, 0))
        assert_raises(OutOfBoundsError, self.block.deallocate, (-1, 9))
        assert_raises(OutOfBoundsError, self.block.deallocate, (-1, 10))
        assert_raises(OutOfBoundsError, self.block.deallocate, (0, 10))
        assert_raises(OutOfBoundsError, self.block.deallocate, (1, 11))
        assert_raises(OutOfBoundsError, self.block.deallocate, (9, 10))

        self.block.deallocate((0, 2))
        assert_list_equal(self.block.unallocated_ranges, [(0, 2)])
        self.block.deallocate((4, 9))
        assert_list_equal(self.block.unallocated_ranges, [(0, 2), (4, 9)])

    def test_mark_allocated(self):
        self.block.from_list([0] * 10)
        assert_raises(InvalidArgumentError, self.block.mark_allocated, (1, 0))
        assert_raises(InvalidArgumentError, self.block.mark_allocated, (8, 2))
        assert_raises(OutOfBoundsError, self.block.mark_allocated, (-1, 0))
        assert_raises(OutOfBoundsError, self.block.mark_allocated, (-1, 9))
        assert_raises(OutOfBoundsError, self.block.mark_allocated, (-1, 10))
        assert_raises(OutOfBoundsError, self.block.mark_allocated, (0, 10))
        assert_raises(OutOfBoundsError, self.block.mark_allocated, (1, 11))
        assert_raises(OutOfBoundsError, self.block.mark_allocated, (9, 10))
        assert_raises(CouldNotAllocateError, self.block.mark_allocated, (0, 1))

        self.block.from_list([0] * 100)
        self.block.deallocate((0, 99))
        assert_list_equal(self.block.unallocated_ranges, [(0, 99)])
        # Mark middle as allocated, splitting the range into two
        self.block.mark_allocated((3, 44))
        assert_list_equal(self.block.unallocated_ranges, [(0, 2), (45, 99)])
        # Again, but splitting a range into the smallest possible size
        self.block.mark_allocated((1, 1))
        assert_list_equal(self.block.unallocated_ranges, [(0, 0), (2, 2), (45, 99)])
        # Destroying a range of size 1
        self.block.mark_allocated((0, 0))
        assert_list_equal(self.block.unallocated_ranges, [(2, 2), (45, 99)])
        # Allocate from the beginning
        self.block.mark_allocated((45, 55))
        assert_list_equal(self.block.unallocated_ranges, [(2, 2), (56, 99)])
        # Allocate from the end
        self.block.mark_allocated((80, 99))
        assert_list_equal(self.block.unallocated_ranges, [(2, 2), (56, 79)])
        # Allocate an entire range
        self.block.mark_allocated((56, 79))
        assert_list_equal(self.block.unallocated_ranges, [(2, 2)])

        self.block.from_list([0] * 0x50)
        self.block.unallocated_ranges = [(0, 0xf), (0x10, 0x1f), (0x20, 0x2f), (0x30, 0x3f)]
        # Mark a range free that spans multiple unallocated ranges
        self.block.mark_allocated((0x5, 0x25))
        assert_list_equal(self.block.unallocated_ranges, [(0, 0x4), (0x26, 0x2f), (0x30, 0x3f)])
        self.block.mark_allocated((0x26, 0x31))
        assert_list_equal(self.block.unallocated_ranges, [(0, 0x4), (0x32, 0x3f)])
        # Test invalid allocation
        assert_raises(CouldNotAllocateError, self.block.mark_allocated, (0x31, 0x32))
        assert_raises(CouldNotAllocateError, self.block.mark_allocated, (0x3f, 0x40))
        assert_raises(CouldNotAllocateError, self.block.mark_allocated, (0x31, 0x40))

    def test_get_unallocated_portions_of_range(self):
        self.block.from_list([0] * 50)
        self.block.deallocate((0, 10))
        assert_list_equal(self.block.get_unallocated_portions_of_range((2, 8)), [(2, 8)])
        assert_list_equal(self.block.get_unallocated_portions_of_range((5, 20)), [(5, 10)])
        self.block.deallocate((12, 14))
        assert_list_equal(self.block.get_unallocated_portions_of_range((5, 20)), [(5, 10), (12, 14)])
        self.block.deallocate((18, 30))
        assert_list_equal(self.block.get_unallocated_portions_of_range((5, 20)), [(5, 10), (12, 14), (18, 20)])
        assert_list_equal(self.block.get_unallocated_portions_of_range((16, 32)), [(18, 30)])

    def test_is_unallocated(self):
        self.block.from_list([0] * 10)
        assert_raises(InvalidArgumentError, self.block.is_unallocated, (1, 0))
        assert_raises(InvalidArgumentError, self.block.is_unallocated, (8, 2))
        assert_raises(OutOfBoundsError, self.block.is_unallocated, (-1, 0))
        assert_raises(OutOfBoundsError, self.block.is_unallocated, (-1, 9))
        assert_raises(OutOfBoundsError, self.block.is_unallocated, (-1, 10))
        assert_raises(OutOfBoundsError, self.block.is_unallocated, (0, 10))
        assert_raises(OutOfBoundsError, self.block.is_unallocated, (1, 11))
        assert_raises(OutOfBoundsError, self.block.is_unallocated, (9, 10))

        assert_false(self.block.is_unallocated((0, 0)))
        assert_true(self.block.is_allocated((0, 0)))

        self.block.deallocate((1, 3))
        self.block.deallocate((4, 5))
        self.block.deallocate((9, 9))

        assert_true(self.block.is_unallocated((1, 3)))
        assert_true(self.block.is_unallocated((4, 5)))
        assert_true(self.block.is_unallocated((9, 9)))
        assert_true(self.block.is_unallocated((1, 1)))
        assert_false(self.block.is_unallocated((0, 1)))
        assert_false(self.block.is_unallocated((1, 4)))
        assert_false(self.block.is_unallocated((0, 4)))
        assert_false(self.block.is_unallocated((0, 9)))
        assert_false(self.block.is_unallocated((1, 9)))

    def test_allocate(self):
        self.block.from_list([0] * 100)
        assert_raises(InvalidArgumentError, self.block.allocate)
        assert_raises(InvalidArgumentError, self.block.allocate, None, 0)
        assert_raises(InvalidArgumentError, self.block.allocate, None, -1)
        assert_raises(InvalidArgumentError, self.block.allocate, None, -10)
        assert_raises(InvalidArgumentError, self.block.allocate, [], None)
        assert_raises(InvalidArgumentError, self.block.allocate, [1], 2)

        # Allocate an entire range
        self.block.deallocate((0, 49))
        assert_raises(NotEnoughUnallocatedSpaceError, self.block.allocate, None, 51)
        offset = self.block.allocate(size=50)
        assert_equal(offset, 0)
        assert_equal(self.block.unallocated_ranges, [])

        # Allocate the beginning of a range
        self.block.deallocate((10, 39))
        offset = self.block.allocate(data=[0x12, 0x34, 0xef])
        assert_equal(offset, 10)
        assert_equal(self.block.unallocated_ranges, [(13, 39)])
        assert_equal(self.block[offset:offset + 3].to_list(), [0x12, 0x34, 0xef])
        assert_not_equal(self.block.to_list(), [0] * 100)
        self.block[offset:offset + 3] = [0] * 3
        assert_equal(self.block.to_list(), [0] * 100)

    def test_allocate_across_ranges(self):
        self.block.from_list([0] * 100)
        self.block.deallocate((0, 5))
        self.block.deallocate((6, 9))
        assert_raises(NotEnoughUnallocatedSpaceError, self.block.allocate, None, 10)


class TestRom(TestAllocatableBlock):
    def setup(self):
        self.block = Rom()

    def test_detect_rom_type(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_noheader.smc"))
        assert_equal(self.block.type, "Earthbound")
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_header.smc"))
        assert_equal(self.block.type, "Earthbound")
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "empty.bin"))
        assert_equal(self.block.type, ROM_TYPE_NAME_UNKNOWN)
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_null.bin"))
        assert_equal(self.block.type, ROM_TYPE_NAME_UNKNOWN)
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_header.smc"))
        assert_equal(self.block.type, "Earthbound")
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        assert_equal(self.block.type, "Earthbound")

    @raises(NotImplementedError)
    def test_add_header_unknown(self):
        self.block.from_list([0])
        self.block.add_header()

    def test_add_header_eb(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        assert_equal(self.block.size, 0x300000)
        self.block.add_header()
        assert_equal(self.block.size, 0x300200)
        assert_equal(len(self.block.data), 0x300200)
        assert_equal(self.block[0:0x200].to_list(), [0] * 0x200)

    @raises(NotImplementedError)
    def test_expand_unknown(self):
        self.block.from_list([0])
        self.block.expand(0x123456)

    def test_expand_eb(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        assert_raises(InvalidArgumentError, self.block.expand, 0x400200)
        assert_raises(InvalidArgumentError, self.block.expand, 0x300000)
        self.block.expand(0x400000)
        assert_equal(self.block.size, 0x400000)
        assert_equal(len(self.block.data), 0x400000)
        assert_list_equal(self.block[0x300000:0x400000].to_list(), [0] * 0x100000)
        self.block.expand(0x600000)
        assert_equal(self.block.size, 0x600000)
        assert_equal(len(self.block.data), 0x600000)
        assert_equal(self.block[0xffd5], 0x25)
        assert_equal(self.block[0xffd7], 0x0d)

        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        self.block.expand(0x600000)
        assert_equal(self.block.size, 0x600000)
        assert_equal(len(self.block.data), 0x600000)
        assert_equal(self.block[0xffd5], 0x25)
        assert_equal(self.block[0xffd7], 0x0d)