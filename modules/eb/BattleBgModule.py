import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import EbCompressedData, DataBlock
from CompressedGraphicsModule import EbArrangement, EbTileGraphics, EbPalettes

class BattleBgModule(EbModule.EbModule):
    _name = "Battle Backgrounds"
    def __init__(self):
        self._bbgGfxPtrTbl = EbTable(0xcad7a1)
        self._bbgArrPtrTbl = EbTable(0xcad93d)
        self._bbgPalPtrTbl = EbTable(0xcadad9)
        self._bbgTbl = EbTable(0xcadca1)
    def readFromRom(self, rom):
        self._bbgGfxPtrTbl.readFromRom(rom)
        self._bbgArrPtrTbl.readFromRom(rom)
        self._bbgPalPtrTbl.readFromRom(rom)

        self._bbgGfxArrs = [ None for i in range(self._bbgGfxPtrTbl.height()) ]
        self._bbgPals = [ None for i in range(self._bbgPalPtrTbl.height()) ]
        self._bbgTbl.readFromRom(rom)
        for i in range(self._bbgTbl.height()):
            gfxNum = self._bbgTbl[i,0].val()
            colorDepth = self._bbgTbl[i,2].val()
            if (self._bbgGfxArrs[gfxNum] == None):
                tgb = EbCompressedData()
                tgb.readFromRom(rom,
                        EbModule.toRegAddr(self._bbgGfxPtrTbl[gfxNum,0].val()))
                ab = EbCompressedData()
                ab.readFromRom(rom,
                        EbModule.toRegAddr(self._bbgArrPtrTbl[gfxNum,0].val()))
                tg = EbTileGraphics(512, 8, colorDepth)
                tg.readFromBlock(tgb)
                a = EbArrangement(32, 32)
                a.readFromBlock(ab)
                self._bbgGfxArrs[gfxNum] = (tg, a, tgb, ab)
            palNum = self._bbgTbl[i,1].val()
            if (self._bbgPals[palNum] == None):
                pb = DataBlock(32)
                pb.readFromRom(rom,
                        EbModule.toRegAddr(self._bbgPalPtrTbl[palNum,0].val()))
                p = EbPalettes(1, 16)
                p.readFromBlock(pb)
                self._bbgPals[palNum] = (p, pb)
    def writeToRom(self, rom):
       # Write gfx+arrs
        i = 0
        for (tg, a, tgb, ab) in self._bbgGfxArrs:
            tg.writeToBlock(tgb)
            a.writeToBlock(ab)
            self._bbgGfxPtrTbl[i][0] = EbModule.toSnesAddr(
                    tgb.writeToFree(rom))
            self._bbgArrPtrTbl[i][0] = EbModule.toSnesAddr(
                    ab.writeToFree(rom))
            i += 1
        self._bbgGfxPtrTbl.writeToRom(rom)
        self._bbgArrPtrTbl.writeToRom(rom)

        # Write pals
        i = 0
        for (p, pb) in self._bbgPals:
            p.writeToBlock(pb)
            self._bbgPalPtrTbl[i][0] = EbModule.toSnesAddr(
                    pb.writeToFree(rom))
            i += 1
        self._bbgPalPtrTbl.writeToRom(rom)

        # Write the data table
        self._bbgTbl.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        # Export BGs by table entry
        for i in range(self._bbgTbl.height()):
            (tg, a, _, _) = self._bbgGfxArrs[self._bbgTbl[i,0].val()]
            pal = self._bbgTbl[i,1].val()
            img = a.toImage(tg, self._bbgPals[pal][0])
            imgFile = resourceOpener('BattleBGs/' + str(i).zfill(3), 'png')
            img.save(imgFile, 'png')
            imgFile.close()
    def readFromProject(self, resourceOpener):
        pass
