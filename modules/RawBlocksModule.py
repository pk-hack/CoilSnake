import GenericModule

import array
import yaml

class DataBlock:
    def __init__(self, addr, spec):
        self._addr = addr
        self._name = spec['name']
        self._size = spec['size']
        self._data = array.array('B')
    def readFromRom(self, rom):
        self._data = array.array('B')
        self._data.fromlist(rom.readList(self._addr, self._size))
    def writeToRom(self, rom):
        rom.write(self._addr, self._data.tolist())
    def dump(self):
        return self._data.tostring()
    def load(self, inputRaw):
        self._data = array.array('B')
        self._data.fromstring(inputRaw)

class RawBlocksModule(GenericModule.GenericModule):
    _name = "Generic Raw Blocks"
    def __init__(self, structureFile, BlockClass):
        self._blocks = []
        with open(structureFile) as f:
            i=1
            for doc in yaml.load_all(f):
                if i == 1:
                    i += 1
                elif i == 2:
                    # Load the Raw Blocks
                    for addr in doc:
                        if doc[addr]['type'] == 'data' and \
                        (not doc[addr].has_key('entries')):
                            self._blocks.append(BlockClass(addr, doc[addr]))
                    break
    def readFromRom(self, rom):
        for b in self._blocks:
           b.readFromRom(rom)
    def writeToRom(self, rom):
        for b in self._blocks:
            b.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        for b in self._blocks:
            f = resourceOpener(b._name, 'bin')
            f.write(b.dump())
            f.close()
    def readFromProject(self, resourceOpener):
        for b in self._blocks:
            f = resourceOpener(b._name, 'bin')
            contents = f.read()
            f.close()
            b.load(contents)
