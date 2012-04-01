import array
import os
import yaml

class Rom:
    def __init__(self, romtypeFname=None):
        self._data = array.array('B')
        self._size = 0
        self._type = "Unknown"
        self._type_map = { }
        self._freeRanges = [ ]
        if (romtypeFname):
            with open(romtypeFname, 'r') as f:
                self._type_map = yaml.load(f)
    def checkRomType(self):
        for t, d in self._type_map.iteritems():
            offset, data, platform = d['offset'], d['data'], d['platform']

            if (platform == "SNES"):
                # Validate the ROM and check if it's headered

                # Check for unheadered HiROM
                try:
                    if (~self[0xffdc] & 0xff == self[0xffde]) \
                            and (~self[0xffdd] & 0xff == self[0xffdf]) \
                            and (self[offset:offset+len(data)] == data):
                        return t
                except IndexError:
                    pass

                # Check for unheadered LoROM
                try:
                    if (~self[0x7fdc] & 0xff == self[0x7fde]) \
                            and (~self[0x7fdd] & 0xff == self[0x7fdf]) \
                            and (self[offset:offset+len(data)] == data):
                        return t
                except IndexError:
                    pass

                # Check for headered HiROM
                try:
                    if (~self[0x101dc] & 0xff == self[0x101de]) \
                            and (~self[0x101dd] & 0xff == self[0x101df]) \
                            and (self[offset+0x200:offset+0x200+len(data)]==data):
                        # Remove header
                        self._data = self._data[0x200:]
                        self._size -= 0x200
                        return t
                except IndexError:
                    pass

                # Check for unheadered LoROM
                try:
                    if (~self[0x81dc] & 0xff == self[0x81de]) \
                            and (~self[0x81dd] & 0xff == self[0x81df]) \
                            and (self[offset+0x200:offset+0x200+len(data)]==data):
                        # Remove header
                        self._data = self._data[0x200:]
                        self._size -= 0x200
                        return t
                except:
                    pass

            elif (self[offset:offset+len(data)] == data):
                return t
        else:
            return "Unknown"
    def load(self, f):
        if type(f) == str:
            f = open(f,'rb')
        self._size = int(os.path.getsize(f.name))
        self._data = array.array('B')
        self._data.fromfile(f, self._size)
        f.close()
        self._type = self.checkRomType()
        if (self._type != "Unknown" and
                self._type_map[self._type].has_key('free ranges')):
            #self._free_loc = self._type_map[self._type]['free space']
            self._freeRanges = map(
                    lambda y: tuple(map(lambda z: int(z, 0),
                        y[1:-1].split(','))),
                    self._type_map[self._type]['free ranges'])
            self._freeRanges.sort()
        else:
            self._freeRanges = []
    def save(self, f):
        if type(f) == str:
            f = open(f, 'wb')
        self._data.tofile(f)
    def type(self):
        return self._type
    # Reading methods
    def read(self, i):
        if (i < 0) or (i >= self._size):
            raise ValueError("Reading outside of ROM range")
        return self._data[i]
    def readList(self, i, len):
        if (len < 0):
            raise ValueError("Can only read a list of non-negative length")
        elif (i < 0) or (i >= self._size) or (i+len > self._size):
            raise ValueError("Reading outside of ROM range")
        return self._data[i:i+len].tolist()
    def readMulti(self, i, len):
        # Note: reads in reverse endian
        if (len < 0):
            raise ValueError("Can only read an int of non-negative length")
        elif (i < 0) or (i >= self._size) or (i+len > self._size):
            raise ValueError("Reading outside of ROM range")
        d = self[i:i+len]
        d.reverse()
        return reduce(lambda x,y: (x<<8)|y, d)
    # Writing methods
    def write(self, i, data):
        if (type(data) == list):
            if (i < 0) or (i >= self._size) or (i+len(data) > self._size):
                raise ValueError("Writing outside of ROM range")
            self[i:i+len(data)] = data
        elif (type(data) == int):
            if (i < 0) or (i >= self._size):
                raise ValueError("Writing outside of ROM range")
            self[i] = data
        else:
            raise ValueError("write(): data must be either a list or int")
    def writeMulti(self, i, data, size):
        while size > 0:
            self.write(i, data & 0xff)
            data >>= 8
            size -= 1
            i += 1
    def addFreeRanges(self, ranges):
        # TODO do some check so that free ranges don't overlap
        self._freeRanges += ranges
        self._freeRanges.sort()
    # Find a free range starting at addr such that add & mask == 0
    def getFreeLoc(self, size, mask=0):
        ranges = filter(lambda (x,y): x & mask == 0, self._freeRanges)
        for i in range(0, len(self._freeRanges)):
            begin, end = self._freeRanges[i]
            if begin & mask != 0:
                continue
            if size <= end-begin+1:
                if begin+size == end:
                    # Used up the entire free range
                    del(self._freeRanges[i])
                else:
                    self._freeRanges[i] = (begin+size, end)
                return begin
        # TODO what if there is enough free space available, but not starting
        # with the mask?
        return -1
    def writeToFree(self, data):
        loc = self.getFreeLoc(len(data))
        if loc < 0:
            raise RuntimeError(
                    "writeToFree: not enough free space left")
        else:
            self.write(loc, data)
            return loc
    # Overloaded operators
    def __getitem__(self, key):
        if (type(key) == slice):
            return self._data[key].tolist()
        else:
            return self._data[key]
    def __setitem__(self, key, item):
        if (type(key) == slice):
            self._data[key] = array.array('B',item)
        else:
            self._data[key] = item
    def __len__(self):
        return self._size
    def __eq__(self, other):
        return (type(other) == type(self)) and (self._data == other._data)
    def __ne__(self, other):
        return not (self == other)
