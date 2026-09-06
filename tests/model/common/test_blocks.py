import os

from unittest import skipUnless

from coilsnake.model.common.blocks import Block, AllocatableBlock, Rom, ROM_TYPE_NAME_UNKNOWN
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR, earthbound_rom_available
from coilsnake.exceptions.common.exceptions import FileAccessError, OutOfBoundsError, InvalidArgumentError, \
    CouldNotAllocateError, NotEnoughUnallocatedSpaceError


class TestBlock(BaseTestCase):
    def setUp(self):
        self.block = Block()

    def tearDown(self):
        del self.block

    def test_baseline(self):
        pass

    def test_empty(self):
        self.assertEqual(len(self.block), 0)
        self.assertEqual(len(self.block.data), 0)

    def test_from_file(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_null.bin"))
        self.assertEqual(len(self.block), 1024)
        self.assertListEqual(self.block.to_list(), [0] * 1024)

    def test_from_file_unhappy(self):
        # Attempt to load a directory
        self.assertRaises(FileAccessError, self.block.from_file, TEST_DATA_DIR)
        # Attempt to load a nonexistent file
        self.assertRaises(FileAccessError, self.block.from_file, os.path.join(TEST_DATA_DIR, "doesnotexist.bin"))
        # Attempt to load a file in a nonexistent directory
        self.assertRaises(FileAccessError, self.block.from_file, os.path.join(TEST_DATA_DIR, "dne", "dne.bin"))

    def test_from_list(self):
        self.block.from_list([0, 1, 2, 3, 4, 5])
        self.assertEqual(len(self.block), 6)
        self.assertListEqual(self.block.to_list(), [0, 1, 2, 3, 4, 5])

        self.block.from_list([])
        self.assertEqual(len(self.block), 0)
        self.assertListEqual(self.block.to_list(), [])

        self.block.from_list([69])
        self.assertEqual(len(self.block), 1)
        self.assertListEqual(self.block.to_list(), [69])

    def test_getitem(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        self.assertEqual(self.block[0], 0x25)
        self.assertEqual(self.block[1023], 0x20)
        self.assertEqual(self.block[0x3e3], 0xf4)
        self.assertEqual(self.block[1023], self.block[-1])

        self.assertRaises(OutOfBoundsError, self.block.__getitem__, 1024)
        self.assertRaises(OutOfBoundsError, self.block.__getitem__, 9999)

    def test_getitem_slice(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        self.assertIsInstance(self.block[0:1], Block)

        self.assertListEqual(self.block[0:0].to_list(), [])
        self.assertListEqual(self.block[0x25c:0x25c].to_list(), [])
        self.assertListEqual(self.block[0x25c:0x25d].to_list(), [0xa0])
        self.assertListEqual(self.block[0x25c:0x25c + 5].to_list(), [0xa0, 0x0b, 0x71, 0x5d, 0x91])
        self.assertListEqual(self.block[0x25c:0x25c + 5].to_list(), [0xa0, 0x0b, 0x71, 0x5d, 0x91])
        self.assertListEqual(self.block[1022:1024].to_list(), [0x10, 0x20])

        self.assertRaises(InvalidArgumentError, self.block.__getitem__, slice(0, -1))
        self.assertRaises(OutOfBoundsError, self.block.__getitem__, slice(-2, -1))
        self.assertRaises(InvalidArgumentError, self.block.__getitem__, slice(1024, 0))
        self.assertRaises(InvalidArgumentError, self.block.__getitem__, slice(1024, -1))
        self.assertRaises(InvalidArgumentError, self.block.__getitem__, slice(1022, 3))

    def test_setitem(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        self.block[1] = 0xaa
        self.assertEqual(self.block[0], 0x25)
        self.assertEqual(self.block[1], 0xaa)
        self.assertEqual(self.block[2], 0x38)
        self.assertRaises(OutOfBoundsError, self.block.__setitem__, 1024, 0xbb)

        self.assertRaises(InvalidArgumentError, self.block.__setitem__, 5, 0x1234)
        self.assertRaises(InvalidArgumentError, self.block.__setitem__, 0, 0x100)
        self.assertRaises(InvalidArgumentError, self.block.__setitem__, 1, -1)

    def test_setitem_slice(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_rand.bin"))

        self.assertListEqual(self.block[0:3].to_list(), [0x25, 0x20, 0x38])
        self.block[0:3] = [0xeb, 0x15, 0x66]
        self.assertListEqual(self.block[0:3].to_list(), [0xeb, 0x15, 0x66])
        self.block[0:1024] = [5] * 1024
        self.assertEqual(self.block[0:1024].to_list(), [5] * 1024)

        self.assertRaises(InvalidArgumentError, self.block.__setitem__, slice(5, 0), [])
        self.assertRaises(InvalidArgumentError, self.block.__setitem__, slice(55, 55), [])
        self.assertRaises(OutOfBoundsError, self.block.__setitem__, slice(-1, 2), [])
        self.assertRaises(OutOfBoundsError, self.block.__setitem__, slice(1, 1025), [0] * 1024)
        self.assertRaises(OutOfBoundsError, self.block.__setitem__, slice(1024, 1025), [1])
        self.assertRaises(InvalidArgumentError, self.block.__setitem__, slice(0, 1), [])
        self.assertRaises(InvalidArgumentError, self.block.__setitem__, slice(0, 1), [1, 2, 3])
        self.assertRaises(InvalidArgumentError, self.block.__setitem__, slice(0, 5), [1, 2])

    def test_read_multi(self):
        self.block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])

        self.assertEqual(self.block.read_multi(0, 4), 0x1544a103)
        self.assertEqual(self.block.read_multi(1, 4), 0x921544a1)
        self.assertEqual(self.block.read_multi(1, 1), 0xa1)
        self.assertEqual(self.block.read_multi(1, 2), 0x44a1)
        self.assertEqual(self.block.read_multi(2, 3), 0x921544)
        self.assertEqual(self.block.read_multi(3, 3), 0x659215)
        self.assertEqual(self.block.read_multi(5, 1), 0x65)
        self.assertEqual(self.block.read_multi(0, 0), 0)
        self.assertEqual(self.block.read_multi(5, 0), 0)

        self.assertRaises(InvalidArgumentError, self.block.read_multi, 0, -1)
        self.assertRaises(InvalidArgumentError, self.block.read_multi, 0, -99)
        self.assertRaises(OutOfBoundsError, self.block.read_multi, -1, 3)
        self.assertRaises(OutOfBoundsError, self.block.read_multi, 7, 1)
        self.assertRaises(OutOfBoundsError, self.block.read_multi, 5, 2)
        self.assertRaises(OutOfBoundsError, self.block.read_multi, 0, 7)

    def test_write_multi(self):
        self.block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])

        self.block.write_multi(0, 0, 0)
        self.assertListEqual(self.block.to_list(), [0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])
        self.block.write_multi(0, 0xff, 1)
        self.assertListEqual(self.block.to_list(), [0xff, 0xa1, 0x44, 0x15, 0x92, 0x65])
        self.block.write_multi(1, 0xa1b2, 2)
        self.assertListEqual(self.block.to_list(), [0xff, 0xb2, 0xa1, 0x15, 0x92, 0x65])
        self.block.write_multi(2, 0x100000f, 4)
        self.assertListEqual(self.block.to_list(), [0xff, 0xb2, 0x0f, 0x00, 0x00, 0x01])

        self.assertRaises(InvalidArgumentError, self.block.write_multi, 0, 0, -1)
        self.assertRaises(OutOfBoundsError, self.block.write_multi, -1, 0, 1)
        self.assertRaises(OutOfBoundsError, self.block.write_multi, -1, 0, 1)
        self.assertRaises(OutOfBoundsError, self.block.write_multi, 0, 0, 7)
        self.assertRaises(OutOfBoundsError, self.block.write_multi, 1, 0, 6)
        self.assertRaises(OutOfBoundsError, self.block.write_multi, 3, 0, 4)

    def test_len(self):
        self.block.from_list([0x03, 0xa1, 0x44, 0x15, 0x92, 0x65])
        self.assertEqual(len(self.block), 6)
        self.block.from_list([])
        self.assertEqual(len(self.block), 0)


class TestAllocatableBlock(TestBlock):
    def setUp(self):
        self.block = AllocatableBlock()

    def test_getitem_slice_type(self):
        self.block.from_list([0] * 10)
        self.assertIsInstance(self.block[0:1], Block)

    def test_deallocate(self):
        self.block.from_list([0] * 10)
        self.assertRaises(InvalidArgumentError, self.block.deallocate, (1, 0))
        self.assertRaises(InvalidArgumentError, self.block.deallocate, (8, 2))
        self.assertRaises(OutOfBoundsError, self.block.deallocate, (-1, 0))
        self.assertRaises(OutOfBoundsError, self.block.deallocate, (-1, 9))
        self.assertRaises(OutOfBoundsError, self.block.deallocate, (-1, 10))
        self.assertRaises(OutOfBoundsError, self.block.deallocate, (0, 10))
        self.assertRaises(OutOfBoundsError, self.block.deallocate, (1, 11))
        self.assertRaises(OutOfBoundsError, self.block.deallocate, (9, 10))

        self.block.deallocate((0, 2))
        self.assertListEqual(self.block.unallocated_ranges, [(0, 2)])
        self.block.deallocate((4, 9))
        self.assertListEqual(self.block.unallocated_ranges, [(0, 2), (4, 9)])

    def test_mark_allocated(self):
        self.block.from_list([0] * 10)
        self.assertRaises(InvalidArgumentError, self.block.mark_allocated, (1, 0))
        self.assertRaises(InvalidArgumentError, self.block.mark_allocated, (8, 2))
        self.assertRaises(OutOfBoundsError, self.block.mark_allocated, (-1, 0))
        self.assertRaises(OutOfBoundsError, self.block.mark_allocated, (-1, 9))
        self.assertRaises(OutOfBoundsError, self.block.mark_allocated, (-1, 10))
        self.assertRaises(OutOfBoundsError, self.block.mark_allocated, (0, 10))
        self.assertRaises(OutOfBoundsError, self.block.mark_allocated, (1, 11))
        self.assertRaises(OutOfBoundsError, self.block.mark_allocated, (9, 10))
        self.assertRaises(CouldNotAllocateError, self.block.mark_allocated, (0, 1))

        self.block.from_list([0] * 100)
        self.block.deallocate((0, 99))
        self.assertListEqual(self.block.unallocated_ranges, [(0, 99)])
        # Mark middle as allocated, splitting the range into two
        self.block.mark_allocated((3, 44))
        self.assertListEqual(self.block.unallocated_ranges, [(0, 2), (45, 99)])
        # Again, but splitting a range into the smallest possible size
        self.block.mark_allocated((1, 1))
        self.assertListEqual(self.block.unallocated_ranges, [(0, 0), (2, 2), (45, 99)])
        # Destroying a range of size 1
        self.block.mark_allocated((0, 0))
        self.assertListEqual(self.block.unallocated_ranges, [(2, 2), (45, 99)])
        # Allocate from the beginning
        self.block.mark_allocated((45, 55))
        self.assertListEqual(self.block.unallocated_ranges, [(2, 2), (56, 99)])
        # Allocate from the end
        self.block.mark_allocated((80, 99))
        self.assertListEqual(self.block.unallocated_ranges, [(2, 2), (56, 79)])
        # Allocate an entire range
        self.block.mark_allocated((56, 79))
        self.assertListEqual(self.block.unallocated_ranges, [(2, 2)])

        self.block.from_list([0] * 0x50)
        self.block.unallocated_ranges = [(0, 0xf), (0x10, 0x1f), (0x20, 0x2f), (0x30, 0x3f)]
        # Mark a range free that spans multiple unallocated ranges
        self.block.mark_allocated((0x5, 0x25))
        self.assertListEqual(self.block.unallocated_ranges, [(0, 0x4), (0x26, 0x2f), (0x30, 0x3f)])
        self.block.mark_allocated((0x26, 0x31))
        self.assertListEqual(self.block.unallocated_ranges, [(0, 0x4), (0x32, 0x3f)])
        # Test invalid allocation
        self.assertRaises(CouldNotAllocateError, self.block.mark_allocated, (0x31, 0x32))
        self.assertRaises(CouldNotAllocateError, self.block.mark_allocated, (0x3f, 0x40))
        self.assertRaises(CouldNotAllocateError, self.block.mark_allocated, (0x31, 0x40))

    def test_get_unallocated_portions_of_range(self):
        self.block.from_list([0] * 50)
        self.block.deallocate((0, 10))
        self.assertListEqual(self.block.get_unallocated_portions_of_range((2, 8)), [(2, 8)])
        self.assertListEqual(self.block.get_unallocated_portions_of_range((5, 20)), [(5, 10)])
        self.block.deallocate((12, 14))
        self.assertListEqual(self.block.get_unallocated_portions_of_range((5, 20)), [(5, 10), (12, 14)])
        self.block.deallocate((18, 30))
        self.assertListEqual(self.block.get_unallocated_portions_of_range((5, 20)), [(5, 10), (12, 14), (18, 20)])
        self.assertListEqual(self.block.get_unallocated_portions_of_range((16, 32)), [(18, 30)])

    def test_is_unallocated(self):
        self.block.from_list([0] * 10)
        self.assertRaises(InvalidArgumentError, self.block.is_unallocated, (1, 0))
        self.assertRaises(InvalidArgumentError, self.block.is_unallocated, (8, 2))
        self.assertRaises(OutOfBoundsError, self.block.is_unallocated, (-1, 0))
        self.assertRaises(OutOfBoundsError, self.block.is_unallocated, (-1, 9))
        self.assertRaises(OutOfBoundsError, self.block.is_unallocated, (-1, 10))
        self.assertRaises(OutOfBoundsError, self.block.is_unallocated, (0, 10))
        self.assertRaises(OutOfBoundsError, self.block.is_unallocated, (1, 11))
        self.assertRaises(OutOfBoundsError, self.block.is_unallocated, (9, 10))

        self.assertFalse(self.block.is_unallocated((0, 0)))
        self.assertTrue(self.block.is_allocated((0, 0)))

        self.block.deallocate((1, 3))
        self.block.deallocate((4, 5))
        self.block.deallocate((9, 9))

        self.assertTrue(self.block.is_unallocated((1, 3)))
        self.assertTrue(self.block.is_unallocated((4, 5)))
        self.assertTrue(self.block.is_unallocated((9, 9)))
        self.assertTrue(self.block.is_unallocated((1, 1)))
        self.assertFalse(self.block.is_unallocated((0, 1)))
        self.assertFalse(self.block.is_unallocated((1, 4)))
        self.assertFalse(self.block.is_unallocated((0, 4)))
        self.assertFalse(self.block.is_unallocated((0, 9)))
        self.assertFalse(self.block.is_unallocated((1, 9)))

    def test_allocate(self):
        self.block.from_list([0] * 100)
        self.assertRaises(InvalidArgumentError, self.block.allocate)
        self.assertRaises(InvalidArgumentError, self.block.allocate, None, 0)
        self.assertRaises(InvalidArgumentError, self.block.allocate, None, -1)
        self.assertRaises(InvalidArgumentError, self.block.allocate, None, -10)
        self.assertRaises(InvalidArgumentError, self.block.allocate, [], None)
        self.assertRaises(InvalidArgumentError, self.block.allocate, [1], 2)

        # Allocate an entire range
        self.block.deallocate((0, 49))
        self.assertRaises(NotEnoughUnallocatedSpaceError, self.block.allocate, None, 51)
        offset = self.block.allocate(size=50)
        self.assertEqual(offset, 0)
        self.assertEqual(self.block.unallocated_ranges, [])

        # Allocate the beginning of a range
        self.block.deallocate((10, 39))
        offset = self.block.allocate(data=[0x12, 0x34, 0xef])
        self.assertEqual(offset, 10)
        self.assertEqual(self.block.unallocated_ranges, [(13, 39)])
        self.assertEqual(self.block[offset:offset + 3].to_list(), [0x12, 0x34, 0xef])
        self.assertNotEqual(self.block.to_list(), [0] * 100)
        self.block[offset:offset + 3] = [0] * 3
        self.assertEqual(self.block.to_list(), [0] * 100)

    def test_allocate_across_ranges(self):
        self.block.from_list([0] * 100)
        self.block.deallocate((0, 5))
        self.block.deallocate((6, 9))
        self.assertRaises(NotEnoughUnallocatedSpaceError, self.block.allocate, None, 10)


class TestRom(TestAllocatableBlock):
    def setUp(self):
        self.block = Rom()

    def test_detect_rom_type(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_noheader.smc"))
        self.assertEqual(self.block.type, "Earthbound")
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_header.smc"))
        self.assertEqual(self.block.type, "Earthbound")
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "empty.bin"))
        self.assertEqual(self.block.type, ROM_TYPE_NAME_UNKNOWN)
        self.block.from_file(os.path.join(TEST_DATA_DIR, "binaries", "1kb_null.bin"))
        self.assertEqual(self.block.type, ROM_TYPE_NAME_UNKNOWN)
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_header.smc"))
        self.assertEqual(self.block.type, "Earthbound")

    @skipUnless(earthbound_rom_available(), "real_EarthBound.smc is missing")
    def test_detect_rom_type_earthbound(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        self.assertEqual(self.block.type, "Earthbound")

    def test_add_header_unknown(self):
        self.block.from_list([0])
        with self.assertRaises(NotImplementedError):
            self.block.add_header()

    @skipUnless(earthbound_rom_available(), "real_EarthBound.smc is missing")
    def test_add_header_eb(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        self.assertEqual(self.block.size, 0x300000)
        self.block.add_header()
        self.assertEqual(self.block.size, 0x300200)
        self.assertEqual(len(self.block.data), 0x300200)
        self.assertEqual(self.block[0:0x200].to_list(), [0] * 0x200)

    def test_expand_unknown(self):
        self.block.from_list([0])
        with self.assertRaises(NotImplementedError):
            self.block.expand(0x123456)

    @skipUnless(earthbound_rom_available(), "real_EarthBound.smc is missing")
    def test_expand_eb(self):
        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        self.assertRaises(InvalidArgumentError, self.block.expand, 0x400200)
        self.assertRaises(InvalidArgumentError, self.block.expand, 0x300000)
        self.block.expand(0x400000)
        self.assertEqual(self.block.size, 0x400000)
        self.assertEqual(len(self.block.data), 0x400000)
        self.assertListEqual(self.block[0x300000:0x400000].to_list(), [0] * 0x100000)
        self.block.expand(0x600000)
        self.assertEqual(self.block.size, 0x600000)
        self.assertEqual(len(self.block.data), 0x600000)
        self.assertEqual(self.block[0xffd5], 0x25)
        self.assertEqual(self.block[0xffd7], 0x0d)

        self.block.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
        self.block.expand(0x600000)
        self.assertEqual(self.block.size, 0x600000)
        self.assertEqual(len(self.block.data), 0x600000)
        self.assertEqual(self.block[0xffd5], 0x25)
        self.assertEqual(self.block[0xffd7], 0x0d)
