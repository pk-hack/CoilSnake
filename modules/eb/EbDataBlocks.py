import EbModule
from array import array
from zlib import crc32


class DataBlock:

    def __init__(self, size):
        self._size = size
        self._data = array('B', [0] * self._size)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # TODO ?
        pass

    def readFromRom(self, rom, addr):
        self._data = rom.readList(addr, self._size)

    def writeToRom(self, rom, addr):
        rom.write(addr, self._data)

    def writeToFree(self, rom):
        return rom.writeToFree(self._data)

    def hash(self):
        return crc32(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, val):
        if isinstance(val, list):
            self._data[key] = array('B', val)
        else:
            self._data[key] = val

    def __len__(self):
        return len(self._data)


class EbCompressedData:

    def __init__(self, size=None):
        if size is not None:
            self._data = array('B', [0] * size)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # TODO ?
        pass

    def readFromRom(self, rom, addr):
        ucdata = EbModule.decomp(rom, addr)
        if ucdata[0] < 0:
            print "Error decompressing data @", hex(addr)
        else:
            self._data = array('B', ucdata)
#    def writeToProject(self, resourceOpener):
#        f = resourceOpener("dump", "smc")
#        self._data.tofile(f)
#        f.close()

    def writeToFree(self, rom):
        cdata = EbModule.comp(self._data.tolist())
        return rom.writeToFree(cdata)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self._data[key]
        else:
            return self._data[key]

    def __setitem__(self, key, val):
        self._data[key] = val

    def __len__(self):
        return len(self._data)

    def tolist(self):
        return self._data.tolist()
