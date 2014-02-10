import array
import logging
import os
import yaml
from error import OutOfBoundsError, InvalidArgumentError, NotEnoughUnallocatedSpaceError, FileAccessError, \
    ValueNotUnsignedByteError


log = logging.getLogger(__name__)


class DataBlock(object):
    def __init__(self):
        self.reset()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self.data

    def reset(self):
        self.data = array.array('B')
        self.size = 0

    def from_file(self, filename):
        self.reset()

        try:
            self.size = int(os.path.getsize(filename))
            with open(filename, 'rb') as f:
                self.data.fromfile(f, self.size)
        except (IOError, OSError) as e:
            log.exception(e)
            raise FileAccessError("Could not access file[%s]" % filename)

    def from_list(self, data_list):
        self.size = len(data_list)
        del self.data
        self.data = array.array('B')
        self.data.fromlist(data_list)

    def to_file(self, filename):
        with open(filename, 'wb') as f:
            self.data.tofile(f)

    def to_list(self):
        return self.data.tolist()

    def read_multi(self, key, size):
        if size < 0:
            raise InvalidArgumentError("Attempted to read data of negative length[%d]" % size)
        elif size == 0:
            return 0
        elif (key < 0) or (key >= self.size) or (key + size > self.size):
            raise OutOfBoundsError("Attempted to read from out of bounds offset[%#x]" % key)
        else:
            data = self[key:key + size]
            data.reverse()
            return reduce(lambda x, y: (x << 8) | y, data)

    def write_multi(self, key, item, size):
        if size < 0:
            raise InvalidArgumentError("Attempted to write data of negative length[%d]" % size)
        elif (key < 0) or (key >= self.size) or (key + size > self.size):
            raise OutOfBoundsError("Attempted to write to out of bounds offset[%#x]" % key)
        elif size == 0:
            return
        else:
            while size > 0:
                self[key] = item & 0xff
                item >>= 8
                size -= 1
                key += 1

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.start > key.stop:
                raise InvalidArgumentError("Second argument of slice %s must be greater than the first" % key)
            elif (key.start < 0) or (key.stop-1 >= self.size):
                raise OutOfBoundsError("Attempted to read from range (%d,%d) which is out of bounds" % (key.start,
                                       key.stop-1))
            else:
                return self.data[key].tolist()
        elif isinstance(key, int):
            if key >= self.size:
                raise OutOfBoundsError("Attempted to read at offset[%d] which is out of bounds" % key)
            else:
                return self.data[key]
        else:
            raise TypeError("Invalid argument type")

    def __setitem__(self, key, item):
        if isinstance(key, slice) and isinstance(item, list):
            if key.start > key.stop:
                raise InvalidArgumentError("Second argument of slice %s must be greater than  the first" % key)
            elif (key.start < 0) or (key.stop-1 >= self.size):
                raise OutOfBoundsError("Attempted to write to range (%d,%d) which is out of bounds" % (key.start,
                                       key.stop-1))
            elif len(item) != (key.stop - key.start):
                raise InvalidArgumentError("Attempted to write data of size %d to range of length %d" % (len(item),
                                           key.stop - key.start))
            elif (key.stop - key.start) == 0:
                raise InvalidArgumentError("Attempted to write data of size 0")
            else:
                self.data[key] = array.array('B', item)
        elif isinstance(key, int) and isinstance(item, int):
            if item < 0 or item > 0xff:
                raise ValueNotUnsignedByteError("Attempting to write value[%d] into a single byte" % item)
            if key >= self.size:
                raise OutOfBoundsError("Attempted to write to offset[%#x] which is out of bounds" % key)
            else:
                self.data[key] = item
        else:
            raise TypeError("Invalid argument type")

    def __len__(self):
        return self.size

    def __eq__(self, other):
        return (isinstance(other, type(self))) and (self.data == other.data)

    def __ne__(self, other):
        return not (self == other)


