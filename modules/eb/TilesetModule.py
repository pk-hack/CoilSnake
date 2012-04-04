import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import EbCompressedData
from CompressedGraphicsModule import EbTileGraphics
from modules.Progress import updateProgress

from array import array

chars = "0123456789abcdefghijklmnopqrstuv"

# Just a palette with 6 subpals and hidden data
class MapPalette:
    def __init__(self):
        self.flag = 0
        self.altAddr = 0
        self.altMapTileset = -1
        self.altMapPalette = -1
        self.spritePal = 0
        self.flashEffect = 0
        self.subpals = None
    def readFromRom(self, rom, addr):
        self.flag = rom.readMulti(addr, 2)
        self.altAddr = rom.readMulti(addr + 0x20, 2)
        self.spritePal = rom.read(addr + 0x40)
        self.flashEffect = rom.read(addr + 0x60)
        self.subpals = map(lambda x: EbModule.readPalette(rom, x, 16),
                range(addr, addr+32*6, 32))
        for subp in self.subpals:
            subp[0] = (0,0,0)
    def getAsString(self):
        out = str()
        for subp in self.subpals:
            for (r,g,b) in subp:
                out += chars[r>>3]
                out += chars[g>>3]
                out += chars[b>>3]
        return out

class Tileset:
    def __init__(self):
        self.tg = EbTileGraphics(896, 8, 4)
        self.arr = [None for i in range(0,1024)]
        self.col = [None for i in range(0,1024)]
        self.pals = [ ]
    def readMinitilesFromRom(self, rom, addr):
        with EbCompressedData() as tgb:
            tgb.readFromRom(rom, addr)
            self.tg.readFromBlock(tgb)
    def readArrangementsFromRom(self, rom, addr):
        with EbCompressedData() as ab:
            ab.readFromRom(rom, addr)
            self.numArrs = len(ab)/32
            a = 0
            for i in range(self.numArrs):
                self.arr[i] = [ [0 for y in range(4)] for z in range(4) ]
                for j in range(4):
                    for k in range(4):
                        self.arr[i][k][j] = ab[a] + (ab[a+1]<<8)
                        a += 2
    def readCollisionsFromRom(self, rom, addr):
        for i in range(self.numArrs):
            tmp = rom.readMulti(addr + i*2, 2)
            self.col[i] = rom[0x180000+tmp:0x180000+tmp+16]
    def readPaletteFromRom(self, rom, mapTset, palNum, addr):
        pal = MapPalette()
        pal.readFromRom(rom, addr)
        self.pals.append((mapTset, palNum, pal))
    def getTileAsString(self, n):
        if n >= 896:
            return "0000000000000000000000000000000000000000000000000000000000000000"
        else:
            s = str()
            t = self.tg[n]
            for j in xrange(8):
                for i in xrange(8):
                    if t[i][j] <= 9:
                        s += chr(0x30 + t[i][j])
                    else:
                        s += chr(0x57 + t[i][j])
            return s
    def getArrAsString(self, n):
        if n >= self.numArrs:
            return '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        else:
            s = str()
            tmp = 0
            for j in xrange(4):
                for k in xrange(4):
                    s += hex(self.arr[n][k][j])[2:].zfill(4)
                    s += hex(self.col[n][j*4+k])[2:].zfill(2)
            return s
                        
    def writeToProject(self, file):
        for i in range(512):
            print >>file, self.getTileAsString(i)
            print >>file, self.getTileAsString(i^512)
            print >>file
        print >>file

        for (mt,mp,pal) in self.pals:
            file.write(chars[mt])
            file.write(chars[mp])
            print >>file, pal.getAsString()
        print >>file
        print >>file

        for i in range(1024):
            print >>file, self.getArrAsString(i)

class TilesetModule(EbModule.EbModule):
    _name = "Tilesets"
    def __init__(self):
        self._gfxPtrTbl = EbTable(0xEF105B)
        self._arrPtrTbl = EbTable(0xEF10AB)
        self._colPtrTbl = EbTable(0xEF117B)
        self._mapTsetTbl = EbTable(0xEF101B)
        self._palPtrTbl = EbTable(0xEF10FB)
    def readFromRom(self, rom):
        self._gfxPtrTbl.readFromRom(rom)
        self._arrPtrTbl.readFromRom(rom)
        self._colPtrTbl.readFromRom(rom)
        self._mapTsetTbl.readFromRom(rom)
        self._palPtrTbl.readFromRom(rom)
        self._tsets = [ Tileset() for i in range(20) ]

        # Read tilesets
        i=0
        for tset in self._tsets:
            # Read data
            tset.readMinitilesFromRom(rom,
                    EbModule.toRegAddr(self._gfxPtrTbl[i,0].val()))
            tset.readArrangementsFromRom(rom,
                    EbModule.toRegAddr(self._arrPtrTbl[i,0].val()))
            tset.readCollisionsFromRom(rom,
                    EbModule.toRegAddr(self._colPtrTbl[i,0].val()))
            i += 1

        # Read palettes
        palLocs = { }
        for i in range(self._mapTsetTbl.height()):
            drawTset = self._mapTsetTbl[i,0].val()
            # Estimate the number of palettes for this map tileset
            if i == 31:
                k = 0xDAFAA7 - self._palPtrTbl[i,0].val()
            else:
                k = self._palPtrTbl[i+1,0].val() - self._palPtrTbl[i,0].val()
            k /= 0xc0
            # Add the palettes
            romLoc = self._palPtrTbl[i,0].val() - 0xDA0000
            for j in range(k):
                # Read the palette
                self._tsets[drawTset].readPaletteFromRom(rom, i, j,
                        0x1A0000 + romLoc)
                # Add to the dict (format: (tset#, mtset#, pal#))
                palLocs[romLoc] = (drawTset, i, j)
                romLoc += 0xc0

        # Now convert all the "alternate addresses" in the MapPalettes to
        # palette numbers
        for ts in self._tsets:
            for (mt,mp,p) in ts.pals:
                if p.altAddr != 0:
                    altTs, altMtset, altPal = palLocs[p.altAddr]
                    p.altMapTileset = altMtset
                    p.altMapPalette = altPal

    def writeToProject(self, resourceOpener):
        i=0
        for tset in self._tsets:
            with resourceOpener('Tilesets/' + str(i).zfill(2), 'fts') as f:
                tset.writeToProject(f)
            i += 1
