import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import EbCompressedData, DataBlock
from CompressedGraphicsModule import EbTileGraphics
from modules.Progress import updateProgress

from array import array
from zlib import crc32
from re import sub
import yaml

chars = "0123456789abcdefghijklmnopqrstuv"

# Just a palette with 6 subpals and hidden data
class MapPalette:
    def __init__(self):
        self.flag = 0
        self.flagPal = None
        self.flagPalPtr = 0
        self.spritePalNum = 0
        self.flashEffect = 0
        self.subpals = None
        self.flagPal = None
    def readFromRom(self, rom, addr, getFlagPal=True):
        self.flag = rom.readMulti(addr, 2)
        if (self.flag != 0) and getFlagPal:
            altAddr = rom.readMulti(addr + 0x20, 2)
            self.flagPal = MapPalette()
            self.flagPal.readFromRom(rom, altAddr | 0x1a0000, getFlagPal=False)
        self.spritePalNum = rom.read(addr + 0x40)
        self.flashEffect = rom.read(addr + 0x60)
        self.subpals = map(lambda x: EbModule.readPalette(rom, x, 16),
                range(addr, addr+32*6, 32))
        for subp in self.subpals:
            subp[0] = (0,0,0)
    def dump(self):
        out = dict()
        out["Event Flag"] = self.flag
        if self.flag != 0:
            out["Event Palette"] = self.flagPal.getAsString()
        out["Sprite Palette"] = self.spritePalNum
        out["Flash Effect"] = self.flashEffect
        return out
    def writeToBlock(self, block, addr):
        i=0
        for subp in self.subpals:
            EbModule.writePalette(block, addr + i, subp)
            i += 32
        #block.writeMulti(addr, self.flag, 2)
        #block.writeMulti(addr+0x20, self.flagPalPtr, 2)
        block[addr] = self.flag & 0xff
        block[addr+1] = self.flag >> 8
        block[addr+0x20] = self.flagPalPtr & 0xff
        block[addr+0x21] = self.flagPalPtr >> 8
        block[addr+0x40] = self.spritePalNum
        block[addr+0x60] = self.flashEffect
        return 0xc0
    def getAsString(self):
        out = str()
        for subp in self.subpals:
            for (r,g,b) in subp:
                out += chars[r>>3]
                out += chars[g>>3]
                out += chars[b>>3]
        return out
    def setFromString(self, s):
        self.subpals = []
        i=0
        for j in range(6):
            subpal = []
            for k in range(16):
                subpal.append((
                        int(s[i],32)<<3,
                        int(s[i+1],32)<<3,
                        int(s[i+2],32)<<3))
                i += 3
            subpal[0] = (0,0,0)
            self.subpals.append(subpal)

class Tileset:
    def __init__(self):
        self.tg = EbTileGraphics(896, 8, 4)
        self.tg._tiles = [ None ] * 896
        self.arr = [None for i in range(0,1024)]
        self.col = [None for i in range(0,1024)]
        self.pals = [ ]
    def readMinitilesFromRom(self, rom, addr):
        with EbCompressedData() as tgb:
            tgb.readFromRom(rom, addr)
            self.tg.readFromBlock(tgb)
    def writeMinitilesToFree(self, rom):
        with EbCompressedData(self.tg.sizeBlock()) as tgb:
            self.tg.writeToBlock(tgb)
            return tgb.writeToFree(rom)
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
    def writeArrangementsToFree(self, rom):
        with EbCompressedData(1024*16*2) as ab:
            i=0
            for a in self.arr:
                for j in range(4):
                    for k in range(4):
                        ab[i] = a[k][j] & 0xff
                        ab[i+1] = a[k][j] >> 8
                        i += 2
            return ab.writeToFree(rom)
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
                    s += chars[t[i][j]]
            return s
    def setTileFromString(self, n, s):
        if n < 896:
            strVals = map(lambda x: int(x,32), s)
            k=0
            tile = [array('B', [0]*8) for i in xrange(8)]
            for j in xrange(8):
                for i in xrange(8):
                    tile[i][j] = strVals[k]
                    k += 1
            self.tg._tiles[n] = tile
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
    def setArrFromString(self, n, s):
        i=0
        self.arr[n] = [ [0 for y in range(4)] for z in range(4) ]
        self.col[n] = array('B', [0]*16)
        for j in xrange(4):
            for k in xrange(4):
                self.arr[n][k][j] = int(s[i:i+4], 16)
                self.col[n][j*4+k] = int(s[i+4:i+6], 16)
                i += 6
    def writeToFTS(self, file):
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
    def hasMapTileset(self, mt):
        for (mt2,mp,pal) in self.pals:
            if mt == mt2:
                return True
        return False
    def readFromFTS(self, file):
        for i in range(512):
            self.setTileFromString(i, file.readline()[:-1])
            self.setTileFromString(i^512, file.readline()[:-1])
            file.readline()
        file.readline()

        while True:
            line = file.readline()
            if line == "\n":
                break
            mt = int(line[0], 32)
            mp = int(line[1], 32)
            pal = MapPalette()
            pal.setFromString(line[2:-1])
            self.pals.append((mt,mp,pal))
        file.readline()

        for i in range(1024):
            self.setArrFromString(i, file.readline()[:-1])


