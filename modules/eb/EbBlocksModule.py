import EbModule
from modules.RawBlocksModule import DataBlock, RawBlocksModule

class EbDataBlock(DataBlock):
    def __init__(self, addr, spec):
        DataBlock.__init__(self, addr, spec)
        self._addr = EbModule.toRegAddr(self._addr)
        if spec.has_key('compression'):
            self._comp = spec['compression']
        else:
            self._comp = None
    def readFromRom(self, rom):
        if self._comp == 'comp':
            self._data = EbModule.decomp(rom, self._addr)
        else:
            DataBlock.readFromRom(self, rom)

class EbBlocksModule(EbModule.EbModule):
    _name = "EarthBound Binary Data"
    def __init__(self):
        self._rbm = RawBlocksModule("structures/eb.yml", EbDataBlock)
    def readFromRom(self, rom):
        self._rbm.readFromRom(rom)
    def writeToRom(self, rom):
        self._rbm.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        self._rbm.writeToProject(resourceOpener)
    def readFromProject(self, resourceOpener):
        self._rbm.readFromProject(resourceOpener)

