from nose.tools import assert_equal, assert_raises, assert_list_equal, assert_false, assert_true

from coilsnake.exceptions.common.exceptions import OutOfBoundsError, InvalidArgumentError, \
    CouldNotAllocateError, NotEnoughUnallocatedSpaceError
from coilsnake.util.common.memory import MemoryAllocationManager
from tests.coilsnake_test import BaseTestCase


class TestMemoryAllocationManager(BaseTestCase):
    def test_deallocate(self):
        mam = MemoryAllocationManager(size=10)
        assert_raises(InvalidArgumentError, mam.deallocate, (1, 0))
        assert_raises(InvalidArgumentError, mam.deallocate, (8, 2))
        assert_raises(OutOfBoundsError, mam.deallocate, (-1, 0))
        assert_raises(OutOfBoundsError, mam.deallocate, (-1, 9))
        assert_raises(OutOfBoundsError, mam.deallocate, (-1, 10))
        assert_raises(OutOfBoundsError, mam.deallocate, (0, 10))
        assert_raises(OutOfBoundsError, mam.deallocate, (1, 11))
        assert_raises(OutOfBoundsError, mam.deallocate, (9, 10))

        mam.deallocate((0, 2))
        assert_list_equal(mam.unallocated_ranges, [(0, 2)])
        mam.deallocate((4, 9))
        assert_list_equal(mam.unallocated_ranges, [(0, 2), (4, 9)])

    def test_set_as_allocated(self):
        mam = MemoryAllocationManager(size=10)
        assert_raises(InvalidArgumentError, mam.set_as_allocated, (1, 0))
        assert_raises(InvalidArgumentError, mam.set_as_allocated, (8, 2))
        assert_raises(OutOfBoundsError, mam.set_as_allocated, (-1, 0))
        assert_raises(OutOfBoundsError, mam.set_as_allocated, (-1, 9))
        assert_raises(OutOfBoundsError, mam.set_as_allocated, (-1, 10))
        assert_raises(OutOfBoundsError, mam.set_as_allocated, (0, 10))
        assert_raises(OutOfBoundsError, mam.set_as_allocated, (1, 11))
        assert_raises(OutOfBoundsError, mam.set_as_allocated, (9, 10))
        assert_raises(CouldNotAllocateError, mam.set_as_allocated, (0, 1))

        mam = MemoryAllocationManager(size=100)
        mam.deallocate((0, 99))
        assert_list_equal(mam.unallocated_ranges, [(0, 99)])
        # Mark middle as allocated, splitting the range into two
        mam.set_as_allocated((3, 44))
        assert_list_equal(mam.unallocated_ranges, [(0, 2), (45, 99)])
        # Again, but splitting a range into the smallest possible size
        mam.set_as_allocated((1, 1))
        assert_list_equal(mam.unallocated_ranges, [(0, 0), (2, 2), (45, 99)])
        # Destroying a range of size 1
        mam.set_as_allocated((0, 0))
        assert_list_equal(mam.unallocated_ranges, [(2, 2), (45, 99)])
        # Allocate from the beginning
        mam.set_as_allocated((45, 55))
        assert_list_equal(mam.unallocated_ranges, [(2, 2), (56, 99)])
        # Allocate from the end
        mam.set_as_allocated((80, 99))
        assert_list_equal(mam.unallocated_ranges, [(2, 2), (56, 79)])
        # Allocate an entire range
        mam.set_as_allocated((56, 79))
        assert_list_equal(mam.unallocated_ranges, [(2, 2)])

        mam = MemoryAllocationManager(size=0x50, unallocated_ranges=[(0, 0xf), (0x10, 0x1f), (0x20, 0x2f), (0x30, 0x3f)])
        # Mark a range free that spans multiple unallocated ranges
        mam.set_as_allocated((0x5, 0x25))
        assert_list_equal(mam.unallocated_ranges, [(0, 0x4), (0x26, 0x2f), (0x30, 0x3f)])
        mam.set_as_allocated((0x26, 0x31))
        assert_list_equal(mam.unallocated_ranges, [(0, 0x4), (0x32, 0x3f)])
        # Test invalid allocation
        assert_raises(CouldNotAllocateError, mam.set_as_allocated, (0x31, 0x32))
        assert_raises(CouldNotAllocateError, mam.set_as_allocated, (0x3f, 0x40))
        assert_raises(CouldNotAllocateError, mam.set_as_allocated, (0x31, 0x40))

    def test_get_unallocated_portions_of_range(self):
        mam = MemoryAllocationManager(size=50)
        mam.deallocate((0, 10))
        assert_list_equal(mam.get_unallocated_portions_of_range((2, 8)), [(2, 8)])
        assert_list_equal(mam.get_unallocated_portions_of_range((5, 20)), [(5, 10)])
        mam.deallocate((12, 14))
        assert_list_equal(mam.get_unallocated_portions_of_range((5, 20)), [(5, 10), (12, 14)])
        mam.deallocate((18, 30))
        assert_list_equal(mam.get_unallocated_portions_of_range((5, 20)), [(5, 10), (12, 14), (18, 20)])
        assert_list_equal(mam.get_unallocated_portions_of_range((16, 32)), [(18, 30)])

    def test_is_unallocated(self):
        mam = MemoryAllocationManager(size=10)
        assert_raises(InvalidArgumentError, mam.is_unallocated, (1, 0))
        assert_raises(InvalidArgumentError, mam.is_unallocated, (8, 2))
        assert_raises(OutOfBoundsError, mam.is_unallocated, (-1, 0))
        assert_raises(OutOfBoundsError, mam.is_unallocated, (-1, 9))
        assert_raises(OutOfBoundsError, mam.is_unallocated, (-1, 10))
        assert_raises(OutOfBoundsError, mam.is_unallocated, (0, 10))
        assert_raises(OutOfBoundsError, mam.is_unallocated, (1, 11))
        assert_raises(OutOfBoundsError, mam.is_unallocated, (9, 10))

        assert_false(mam.is_unallocated((0, 0)))
        assert_true(mam.is_allocated((0, 0)))

        mam.deallocate((1, 3))
        mam.deallocate((4, 5))
        mam.deallocate((9, 9))

        assert_true(mam.is_unallocated((1, 3)))
        assert_true(mam.is_unallocated((4, 5)))
        assert_true(mam.is_unallocated((9, 9)))
        assert_true(mam.is_unallocated((1, 1)))
        assert_false(mam.is_unallocated((0, 1)))
        assert_false(mam.is_unallocated((1, 4)))
        assert_false(mam.is_unallocated((0, 4)))
        assert_false(mam.is_unallocated((0, 9)))
        assert_false(mam.is_unallocated((1, 9)))

    def test_allocate(self):
        mam = MemoryAllocationManager(size=100)
        assert_raises(InvalidArgumentError, mam.allocate)
        assert_raises(InvalidArgumentError, mam.allocate, 0)
        assert_raises(InvalidArgumentError, mam.allocate, -1)
        assert_raises(InvalidArgumentError, mam.allocate, -10)

        # Allocate an entire range
        mam.deallocate((0, 49))
        assert_raises(NotEnoughUnallocatedSpaceError, mam.allocate, 51)
        offset = mam.allocate(size=50)
        assert_equal(offset, 0)
        assert_equal(mam.unallocated_ranges, [])

        # Allocate the beginning of a range
        mam.deallocate((10, 39))
        offset = mam.allocate(size=3)
        assert_equal(offset, 10)
        assert_equal(mam.unallocated_ranges, [(13, 39)])

    def test_allocate_across_ranges(self):
        mam = MemoryAllocationManager(size=100)
        mam.deallocate((0, 5))
        mam.deallocate((6, 9))
        assert_raises(NotEnoughUnallocatedSpaceError, mam.allocate, 10)