class TilesetModule(EbModule.EbModule):
    _name = "Tilesets"

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._gfxPtrTbl = EbTable(0xEF105B)
        self._arrPtrTbl = EbTable(0xEF10AB)
        self._colPtrTbl = EbTable(0xEF117B)
        self._mapTsetTbl = EbTable(0xEF101B)
        self._palPtrTbl = EbTable(0xEF10FB)
        self._tsets = [Tileset() for i in range(20)]
    def freeRanges(self):
        return [(0x17c600, 0x17fbe7),
                (0x190000, 0x19fc17),
                (0x1b0000, 0x1bf2ea),
                (0x1c0000, 0x1cd636),
                (0x1d0000, 0x1dfecd),
                (0x1e0000, 0x1ef0e6),
                (0x1f0000, 0x1fc242)]
    def readFromRom(self, rom):
        self._gfxPtrTbl.readFromRom(rom)
        updateProgress(2)
        self._arrPtrTbl.readFromRom(rom)
        updateProgress(2)
        self._colPtrTbl.readFromRom(rom)
        updateProgress(2)
        self._mapTsetTbl.readFromRom(rom)
        updateProgress(2)
        self._palPtrTbl.readFromRom(rom)
        updateProgress(2)

        # Read tilesets
        pct = 30.0/len(self._tsets)
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
            updateProgress(pct)

        # Read palettes
        pct = 10.0/self._mapTsetTbl.height()
        for i in range(self._mapTsetTbl.height()):
            drawTset = self._mapTsetTbl[i,0].val()
            # Each map tset has 8 maximum palettes
            # We'll just assume they all use 8 and read the garbage
            #romLoc = self._palPtrTbl[i,0].val()
            #for j in xrange(8):
            #    # Read the palette
            #    self._tsets[drawTset].readPaletteFromRom(rom, i, j,
            #            EbModule.toRegAddr(romLoc))
            #    romLoc += 0xc0

            # OK, as it turns out, all palettes need to be in the 1A bank
            # So we actually need to conserve space and not read garbage
            # Estimate the number of palettes for this map tileset
            if i == 31:
                #k = 0xDAFAA7 - self._palPtrTbl[i,0].val()
                k = 8
            else:
                k = self._palPtrTbl[i+1,0].val() - self._palPtrTbl[i,0].val()
                k /= 0xc0
            # Add the palettes
            romLoc = EbModule.toRegAddr(self._palPtrTbl[i,0].val())
            for j in range(k):
                # Read the palette
                self._tsets[drawTset].readPaletteFromRom(rom, i, j, romLoc)
                romLoc += 0xc0
            updateProgress(pct)

    def writeToRom(self, rom):
        numTsets = len(self._tsets)
        self._gfxPtrTbl.clear(numTsets)
        self._arrPtrTbl.clear(numTsets)
        self._colPtrTbl.clear(numTsets)
        self._mapTsetTbl.clear(32)
        self._palPtrTbl.clear(32)

        # Write gfx & arrs
        pct = 30.0/numTsets
        i=0
        for tset in self._tsets:
            self._gfxPtrTbl[i,0].setVal(EbModule.toSnesAddr(
                tset.writeMinitilesToFree(rom)))
            self._arrPtrTbl[i,0].setVal(EbModule.toSnesAddr(
               tset.writeArrangementsToFree(rom)))
            i += 1
            updateProgress(pct)
        self._gfxPtrTbl.writeToRom(rom)
        updateProgress(2)
        self._arrPtrTbl.writeToRom(rom)
        updateProgress(2)

        # Write collissions
        pct = 6.0/numTsets
        colLocs = dict()
        colWriteLoc = 0x180000
        colRangeEnd = 0x18f05d
        i=0
        for tset in self._tsets:
            with DataBlock(len(tset.col)*2) as colTable:
                j=0
                for c in tset.col:
                    hash = crc32(c)
                    try:
                        addr = colLocs[hash]
                    except KeyError:
                        if (colWriteLoc + 16) > colRangeEnd:
                            # TODO Error, not enough space for collisions
                            print "Ran out of collision space"
                            raise Exception
                        else:
                            colLocs[hash] = colWriteLoc
                            addr = colWriteLoc
                            rom.write(colWriteLoc, c)
                            colWriteLoc += 16
                    colTable[j] = addr & 0xff
                    colTable[j+1] = (addr >> 8) & 0xff
                    j += 2
                self._colPtrTbl[i,0].setVal(EbModule.toSnesAddr(
                    colTable.writeToFree(rom)))
                i += 1
            updateProgress(pct)
        self._colPtrTbl.writeToRom(rom)
        updateProgress(1)

        # Write the palettes, they need to be in the DA bank
        pct = 7.0/32
        palWriteLoc = 0x1a0000
        palRangeEnd = 0x1afaa6 # can we go more?
        # Write maps/drawing tilesets associations and map tset pals
        for i in range(32): # For each map tileset
            # Find the drawing tileset number for this map tileset
            drawTset = -1
            j = 0
            for tset in self._tsets:
                for (mt,mp,pal) in tset.pals:
                    if mt == i:
                        drawTset = j
                        break
                if drawTset != -1:
                    break
                j += 1
            else:
                # TODO Error, this drawing tileset isn't associated
                drawTset = 0
            self._mapTsetTbl[i,0].setVal(drawTset)
            # Write the palette data for this map tileset
            mtset_pals = [(mp,pal) for (mt,mp,pal)
                    in self._tsets[drawTset].pals if mt == i]
            mtset_pals.sort()
            # Let's take the easy way out and just write redundant flag pals
            # This will waste space but oh well
            # First, write the flag pals
            for (mp,pal) in mtset_pals:
                if pal.flag != 0:
                    if palWriteLoc + 0xc0 > palRangeEnd:
                        # TODO Error, not enough space for all these palettes
                        raise RuntimeError("Too many palettes")
                    pal.flagPal.writeToBlock(rom, palWriteLoc)
                    pal.flagPalPtr = palWriteLoc & 0xffff
                    palWriteLoc += 0xc0
            self._palPtrTbl[i,0].setVal(EbModule.toSnesAddr(palWriteLoc))
            # Now write the regular pals
            for (mp,pal) in mtset_pals:
                if palWriteLoc + 0xc0 > palRangeEnd:
                    # TODO Error, not enough space for all these palettes
                    raise RuntimeError("Too many palettes")
                pal.writeToBlock(rom, palWriteLoc)
                palWriteLoc += 0xc0
            updateProgress(pct)
        self._mapTsetTbl.writeToRom(rom)
        updateProgress(1)
        self._palPtrTbl.writeToRom(rom)
        updateProgress(1)

        # Might as well use any extra leftover space
        ranges = [(colWriteLoc, colRangeEnd), (palWriteLoc, palRangeEnd)]
        ranges = [(a,b) for (a,b) in ranges if a < b]
        rom.addFreeRanges(ranges)

    def writeToProject(self, resourceOpener):
        # Dump an additional YML with color0 data
        out = dict()
        for i in range(0,32): # For each map tset
            entry = dict()
            tset = None
            for ts in self._tsets:
                if ts.hasMapTileset(i):
                    tset = ts
                    break
            for (pN,p) in [(mp,p) for (mt,mp,p) in tset.pals if mt == i]:
                entry[pN] = p.dump()
            out[i] = entry
        with resourceOpener('map_palette_settings', 'yml') as f:
            s = yaml.dump(out, default_flow_style=False,
                    Dumper=yaml.CSafeDumper)
            s = sub("Event Flag: (\d+)",
                    lambda i: "Event Flag: " + hex(int(i.group(0)[12:])), s)
            f.write(s)
        updateProgress(5)

        # Dump the FTS files
        pct=45.0/len(self._tsets)
        i=0
        for tset in self._tsets:
            with resourceOpener('Tilesets/' + str(i).zfill(2), 'fts') as f:
                tset.writeToFTS(f)
            i += 1
            updateProgress(pct)
    def readFromProject(self, resourceOpener):
        i=0
        pct = 45.0/len(self._tsets)
        for tset in self._tsets:
            with resourceOpener('Tilesets/' + str(i).zfill(2), 'fts') as f:
                tset.readFromFTS(f)
            i += 1
            updateProgress(pct)
        with resourceOpener('map_palette_settings', 'yml') as f:
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            for mtset in input: # For each map tileset
                # Get the draw (normal) tileset
                tset = None
                for ts in self._tsets:
                    if ts.hasMapTileset(mtset):
                        tset = ts
                        break
                # For each map palette
                mtset_pals = [(mp,p) for (mt,mp,p) in tset.pals if mt == mtset]
                for (pN,mtset_pal) in mtset_pals:
                    entry = input[mtset][pN]
                    mtset_pal.flag = entry["Event Flag"]
                    mtset_pal.flashEffect = entry["Flash Effect"]
                    mtset_pal.spritePalNum = entry["Sprite Palette"]
                    if mtset_pal.flag != 0:
                        mtset_pal.flagPal = MapPalette()
                        mtset_pal.flagPal.setFromString(entry["Event Palette"])
                        mtset_pal.flagPal.spritePalNum = entry["Sprite Palette"]
                updateProgress(5.0/32)
