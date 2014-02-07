import array


class DataBlock:

    def __init__(self, spec, addr=None):
        self._addr = addr
        if 'name' in spec:
            self._name = spec['name']
        self._size = spec['size']
        self._data = array.array('B')

    def readFromRom(self, rom, addr=None):
        if addr is None:
            addr = self._addr
        self._data = array.array('B')
        self._data.fromlist(rom.readList(self._addr, self._size))

    def writeToRom(self, rom, addr=None):
        if addr is None:
            addr = self._addr
        rom.write(addr, self._data.tolist())

    def writeToFree(self, rom):
        return rom.writeToFree(self._data.tolist())

    def set(self, inputRaw):
        self._data = array.array('B')
        self._data.fromstring(inputRaw)

    def dump(self):
        return self._data.tostring()

    def name(self):
        return self._name
