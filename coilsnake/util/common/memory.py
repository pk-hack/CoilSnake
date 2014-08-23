from coilsnake.exceptions.common.exceptions import CouldNotAllocateError, InvalidArgumentError, OutOfBoundsError, \
    NotEnoughUnallocatedSpaceError


def check_range_validity(range, size):
    begin, end = range
    if end < begin:
        raise InvalidArgumentError("Invalid range[(%#x,%#x)] provided" % (begin, end))
    elif (begin < 0) or (end >= size):
        raise OutOfBoundsError("Invalid range[(%#x,%#x)] provided" % (begin, end))


class MemoryAllocationManager(object):
    def __init__(self, size, unallocated_ranges=None):
        self.size = size
        if unallocated_ranges:
            self.unallocated_ranges = unallocated_ranges
        else:
            self.unallocated_ranges = []

    def is_unallocated(self, range):
        check_range_validity(range, self.size)

        search_begin, search_end = range
        for begin, end in self.unallocated_ranges:
            if (search_begin >= begin) and (search_end <= end):
                return True
        return False

    def is_allocated(self, range):
        return not self.is_unallocated(range)

    def get_largest_unallocated_range(self):
        largest_begin, largest_end = 1, 0
        for begin, end in self.unallocated_ranges:
            if end - begin > largest_end - largest_begin:
                largest_begin = begin
                largest_end = end
        if largest_end - largest_begin <= 0:
            raise NotEnoughUnallocatedSpaceError("Not enough free space left")
        return largest_begin, largest_end

    def set_as_allocated(self, range):
        check_range_validity(range, self.size)

        allocated_begin, allocated_end = range
        for i in xrange(len(self.unallocated_ranges)):
            a = self.unallocated_ranges[i]
            begin, end = a
            if allocated_begin == begin:
                if allocated_end < end:
                    self.unallocated_ranges[i] = (allocated_end + 1, end)
                elif allocated_end == end:
                    del (self.unallocated_ranges[i])
                else:  # allocated_end > end
                    del (self.unallocated_ranges[i])
                    self.set_as_allocated((end + 1, allocated_end))
                return
            elif (allocated_begin > begin) and (allocated_end <= end):
                self.unallocated_ranges[i] = (begin, allocated_begin - 1)
                if allocated_end != end:
                    self.unallocated_ranges.insert(i, (allocated_end + 1, end))
                    self.unallocated_ranges.sort()
                return
            elif (allocated_begin > begin) and (allocated_begin < end) and (allocated_end > end):
                self.unallocated_ranges[i] = (begin, allocated_begin - 1)
                self.set_as_allocated((end + 1, allocated_end))
                return
        raise CouldNotAllocateError("Couldn't mark range (%#x,%#x) as allocated because it is at least "
                                    "partially already allocated" % (allocated_begin, allocated_end))

    def get_unallocated_portions_of_range(self, input_range):
        check_range_validity(input_range, self.size)

        input_begin, input_end = input_range

        for unallocated_begin, unallocated_end in self.unallocated_ranges:
            if unallocated_begin <= input_begin <= unallocated_end:
                if unallocated_end >= input_end:
                    return [input_range]
                else:
                    return ([(input_begin, unallocated_end)] +
                            self.get_unallocated_portions_of_range((unallocated_end + 1, input_end)))
            elif input_begin <= unallocated_begin <= input_end:
                if input_end <= unallocated_end:
                    return (self.get_unallocated_portions_of_range((input_begin, unallocated_begin - 1)) +
                            [(unallocated_begin, input_end)])
                else:
                    return (self.get_unallocated_portions_of_range((input_begin, unallocated_begin - 1)) +
                            [(unallocated_begin, unallocated_end)] +
                            self.get_unallocated_portions_of_range((unallocated_end + 1, input_end)))
        return []

    def allocate(self, size=None, can_write_to=None):
        if size is None:
            raise InvalidArgumentError("Insufficient parameters provided")
        if size <= 0:
            raise InvalidArgumentError("Cannot allocate a range of size[%d]" % size)

        # First find a free range
        allocated_range = None
        for i in xrange(0, len(self.unallocated_ranges)):
            begin, end = self.unallocated_ranges[i]
            if size <= end - begin + 1:
                if (can_write_to is not None) and (not can_write_to(begin)):
                    continue

                if begin + size - 1 == end:
                    # Used up the entire free range
                    del (self.unallocated_ranges[i])
                else:
                    self.unallocated_ranges[i] = (begin + size, end)

                allocated_range = (begin, begin + size - 1)
                break

        if allocated_range is None:
            raise NotEnoughUnallocatedSpaceError("Not enough free space left")

        return allocated_range[0]

    def deallocate(self, range):
        check_range_validity(range, self.size)

        # TODO do some check so that unallocated ranges don't overlap
        # TODO attach contiguous unallocated ranges if possible

        self.unallocated_ranges.append(range)
        self.unallocated_ranges.sort()