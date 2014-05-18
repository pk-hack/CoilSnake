import array
import copy
import os
from zlib import crc32

from coilsnake.exceptions.common.exceptions import OutOfBoundsError, InvalidArgumentError, \
    NotEnoughUnallocatedSpaceError, FileAccessError, CouldNotAllocateError
from coilsnake.util.common.assets import open_asset
from coilsnake.util.common.yml import yml_load


def check_range_validity(range, size):
    begin, end = range
    if end < begin:
        raise InvalidArgumentError("Invalid range[(%#x,%#x)] provided" % (begin, end))
    elif (begin < 0) or (end >= size):
        raise OutOfBoundsError("Invalid range[(%#x,%#x)] provided" % (begin, end))


class Block(object):
    def __init__(self, size=0):
        self.reset(size)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self.data

    def reset(self, size=0):
        self.data = array.array('B', [0] * size)
        self.size = size

    def from_file(self, filename):
        self.reset()

        try:
            self.size = int(os.path.getsize(filename))
            del self.data
            self.data = array.array('B')
            with open(filename, 'rb') as file:
                self.data.fromfile(file, self.size)
        except (IOError, OSError):
            raise FileAccessError("Could not access file[%s]" % filename)

    def from_list(self, data_list):
        self.size = len(data_list)
        del self.data
        self.data = array.array('B')
        self.data.fromlist(data_list)

    @classmethod
    def create_from_list(cls, data_list):
        block = cls()
        block.from_list(data_list=data_list)
        return block

    def from_array(self, data_array):
        self.size = len(data_array)
        del self.data
        self.data = copy.copy(data_array)

    def from_block(self, block, offset=0, size=None):
        if size is None:
            size = block.size - offset
        with block[offset:offset + size] as sub_block:
            self.size = sub_block.size
            self.data = sub_block.data

    def to_file(self, f):
        if type(f) == str:
            with open(f, 'wb') as fh:
                self.data.tofile(fh)
        else:
            self.data.tofile(f)

    def to_list(self):
        return self.data.tolist()

    def to_array(self):
        return self.data

    def to_block(self, block, offset=0):
        self[offset:offset + block.size] = block

    def read_multi(self, key, size):
        if size < 0:
            raise InvalidArgumentError("Attempted to read data of negative length[%d]" % size)
        elif size == 0:
            return 0
        elif (key < 0) or (key >= self.size) or (key + size > self.size):
            raise OutOfBoundsError("Attempted to read size[%d] bytes from offset[%#x], which is out of bounds in this "
                                   "block of size[%#x]" % (size, key, self.size))
        else:
            out = 0
            bit_offset = 0
            for byte in self.data[key:key + size]:
                out |= byte << bit_offset
                bit_offset += 8
            return out

    def write_multi(self, key, item, size):
        if size < 0:
            raise InvalidArgumentError("Attempted to write data of negative length[%d]" % size)
        elif (key < 0) or (key >= self.size) or (key + size > self.size):
            raise OutOfBoundsError("Attempted to write size[%d] bytes to offset[%#x], which is out of bounds in this "
                                   "block of size[%#x]" % (size, key, self.size))
        elif size == 0:
            return
        else:
            for i in xrange(key, key+size):
                self.data[i] = item & 0xff
                item >>= 8

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.start > key.stop:
                raise InvalidArgumentError("Second argument of slice %s must be greater than the first" % key)
            elif (key.start < 0) or (key.stop - 1 >= self.size):
                raise OutOfBoundsError("Attempted to read from range (%#x,%#x) which is out of bounds" % (key.start,
                                                                                                          key.stop - 1))
            else:
                out = Block()
                out.from_array(self.data[key])
                return out
        elif isinstance(key, int):
            if key >= self.size:
                raise OutOfBoundsError("Attempted to read at offset[%#x] which is out of bounds" % key)
            else:
                return self.data[key]
        else:
            raise TypeError("Argument \"key\" had invalid type of %s" % type(key).__name__)

    def __setitem__(self, key, item):
        if isinstance(key, int) and isinstance(item, (int, long)):
            if item < 0 or item > 0xff:
                raise InvalidArgumentError("Could not write invalid value[%d] as a single byte" % item)
            if key >= self.size:
                raise OutOfBoundsError("Attempted to write to offset[%#x] which is out of bounds" % key)
            else:
                self.data[key] = item
        elif isinstance(key, slice) and \
                (isinstance(item, list) or isinstance(item, array.array) or isinstance(item, Block)):
            if key.start > key.stop:
                raise InvalidArgumentError("Second argument of slice %s must be greater than  the first" % key)
            elif (key.start < 0) or (key.stop - 1 >= self.size):
                raise OutOfBoundsError("Attempted to write to range (%#x,%#x) which is out of bounds" % (key.start,
                                                                                                         key.stop - 1))
            elif len(item) != (key.stop - key.start):
                raise InvalidArgumentError("Attempted to write data of size %d to range of length %d" % (
                    len(item), key.stop - key.start))
            elif (key.stop - key.start) == 0:
                raise InvalidArgumentError("Attempted to write data of size 0")
            else:
                if isinstance(item, list):
                    self.data[key] = array.array('B', item)
                elif isinstance(item, array.array):
                    self.data[key] = item
                elif isinstance(item, Block):
                    self.data[key] = item.data
                else:
                    raise InvalidArgumentError("Can not write value of type[{}]".format(type(item)))
        else:
            raise TypeError("Arguments \"key\" and \"item\" had invalid types of %s and %s" % (type(key).__name__,
                                                                                               type(item).__name__))

    def __len__(self):
        return self.size

    def __eq__(self, other):
        return (isinstance(other, type(self))) and (self.data == other.data)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return crc32(self.data)


