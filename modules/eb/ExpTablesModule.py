import EbModule
from EbTablesModule import EbTable
from modules.TablesModule import TablesModule
from modules.Progress import updateProgress

#Table Addr, Max Entries, ASM Ptr Locs, Reg Ptr Locs, Reg pointer locs with offset
_tableIDs = [
        (0xCF8985, 4096,
            [0x23e5, 0x131ca, 0x1327f, 0x1332f, 0x1b20b, 0x464c1, 0x46831,
                0x46930],
            [0xc32f, 0x1ad78], []), # NPC Config Table
        (0xD5EBAB, 256, [0x1bcc2, 0x46df5], [], []), # Teleport
        (0xD5F2FB, 256, [0x724b, 0x72e5], [], []), # Hotspot
        (0xd58d7a, 256, [0x1c423], [], []), #PSI Names
        (0xd58a50, 256, # PSI Ability Table
            [0x1b694, 0x1b7cf, 0x1b8f9, 0x1bb34, 0x1c243, 0x1c2ad, 0x1c6e4,
                0x1c8d6, 0x1ca12, 0x1cd8f, 0x1d7d6, 0x1d839, 0x1d89b],
            [0x1b8bc, 0x1b9cd, 0x1c9d7, 0x1cae0, 0x1ccb7, 0x1cd4a, 0x1ce3c,
                0x45eff, 0x45f1c, 0x45f39], []),
        (0xd57b68, 4096, # Battle actions
            [0x1adc8, 0x1affd, 0x1b04f, 0x1b0cb, 0x1b138, 0x1b1a7, 0x1b259,
                0x1b371, 0x1b466, 0x1b89c, 0x1b8e7, 0x1b9ad, 0x1c913, 0x1cc9b,
                0x1df64, 0x1dfb8, 0x2451f, 0x2582e, 0x25c32, 0x25ceb, 0x2794d],
            [0x11ff2, 0x1b6e5, 0x1b80f, 0x1c9e8, 0x1cd56, 0x1cdd0, 0x244d5,
                0x256ef, 0x257e5, 0x25a13, 0x25a8b, 0x25b4f, 0x25b9e, 0x269a0,
                0x29448],
            [(0x23210, 432), (0x2328d, 411), (0x232cd, 655), (0x2330a, 387),
                (0x23358, 471), (0x2339b, 459), (0x2341f, 447), (0x234b9, 435),
                (0x2939c, 364), (0x293a2, 366)]),
        (0xd55000, 256, # Items
            [0x137ac, 0x18ddb, 0x19222, 0x19968, 0x19993, 0x19ac2, 0x19e06,
                0x1a108, 0x1a133, 0x1a872, 0x1a8a1, 0x1afb2, 0x1ceaa, 0x1d044,
                0x21712, 0x217eb, 0x2427a, 0x2b257, 0x3f212],
            [0x1388f, 0x14f1c, 0x14f57, 0x170eb, 0x1772d, 0x18b75, 0x18b94,
                0x18e43, 0x1909d, 0x19b98, 0x19c56, 0x19c8e, 0x19ef5, 0x1a277,
                0x1a36b, 0x1a3e5, 0x1a45f, 0x1a558, 0x1a63b, 0x1a6a6, 0x1a70b,
                0x1db4d, 0x1db7e, 0x1df56, 0x218c9, 0x2199d, 0x21a12, 0x21a87,
                0x21b37, 0x21bf0, 0x21ca9, 0x21cf8, 0x21dd5, 0x21e48, 0x21e9b,
                0x21f1d, 0x21f80, 0x2200d, 0x22070, 0x220fd, 0x22160, 0x221e6,
                0x224f0, 0x22533, 0x2318a, 0x24400, 0x2834b, 0x2abb0, 0x3ee32],
            []),
        # Windows
        (0xc3e250, 256, [0x105c9], [], []) ]

class ExpTablesModule(EbModule.EbModule):
    _name = "Expanded Tables"
    def __init__(self):
        self._tables = map(lambda (x,a,b,c,d): (EbTable(x),a,b,c,d), _tableIDs)
        self._pct = 50.0/len(self._tables)
    def readFromRom(self, rom):
        for (t,a,b,c,d) in self._tables:
            t.readFromRom(rom)
            updateProgress(self._pct)
    def freeRanges(self):
        return map(lambda (x,a,b,c,d): (EbModule.toSnesAddr(x._addr),
            EbModule.toSnesAddr(x._addr)+x._size), self._tables)
    def writeToRom(self, rom):
        for (t, a, asmPtrs, regPtrs, regPtrsOff) in self._tables:
            try:
                addr = EbModule.toSnesAddr(t.writeToFree(rom))
            except Exception as inst:
                print t._name
                raise inst
            for asmPtr in asmPtrs:
                EbModule.writeAsmPointer(rom, asmPtr, addr)
            for regPtr in regPtrs:
                rom.writeMulti(regPtr, addr, 3)
            for (ptr, off) in regPtrsOff:
                rom.writeMulti(ptr, addr+off, 3)

            # Hardcoded number of entries in PSI Ability Table
#            if t._addr == 0xd58a50:
#                rom.writeMulti(0x1c843, t.height(), 2)
            updateProgress(self._pct)
    def writeToProject(self, resourceOpener):
        for (t,a,b,c,d) in self._tables:
            t.writeToProject(resourceOpener)
            updateProgress(self._pct)
    def readFromProject(self, resourceOpener):
        for (t,a,b,c,d) in self._tables:
            t.readFromProject(resourceOpener)
            updateProgress(self._pct)
