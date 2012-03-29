import EbModule
import array

class DataBlock:
    def __init__(self, size):
        self._size = size
        self._data = None
    def readFromRom(self, rom, addr):
        self._data = rom.readList(addr, self._size)
    def writeToFree(self, rom):
        return rom.writeToFree(self._data)
    def clear(self, len=0):
        if len != 0:
            self._size = len
        self._data = [0] * self._size
    def __getitem__(self, key):
        if type(key) == slice:
            return self._data[key].tolist()
        else:
            return self._data[key]
    def __setitem__(self, key, val):
        self._data[key] = val
    def __len__(self):
        return len(self._data)

class EbCompressedData:
    def __init__(self):
        self._data = None
    def readFromRom(self, rom, addr):
        ucdata = EbModule.decomp(rom, addr)
        if ucdata[0] < 0:
            print "Error decompressing data @", hex(addr)
        else:
            self._data = array.array('B', ucdata)
#    def writeToProject(self, resourceOpener):
#        f = resourceOpener("dump", "smc")
#        self._data.tofile(f)
#        f.close()
    def writeToFree(self, rom):
        cdata = EbModule.comp(self._data.tolist())
        return rom.writeToFree(cdata)
    def clear(self, len=0):
        self._data = array.array('B', [0] * len)
    def __getitem__(self, key):
        if type(key) == slice:
            return self._data[key].tolist()
        else:
            return self._data[key]
    def __setitem__(self, key, val):
        self._data[key] = val
    def __len__(self):
        return len(self._data)
    def tolist(self):
        return self._data.tolist()