class AllocatableBlock(Block):
    def reset(self, size=0):
        super(AllocatableBlock, self).reset(size)
        self.unallocated_ranges = []

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

    def mark_allocated(self, used_range):
        check_range_validity(used_range, self.size)

        allocated_begin, allocated_end = used_range
        for i in range(len(self.unallocated_ranges)):
            a = self.unallocated_ranges[i]
            begin, end = a
            if allocated_begin == begin:
                if allocated_end < end:
                    self.unallocated_ranges[i] = (allocated_end + 1, end)
                elif allocated_end == end:
                    del (self.unallocated_ranges[i])
                else:  # allocated_end > end
                    del (self.unallocated_ranges[i])
                    self.mark_allocated((end + 1, allocated_end))
                return
            elif (allocated_begin > begin) and (allocated_end <= end):
                self.unallocated_ranges[i] = (begin, allocated_begin - 1)
                if allocated_end != end:
                    self.unallocated_ranges.insert(i, (allocated_end + 1, end))
                    self.unallocated_ranges.sort()
                return
            elif (allocated_begin > begin) and (allocated_begin < end) and (allocated_end > end):
                self.unallocated_ranges[i] = (begin, allocated_begin - 1)
                self.mark_allocated((end + 1, allocated_end))
                return
        raise CouldNotAllocateError("Couldn't mark range (%#x,%#x) as allocated because it is at least "
                                    "partially already allocated" % (allocated_begin, allocated_end))

    def is_unallocated(self, range):
        check_range_validity(range, self.size)

        search_begin, search_end = range
        for begin, end in self.unallocated_ranges:
            if (search_begin >= begin) and (search_end <= end):
                return True
        return False

    def is_allocated(self, range):
        return not self.is_unallocated(range)

    def deallocate(self, range):
        check_range_validity(range, self.size)

        # TODO do some check so that unallocated ranges don't overlap
        # TODO attach contiguous unallocated ranges if possible

        self.unallocated_ranges.append(range)
        self.unallocated_ranges.sort()

    def allocate(self, data=None, size=None, can_write_to=None):
        if data is None and size is None:
            raise InvalidArgumentError("Insufficient parameters provided")

        if size is None:
            size = len(data)
        elif data is not None and size != len(data):
            raise InvalidArgumentError("Parameter size[%d] and data's size[%d] differ" % (size, len(data)))

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

        if data is not None:
            self[allocated_range[0]:allocated_range[1] + 1] = data

        return allocated_range[0]

    def get_largest_unallocated_range(self):
        largest_begin, largest_end = 1, 0
        for begin, end in self.unallocated_ranges:
            if end - begin > largest_end - largest_begin:
                largest_begin = begin
                largest_end = end
        if largest_end - largest_begin <= 0:
            raise NotEnoughUnallocatedSpaceError("Not enough free space left")
        return largest_begin, largest_end