class AllocatableDataBlock(DataBlock):
    def __init__(self):
        super(AllocatableDataBlock, self).__init__()

        self.unallocated_ranges = []

    def mark_allocated(self, used_range):
        allocated_begin, allocated_end = used_range
        for i in range(len(self.unallocated_ranges)):
            begin, end = self.unallocated_ranges[i]
            if allocated_begin == begin:
                if allocated_end < end:
                    self.unallocated_ranges[i] = (allocated_end + 1, end)
                elif allocated_end == end:
                    del(self.unallocated_ranges[i])
                else:  # allocated_end > end
                    del(self.unallocated_ranges[i])
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
        raise InvalidArgumentError("Attempted to mark range (%#x,%#x) as allocated because it is at least "
                                   "partially already allocated" % (allocated_begin, allocated_end))

    def is_unallocated(self, range):
        search_begin, search_end = range
        for begin, end in self.unallocated_ranges:
            if (search_begin >= begin) and (search_end <= end):
                return True
        return False

    def unallocate(self, range):
        # TODO do some check so that unallocated ranges don't overlap
        self.unallocated_ranges += range
        self.unallocated_ranges.sort()

    def allocate(self, data=None, size=None, mask=0):
        if data is None and size is None:
            raise InvalidArgumentError("Insufficient parameters provided")
        if size is None:
            size = len(data)

        # First find a free range
        unallocated_range = None
        for i in xrange(0, len(self.unallocated_ranges)):
            begin, end = self.unallocated_ranges[i]
            if begin & mask != 0:
                continue
            if size <= end - begin + 1:
                if begin + size == end:
                    # Used up the entire free range
                    del(self.unallocated_ranges[i])
                else:
                    self.unallocated_ranges[i] = (begin + size, end)
                unallocated_range = (begin, end)
                break
        # TODO what if there is enough free space available, but not starting with the mask?
        if unallocated_range is None:
            raise NotEnoughUnallocatedSpaceError("Not enough free space left")

        if data is not None:
            self[unallocated_range[0]:unallocated_range[1]+1] = data

        return unallocated_range[0]


ROM_TYPE_MAP = None
with open(os.path.join(os.path.dirname(__file__), "resources", "romtypes.yml"), 'r') as f:
    ROM_TYPE_MAP = yaml.load(f, Loader=yaml.CSafeLoader)

ROM_TYPE_NAME_UNKNOWN = "Unknown"

class Rom2(AllocatableDataBlock):
    def __init__(self):
        super(Rom2, self).__init__()

        self.type = "Unknown"

    def from_file(self, filename):
        super(Rom2, self).from_file(filename)
        self._setup_rom()

    def from_list(self, data_list):
        super(Rom2, self).from_list(data_list)
        self._setup_rom()

    def _setup_rom(self):
        self.type = self._detect_type()
        if self.type != ROM_TYPE_NAME_UNKNOWN and 'free ranges' in ROM_TYPE_MAP[self.type]:
            self.unallocated_ranges = map(lambda y: tuple(map(lambda z: int(z, 0), y[1:-1].split(','))),
                                          ROM_TYPE_MAP[self.type]['free ranges'])
            self.unallocated_ranges = filter(lambda (begin, end): end < self.size, self.free_ranges)
            self.unallocated_ranges.sort()
        else:
            self.unallocated_ranges = []

    def _detect_type(self):
        for type_name, d in ROM_TYPE_MAP.iteritems():
            offset, data, platform = d['offset'], d['data'], d['platform']

            if platform == "SNES":
                # Validate the ROM and check if it's headered

                # Check for unheadered HiROM
                try:
                    if (~self[0xffdc] & 0xff == self[0xffde]) \
                            and (~self[0xffdd] & 0xff == self[0xffdf]) \
                            and (self[offset:offset + len(data)].tolist() == data):
                        return type_name
                except OutOfBoundsError:
                    pass

                # Check for unheadered LoROM
                try:
                    if (~self[0x7fdc] & 0xff == self[0x7fde]) \
                            and (~self[0x7fdd] & 0xff == self[0x7fdf]) \
                            and (self[offset:offset + len(data)].tolist() == data):
                        return type_name
                except OutOfBoundsError:
                    pass

                # Check for headered HiROM
                try:
                    if (~self[0x101dc] & 0xff == self[0x101de]) \
                            and (~self[0x101dd] & 0xff == self[0x101df]) \
                            and (self[offset + 0x200:offset + 0x200 + len(data)].tolist() == data):
                        # Remove header
                        self.data = self._data[0x200:]
                        self.size -= 0x200
                        return type_name
                except OutOfBoundsError:
                    pass

                # Check for unheadered LoROM
                try:
                    if (~self[0x81dc] & 0xff == self[0x81de]) \
                            and (~self[0x81dd] & 0xff == self[0x81df]) \
                            and (self[offset + 0x200:offset + 0x200 + len(data)].tolist() == data):
                        # Remove header
                        self.data = self._data[0x200:]
                        self.size -= 0x200
                        return type_name
                except OutOfBoundsError:
                    pass
            elif self[offset:offset + len(data)].tolist() == data:
                return type_name
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
                    self._data.fromlist([0] * 0x200000)
                    self._size += 0x200000
                    # The data range written below is already marked as used in romtypes.yml
                    for i in range(0x8000, 0x8000 + 0x8000):
                        self[0x400000 + i] = self[i]
        else:
            raise NotImplementedError("Don't know how to expand ROM of type[%s]" % self.type)

