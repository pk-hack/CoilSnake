import EbModule
from modules.RawBlocksModule import DataBlock, RawBlocksModule

import array

class EbDataBlock(DataBlock):
    def __init__(self, spec, addr=None):
        DataBlock.__init__(self, spec, addr)
        self._addr = EbModule.toRegAddr(self._addr)
        if spec.has_key('compression'):
            self._comp = spec['compression']
        else:
            self._comp = None
    def readFromRom(self, rom, addr=None):
        if addr == None:
            addr = self._addr
        if self._comp == 'LZ_EB':
            self._data = array.array('B')
            decomp = EbModule.decomp(rom, addr)
            if decomp[0] < 0: # Error
                print "Error decompressing block @", hex(self._addr)
                self._data.fromlist([ 0 ])
            else:
                self._data.fromlist(decomp)
        else:
            DataBlock.readFromRom(self, rom)
    def writeToRom(self, rom, addr=None):
        if addr == None:
            addr = self._addr
        if self._comp == 'LZ_EB':
            comp = EbModule.comp(self._data.tolist())
            rom.write(addr, comp)
        else:
            DataBlock.writeToRom(self, rom, addr)
    def writeToFree(self, rom):
        if self._comp == 'LZ_EB':
            comp = EbModule.comp(self._data.tolist())
            return rom.writeToFree(comp)
        else:
            return DataBlock.writeToFree(self,rom)
    def rawData(self):
        return self._data

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