with open_asset("romtypes.yml") as f:
    ROM_TYPE_MAP = yml_load(f)

ROM_TYPE_NAME_UNKNOWN = "Unknown"


class Rom(AllocatableBlock):
    def reset(self, size=0):
        super(Rom, self).reset(size)
        self.type = ROM_TYPE_NAME_UNKNOWN

    def from_file(self, filename):
        super(Rom, self).from_file(filename)
        self._setup_rom_post_load()

    def _setup_rom_post_load(self):
        self.type = self._detect_type()
        if self.type != ROM_TYPE_NAME_UNKNOWN and 'free ranges' in ROM_TYPE_MAP[self.type]:
            self.unallocated_ranges = map(lambda y: tuple(map(lambda z: int(z, 0), y[1:-1].split(','))),
                                          ROM_TYPE_MAP[self.type]['free ranges'])
            self.unallocated_ranges = filter(lambda (begin, end): end < self.size, self.unallocated_ranges)
            self.unallocated_ranges.sort()

    def _detect_type(self):
        for type_name, d in ROM_TYPE_MAP.iteritems():
            offset, data, platform = d['offset'], d['data'], d['platform']

            if platform == "SNES":
                # Validate the ROM and check if it's headered

                # Check for unheadered HiROM
                try:
                    if (~self[0xffdc] & 0xff == self[0xffde]) \
                            and (~self[0xffdd] & 0xff == self[0xffdf]) \
                            and (self[offset:offset + len(data)].to_list() == data):
                        return type_name
                except OutOfBoundsError:
                    pass

                # Check for unheadered LoROM
                try:
                    if (~self[0x7fdc] & 0xff == self[0x7fde]) \
                            and (~self[0x7fdd] & 0xff == self[0x7fdf]) \
                            and (self[offset:offset + len(data)].to_list() == data):
                        return type_name
                except OutOfBoundsError:
                    pass

                # Check for headered HiROM
                try:
                    if (~self[0x101dc] & 0xff == self[0x101de]) \
                            and (~self[0x101dd] & 0xff == self[0x101df]) \
                            and (self[offset + 0x200:offset + 0x200 + len(data)].to_list() == data):
                        # Remove header
                        self.data = self.data[0x200:]
                        self.size -= 0x200
                        return type_name
                except OutOfBoundsError:
                    pass

                # Check for headered LoROM
                try:
                    if (~self[0x81dc] & 0xff == self[0x81de]) \
                            and (~self[0x81dd] & 0xff == self[0x81df]) \
                            and (self[offset + 0x200:offset + 0x200 + len(data)].to_list() == data):
                        # Remove header
                        self.data = self.data[0x200:]
                        self.size -= 0x200
                        return type_name
                except OutOfBoundsError:
                    pass
            else:
                try:
                    if self[offset:offset + len(data)].to_list() == data:
                        return type_name
                except OutOfBoundsError:
                    pass
        else:
            return ROM_TYPE_NAME_UNKNOWN

    def add_header(self):
        if self.type == 'Earthbound':
            for i in xrange(0x200):
                self.data.insert(0, 0)
            self.size += 0x200
        else:
            raise NotImplementedError("Don't know how to add header to ROM of type[%s]" % self.type)

    def expand(self, desired_size):
        if self.type == 'Earthbound':
            if (desired_size != 0x400000) and (desired_size != 0x600000):
                raise InvalidArgumentError("Cannot expand an %s ROM to size[%#x]" % (self.type, self.size))
            else:
                if self.size == 0x300000:
                    self.data.fromlist([0] * 0x100000)
                    self.size += 0x100000
                if desired_size == 0x600000 and self.size == 0x400000:
                    self[0x00ffd5] = 0x25
                    self[0x00ffd7] = 0x0d
                    self.data.fromlist([0] * 0x200000)
                    self.size += 0x200000
                    # The data range written below is already marked as used in romtypes.yml
                    for i in xrange(0x8000, 0x8000 + 0x8000):
                        self[0x400000 + i] = self[i]
        else:
            raise NotImplementedError("Don't know how to expand ROM of type[%s]" % self.type)

