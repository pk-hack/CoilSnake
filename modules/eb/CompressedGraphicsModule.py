import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import DataBlock, EbCompressedData
from modules.Progress import updateProgress

from array import array
from PIL import Image

#<Penguin> found it. VHOPPPCC CCCCCCCC
#<Penguin> v for vertical flip, h for horizontal flip, o for priority bit, p for
#          palette number, c for tile id
class EbArrangement:
    # Width/Height is in tiles
    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._arrBuf = [0] * width * height
    def readFromBlock(self, block, loc=0):
        self._arrBuf = map(
            lambda x: block[loc+x] | (block[loc+x+1] << 8),
            range(0, self._width*self._height*2, 2))
    def writeToBlock(self, block, loc=0):
        for a in self._arrBuf:
            block[loc] = a & 0xff
            block[loc+1] = (a >> 8) & 0xff
            loc += 2
    def sizeBlock(self):
        return self._width * self._height * 2
    def width(self):
        return self._width
    def height(self):
        return self._height
    def __getitem__(self, key):
        x, y = key
        tile =  self._arrBuf[y*self._width + x]
        return ((tile & 0x8000 != 0), # Vertical Flip Flag
                (tile & 0x4000 != 0), # Horizontal Flip Flag
                (tile & 0x2000 != 0), # Priority Flag
                (tile & 0x1c00) >> 10, # Palette
                tile & 0x3ff) # Tile id
    def __setitem__(self, key, item):
        x, y = key
        vf, hf, pb, pal, tid = item
        self._arrBuf[y*self._width + x] = ((vf << 15) # Vertical Flip Flag
                | (hf << 14) # Horizontal Flip Flag
                | (pb << 13) # Priority Flag
                | ((pal & 0x7) << 10) # Palette
                | (tid & 0x3ff)) # Tile id
    def __eq__(self, other):
        return ((self._width == other._width)
                and (self._height == other._height)
                and (self._arrBuf == other._arrBuf))
    def toImage(self, gfx, pals):
        img = Image.new("P",
                (self.width() * gfx._tileSize,
                self.height() * gfx._tileSize),
                None)
        # Have to convert the palette from [[(r,g,b),(r,g,b)]] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x,y: x.__add__(list(y)),
                reduce(lambda x,y: x.__add__(y), pals.getData(), []), [])
        img.putpalette(rawPal)
        imgData = img.load()
        offx = offy = 0
        for y in xrange(0, self._height):
            offy = y * gfx._tileSize
            for x in xrange(0, self._width):
                offx = x * gfx._tileSize
                vf, hf, pb, pal, tid = self[x,y]
                pal *= pals._numColors
                tile = gfx[tid]
                for ty in xrange(0, gfx._tileSize):
                    for tx in xrange(0, gfx._tileSize):
                        px , py = tx, ty
                        if vf:
                            py = gfx._tileSize - py - 1
                        if hf:
                            px = gfx._tileSize - px - 1
                        imgData[offx+tx, offy+ty] = tile[px][py] + pal
        return img
    def readFromImage(self, img, pals, gfx):
        if len(pals) == 1:
            # Only one subpalette, don't need to do pal fitting
            palData = img.getpalette()
            for i in xrange(0, pals.palSize()):
                pals[0,i] = (palData[i*3], palData[i*3+1], palData[i*3+2])
            for ty in xrange(self.height()):
                for tx in range(self.width()):
                    vf, hf, tid = gfx.setFromImage(
                            img,
                            tx * gfx._tileSize, ty * gfx._tileSize,
                            pals, 0, indexed=True)
                    self[tx,ty] = (vf, hf, False, 0, tid)
            del(img)
        else:
            # Need to do subpalette filling
            imgRGB = img.convert("RGB")
            del(img)

            for ty in xrange(self.height()):
                for tx in xrange(self.width()):
                    subPalNum = pals.addColorsFromTile(
                            imgRGB,
                            tx * gfx._tileSize, ty * gfx._tileSize,
                            gfx._tileSize, gfx._tileSize)
                    vf, hf, tid = gfx.setFromImage(
                            imgRGB,
                            tx * gfx._tileSize, ty * gfx._tileSize,
                            pals, subPalNum)
                    self[tx,ty] = (vf, hf, False, subPalNum, tid)
            del(imgRGB)
            pals.fill()

class EbTileGraphics:
    def __init__(self, numTiles, tileSize, bpp=2):
        self._numTiles = numTiles
        self._tileSize = tileSize
        self._tiles = [ ] 
        self._usedTiles = 0
        self._usedDict = dict()
        self._bpp = bpp
    def __eq__(self, other):
        return ((self._numTiles == other._numTiles)
                and (self._tileSize == other._tileSize)
                and (self._tiles == other._tiles))
    def readFromBlock(self, block, loc=0):
        off = loc
        self._tiles = []
        for i in xrange(self._numTiles):
            try:
                tile = [array('B', [0]*self._tileSize)
                        for i in xrange(self._tileSize)]
                if self._bpp == 2:
                    off += EbModule.read2BPPArea(
                        tile, block._data, off, 0, 0)
                elif self._bpp == 4:
                    off += EbModule.read4BPPArea(
                        tile, block._data, off, 0, 0)
                elif self._bpp == 8:
                    off += EbModule.read8BPPArea(
                            tile, block._data, off, 0, 0)
            except IndexError:
                pass # Load an empty tile if it's out of range of the data
            self._tiles.append(tile)
        self._usedTiles = self._numTiles
    def writeToBlock(self, block, loc=0):
        for t in self._tiles:
            if self._bpp == 2:
                loc += EbModule.write2BPPArea(
                        t, block._data, loc, 0, 0)
            elif self._bpp == 4:
                loc += EbModule.write4BPPArea(
                        t, block._data, loc, 0, 0)
            elif self._bpp == 8:
                loc += EbModule.write8BPPArea(
                        t, block._data, loc, 0, 0)
    def sizeBlock(self):
        if self._bpp == 2:
            return 16 * self._numTiles
        elif self._bpp == 4:
            return 32 * self._numTiles
        elif self._bpp == 8:
            return 64 * self._numTiles
    # Returns the tile number
    def setFromImage(self, img, x, y, pals, palNum, indexed=False):
        # Check for normal tile
        newTile = None
        imgData = img.load()
        if indexed:
            newTile = [
                    array('B',
                        [ imgData[i,j]
                            for j in xrange(y, self._tileSize + y) ])
                        for i in xrange(x, self._tileSize + x) ]
        else:
            newTile = [
                    array('B',
                        [ pals.getColorFromRGB(palNum,imgData[i,j])
                            for j in xrange(y, self._tileSize + y) ])
                        for i in xrange(x, self._tileSize + x) ]
        # Note: newTile is an array of columns

        # Check for non-flipped tile
        try:
            tIndex = self._usedDict[EbModule.hashArea(newTile)]
            return (False, False, tIndex)
        except KeyError:
            pass

        # Check for only horizontally flipped tile
        try:
            tIndex = self._usedDict[EbModule.hashArea(reversed(newTile))]
            return (False, True, tIndex)
        except KeyError:
            pass

        # Check for vertically and horizontally flipped tile
        for col in newTile:
            col.reverse()
        try:
            tIndex = self._usedDict[EbModule.hashArea(reversed(newTile))]
            return (True, True, tIndex)
        except KeyError:
            pass

        # Check for only vertically flipped tile
        tH = EbModule.hashArea(newTile)
        try:
            tIndex = self._usedDict[tH]
            return (True, False, tIndex)
        except KeyError:
            pass

        # We need to add a new tile
        if self._usedTiles >= self._numTiles:
            # TODO ERROR: Not enough room for a new tile
            return (False, False, 0)
        # Remember, newTile is still vflipped
        self._tiles.append(newTile)
        self._usedDict[tH] = self._usedTiles
        self._usedTiles += 1
        return (True, False, self._usedTiles-1)
    # For dumping a simple raw compressed graphic
    def dumpToImage(self, pal, width=16):
        height = self._numTiles / width
        img = Image.new("P",
                (width * self._tileSize,
                height * self._tileSize),
                None)
        # Have to convert the palette from [[(r,g,b),(r,g,b)]] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x,y: x.__add__(list(y)), pal, [])
        img.putpalette(rawPal)
        imgData = img.load()
        offx = offy = 0
        for y in xrange(0, height):
            offy = y * self._tileSize
            for x in xrange(0, width):
                offx = x * self._tileSize
                tile = self._tiles[x + y * width]
                for ty in xrange(0, self._tileSize):
                    for tx in xrange(0, self._tileSize):
                        imgData[offx+tx, offy+ty] = tile[tx][ty]
        return img
    # For loading a simple raw compressed graphic
    def loadFromImage(self, img):
        imgData = img.load()
        width, height = img.size
        # For removing subpalette info
        mask = pow(2, self._bpp) - 1
        # Load the tiles
        for y in xrange(0, height, self._tileSize):
            for x in xrange(0, width, self._tileSize):
                newTile = [ array('B', [ (imgData[i,j] & mask)
                    for j in xrange(y, self._tileSize + y) ])
                    for i in xrange(x, self._tileSize + x) ]
                self._tiles.append(newTile)
    def tileSize(self):
        return self._tileSize
    def __getitem__(self, key):
        return self._tiles[key]

def _uniques(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

class EbPalettes:
    def __init__(self, numPalettes, numColors):
        self._numPalettes = numPalettes
        self._numColors = numColors
        self._pals = [ [ (-1,-1,-1) for i in range(numColors) ]
                for i in range(numPalettes) ]
    def __eq__(self, other):
        if other == None:
            return False
        else:
            return ((self._numPalettes == other._numPalettes)
                    and (self._numColors == other._numColors)
                    and (self._pals == other._pals))
    def set(self, subpalNum, colors):
        self._pals[subpalNum] = colors
    def getSubpal(self, subpalNum):
        return self._pals[subpalNum]
    def readFromBlock(self, block, loc=0):
        self._pals = map(
                lambda x: EbModule.readPalette(
                    block, loc+x, self._numColors),
                range(0, self._numPalettes*self._numColors*2,
                    self._numColors*2))
    def writeToBlock(self, block, loc=0):
        for p in self._pals:
            EbModule.writePalette(block, loc, p)
            loc += self._numColors * 2
    def loadFromImage(self, img):
        palData = img.getpalette()
        m = 0
        for j in range(self._numPalettes):
            for k in range(self._numColors):
                self[j,k] = (palData[m], palData[m+1], palData[m+2])
                m += 3
    def sizeBlock(self):
        return 2 * self._numColors * self._numPalettes
    # Adjusts the palette so the the colors in a given portion of an image are
    # added to this palette such that all the colors in the tile can be
    # found in a single subpalette
    # Returns the subpalette number to use for this tile
    def addColorsFromTile(self, img, x, y, width, height):
        # Set of unique colors in this tile
        # List of colors in this tile
        imgData = img.load()
        colors = [imgData[i,j]
                for i in range(x,x+width)
                for j in range(y,y+height)]
        # Remove least sig 3 bits, since they aren't used in ROM
        colors = map(lambda (r,g,b): (r&0xf8, g&0xf8, b&0xf8), colors)
        # Set of unique colors from the list of colors
        uniqueColors = set(_uniques(colors))
        if len(uniqueColors) > self._numColors:
            # TODO Handle this error better
            #raise RuntimeError("ERROR: Too many colors in a single palette")
            return 0
        # sorted( [(# shared colors, # empty colors, new colors, pal)] )[0]
        tmp = sorted(
                filter(
                    lambda (nsc, nec, newC, p): nec >= len(newC),
                    map(
                        lambda x: (
                            len(uniqueColors.intersection(x)), # Num shared
                            x.count((-1,-1,-1)), # Num free colors in palette
                            uniqueColors - set(x), # Set of colors not in palette
                            x), # Palette
                        self._pals)),
                    reverse=True)
        if len(tmp) == 0:
            # TODO ERROR: Not enough room to put these colors in a subpalette
            return 0
        numShared, numFree, newColors, pal = tmp[0]
        # Insert new colors into palette
        for newColor in newColors:
            for i in range(0, self._numColors):
                if pal[i] == (-1,-1,-1):
                    pal[i] = newColor
                    break
        return self._pals.index(pal)
    def getColorFromRGB(self, palNum, (r,g,b)):
        # Remove least sig 3 bits, since they aren't used in ROM
        rgb = (r&0xf8, g&0xf8, b&0xf8)
        try:
            return self._pals[palNum].index(rgb)
        except ValueError:
            # TODO ERROR: Color not in palette
            return 0
    def fill(self):
        for pal in self._pals:
            for i in range(self._numColors):
                if pal[i] == (-1,-1,-1):
                    pal[i] = (0,0,0)
    def __getitem__(self, key):
        palNum, colorNum = key
        return self._pals[palNum][colorNum]
    def __setitem__(self, key, val):
        palNum, colorNum = key
        (r,g,b) = val
        self._pals[palNum][colorNum] = (r&0xf8, g&0xf8, b&0xf8)
    def getData(self):
        return self._pals
    def getFlatColors(self):
        return reduce(lambda x,y: x.__add__(list(y)), self._pals, [])
    def __len__(self):
        return self._numPalettes
    def palSize(self):
        return self._numColors

class EbTownMap:
    def __init__(self, name, ptrLoc):
        self._name = name
        self._ptrLoc = ptrLoc
        self._gfx = EbTileGraphics(512, 8, 4)
        self._arr = EbArrangement(32, 28)
        self._pals = EbPalettes(2, 16)
    def readFromRom(self, rom):
        with EbCompressedData() as block:
            block.readFromRom(rom, EbModule.toRegAddr(
                    rom.readMulti(self._ptrLoc, 4)))
            self._arr.readFromBlock(block, 64)
            self._pals.readFromBlock(block, 0)
            self._gfx.readFromBlock(block, 2048+64)
    def writeToRom(self, rom):
        # Arrangement space is 2048 bytes long since it's 32x32x2 in VRAM
        with EbCompressedData(self._pals.sizeBlock() + 2048 +
                self._gfx.sizeBlock()) as block:
            self._pals.writeToBlock(block, 0)
            self._arr.writeToBlock(block, 64)
            self._gfx.writeToBlock(block, 2048+64)
            newAddr = block.writeToFree(rom)
            rom.writeMulti(self._ptrLoc, EbModule.toSnesAddr(newAddr), 4)
    def writeToProject(self, resourceOpener):
        img = self._arr.toImage(self._gfx, self._pals)
        imgFile = resourceOpener(self.name(), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
    def readFromProject(self, resourceOpener):
        img = Image.open(resourceOpener(self.name(), 'png'))
        if img.mode != 'P':
            raise RuntimeError(self.name() + " is not an indexed PNG.")
        # The game has problems if you try to use color 0 of subpal 1
        #   directly after using color 0 of subpal 0
        self._pals[1,0] = (0,0,0)
        self._arr.readFromImage(img, self._pals, self._gfx)
    def name(self):
        return self._name

class EbLogo:
    def __init__(self, name, gfxPtrLoc, arrPtrLoc, palPtrLoc):
        self._name = name

        self._gfx = EbTileGraphics(256, 8)
        self._arr = EbArrangement(32, 28)
        self._pals = EbPalettes(5, 4)

        self._gfxPtrLoc = gfxPtrLoc
        self._arrPtrLoc = arrPtrLoc
        self._palPtrLoc = palPtrLoc
    def readFromRom(self, rom):
        with EbCompressedData() as gb:
            gb.readFromRom(rom, EbModule.toRegAddr(
                EbModule.readAsmPointer(rom, self._gfxPtrLoc)))
            self._gfx.readFromBlock(gb)
        with EbCompressedData() as ab:
            ab.readFromRom(rom, EbModule.toRegAddr(
                EbModule.readAsmPointer(rom, self._arrPtrLoc)))
            self._arr.readFromBlock(ab)
        with EbCompressedData() as pb:
            pb.readFromRom(rom, EbModule.toRegAddr(
                EbModule.readAsmPointer(rom, self._palPtrLoc)))
            self._pals.readFromBlock(pb)
        
        # The first color of every subpalette after subpal0 is ignored and
        # drawn as the first color of subpal0 instead
        c = self._pals[0,0]
        for i in range(1,len(self._pals)):
            self._pals[i,0] = c
    def writeToProject(self, resourceOpener):
        img = self._arr.toImage(self._gfx, self._pals)
        imgFile = resourceOpener(self.name(), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
    def writeToRom(self, rom):
        with EbCompressedData(self._gfx.sizeBlock()) as gb:
            self._gfx.writeToBlock(gb)
            EbModule.writeAsmPointer(rom, self._gfxPtrLoc,
                    EbModule.toSnesAddr(gb.writeToFree(rom)))
        with EbCompressedData(self._arr.sizeBlock()) as ab:
            self._arr.writeToBlock(ab)
            EbModule.writeAsmPointer(rom, self._arrPtrLoc,
                    EbModule.toSnesAddr(ab.writeToFree(rom)))
        with EbCompressedData(self._pals.sizeBlock()) as pb:
            self._pals.writeToBlock(pb)
            EbModule.writeAsmPointer(rom, self._palPtrLoc,
                    EbModule.toSnesAddr(pb.writeToFree(rom)))
    def readFromProject(self, resourceOpener):
        img = Image.open(resourceOpener(self.name(), 'png'))
        if img.mode != 'P':
            raise RuntimeError(self.name() + " is not an indexed PNG.")
        # Set all first colors of each subpalette to the image's first color
        pal = img.getpalette()
        firstColor = (pal[0], pal[1], pal[2])
        for i in range(1,len(self._pals)):
            self._pals[i,0] = firstColor
        self._arr.readFromImage(img, self._pals, self._gfx)
    def name(self):
        return self._name

class CompressedGraphicsModule(EbModule.EbModule):
    _name = "Compressed Graphics"
    TOWN_MAP_PTRS = zip(
            map(lambda x: "TownMaps/" + x,
                ["Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers"]),
            range(0x202190, 0x202190 + 0x18 * 4, 4))
    _ASMPTR_TOWN_MAP_ICON_GFX = 0x4d62f
    _ASMPTR_TOWN_MAP_ICON_PAL = 0x4d5c4
    _TOWN_MAP_ICON_PREVIEW_SUBPALS = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,

            0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,

            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,

            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,

            1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,

            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    _ASMPTR_PRODUCED_GFX = 0x4dd73
    _ASMPTR_PRODUCED_ARR = 0x4dd3a
    _ASMPTR_PRODUCED_PAL = 0x4dd9f
    _ASMPTR_PRESENTED_GFX = 0x4de1b
    _ASMPTR_PRESENTED_ARR = 0x4dde2
    _ASMPTR_PRESENTED_PAL = 0x4de47
    _ASMPTR_GAS_GFX = 0xf0f0
    _ASMPTR_GAS_ARR = 0xf11b
    _ASMPTR_GAS_PAL1 = 0xf147
    _ASMPTR_GAS_PAL2 = 0xf3ba
    _ASMPTR_GAS_PAL3 = 0xf3f0
    def __init__(self):
        self._logos = [
                EbLogo("Logos/Nintendo", 0xeea3, 0xeebb, 0xeed3),
                EbLogo("Logos/APE", 0xeefb, 0xef13, 0xef2b),
                EbLogo("Logos/HALKEN", 0xef52, 0xef6a, 0xef82)
                ]

        self._townmaps = map(lambda (x,y): EbTownMap(x, y),
                self.TOWN_MAP_PTRS)
        self._townmap_icons = EbTileGraphics(288, 8, 4)
        self._townmap_icons_pal = EbPalettes(2, 16)

        self._produced_gfx = EbTileGraphics(256, 8)
        self._produced_arr = EbArrangement(32, 32)
        self._produced_pal = EbPalettes(1, 4)
        self._presented_gfx = EbTileGraphics(256, 8)
        self._presented_arr = EbArrangement(32, 32)
        self._presented_pal = EbPalettes(1, 4)

        self._gas_gfx = EbTileGraphics(632, 8, 8)
        self._gas_arr = EbArrangement(32, 32)
        self._gas_pal1 = EbPalettes(1, 256)
        self._gas_pal2 = EbPalettes(1, 256)
        self._gas_pal3 = EbPalettes(1, 256)

        self._pct = 50.0/(len(self._logos) + len(self._townmaps) + 1 + 2 + 1)
    def free(self):
        del(self._logos)
        del(self._townmaps)
    def readTownMapIconsFromRom(self, rom):
        self._townmap_icons_pal.readFromBlock(rom,
                loc=EbModule.toRegAddr(
                    EbModule.readAsmPointer(rom,
                        self._ASMPTR_TOWN_MAP_ICON_PAL)))
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_TOWN_MAP_ICON_GFX)))
            self._townmap_icons.readFromBlock(cb)
    def readProducedPresentedFromRom(self, rom):
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_PRODUCED_PAL)))
            self._produced_pal.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_PRODUCED_GFX)))
            self._produced_gfx.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_PRODUCED_ARR)))
            self._produced_arr.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_PRESENTED_PAL)))
            self._presented_pal.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_PRESENTED_GFX)))
            self._presented_gfx.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_PRESENTED_ARR)))
            self._presented_arr.readFromBlock(cb)
    def readGasFromRom(self, rom):
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_GAS_GFX)))
            self._gas_gfx.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_GAS_ARR)))
            self._gas_arr.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_GAS_PAL1)))
            self._gas_pal1.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_GAS_PAL2)))
            self._gas_pal2.readFromBlock(cb)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                    EbModule.toRegAddr(
                        EbModule.readAsmPointer(rom,
                        self._ASMPTR_GAS_PAL3)))
            self._gas_pal3.readFromBlock(cb)
    def readFromRom(self, rom):
        for logo in self._logos:
            logo.readFromRom(rom)
            updateProgress(self._pct)
        for tmap in self._townmaps:
            tmap.readFromRom(rom)
            updateProgress(self._pct)

        self.readTownMapIconsFromRom(rom)
        updateProgress(self._pct)
        self.readProducedPresentedFromRom(rom)
        updateProgress(self._pct * 2)
        self.readGasFromRom(rom)
        updateProgress(self._pct)
    def freeRanges(self):
        return [(0x2021a8, 0x20ed02), # Town Map data
                (0x214ec1, 0x21ae7b), # Company Logos, Prod/Pres, and Gas
                (0x21ea50, 0x21f203)] # Town map icon GFX and pal
    def writeToRom(self, rom):
        for logo in self._logos:
            logo.writeToRom(rom)
            updateProgress(self._pct)
        for tmap in self._townmaps:
            tmap.writeToRom(rom)
            updateProgress(self._pct)

        with DataBlock(self._townmap_icons_pal.sizeBlock()) as b:
            self._townmap_icons_pal.writeToBlock(b)
            EbModule.writeAsmPointer(rom, self._ASMPTR_TOWN_MAP_ICON_PAL,
                    EbModule.toSnesAddr(b.writeToFree(rom)))
        with EbCompressedData(self._townmap_icons.sizeBlock()) as cb:
            self._townmap_icons.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_TOWN_MAP_ICON_GFX,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        updateProgress(self._pct)

        with EbCompressedData(self._produced_pal.sizeBlock()) as cb:
            self._produced_pal.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_PRODUCED_PAL,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._produced_gfx.sizeBlock()) as cb:
            self._produced_gfx.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_PRODUCED_GFX,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._produced_arr.sizeBlock()) as cb:
            self._produced_arr.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_PRODUCED_ARR,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        updateProgress(self._pct)
        with EbCompressedData(self._presented_pal.sizeBlock()) as cb:
            self._presented_pal.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_PRESENTED_PAL,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._presented_gfx.sizeBlock()) as cb:
            self._presented_gfx.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_PRESENTED_GFX,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._presented_arr.sizeBlock()) as cb:
            self._presented_arr.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_PRESENTED_ARR,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        updateProgress(self._pct)

        with EbCompressedData(self._gas_gfx.sizeBlock()) as cb:
            self._gas_gfx.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_GAS_GFX,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._gas_arr.sizeBlock()) as cb:
            self._gas_arr.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_GAS_ARR,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._gas_pal1.sizeBlock()) as cb:
            self._gas_pal1.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_GAS_PAL1,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._gas_pal2.sizeBlock()) as cb:
            self._gas_pal2.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_GAS_PAL2,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        with EbCompressedData(self._gas_pal3.sizeBlock()) as cb:
            self._gas_pal3.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_GAS_PAL3,
                    EbModule.toSnesAddr(cb.writeToFree(rom)))
        updateProgress(self._pct)
    def writeTownMapIconsToProject(self, resourceOpener):
        arr = EbArrangement(16, 18)
        for i in range(16*18):
            arr[i%16, i/16] = (False, False, False,
                    self._TOWN_MAP_ICON_PREVIEW_SUBPALS[i], i)
        img = arr.toImage(self._townmap_icons, self._townmap_icons_pal)
        with resourceOpener("TownMaps/icons", "png") as imgFile:
            img.save(imgFile, "png")
            imgFile.close()
    def writeProducedPresentedToProject(self, resourceOpener):
        img = self._produced_arr.toImage(
                self._produced_gfx, self._produced_pal)
        with resourceOpener("Logos/ProducedBy", "png") as imgFile:
            img.save(imgFile, 'png')
            imgFile.close()
        img = self._presented_arr.toImage(
                self._presented_gfx, self._presented_pal)
        with resourceOpener("Logos/PresentedBy", "png") as imgFile:
            img.save(imgFile, 'png')
            imgFile.close()
    def writeGasToProject(self, resourceOpener):
        img = self._gas_arr.toImage(
                self._gas_gfx, self._gas_pal1)
        with resourceOpener("Logos/GasStation1", "png") as imgFile:
            img.save(imgFile, 'png')
            imgFile.close()
        img = self._gas_arr.toImage(
                self._gas_gfx, self._gas_pal2)
        with resourceOpener("Logos/GasStation2", "png") as imgFile:
            img.save(imgFile, 'png')
            imgFile.close()
        img = self._gas_arr.toImage(
                self._gas_gfx, self._gas_pal3)
        with resourceOpener("Logos/GasStation3", "png") as imgFile:
            img.save(imgFile, 'png')
            imgFile.close()
    def writeToProject(self, resourceOpener):
        for logo in self._logos:
            logo.writeToProject(resourceOpener)
            updateProgress(self._pct)
        for tmap in self._townmaps:
            tmap.writeToProject(resourceOpener)
            updateProgress(self._pct)

        self.writeTownMapIconsToProject(resourceOpener)
        updateProgress(self._pct)
        self.writeProducedPresentedToProject(resourceOpener)
        updateProgress(self._pct * 2)
        self.writeGasToProject(resourceOpener)
        updateProgress(self._pct)
    def readFromProject(self, resourceOpener):
        for logo in self._logos:
            logo.readFromProject(resourceOpener)
            updateProgress(self._pct)
        for tmap in self._townmaps:
            tmap.readFromProject(resourceOpener)
            updateProgress(self._pct)

        with resourceOpener("TownMaps/icons", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("TownMaps/icons is not an indexed PNG.")
            self._townmap_icons.loadFromImage(img)
            self._townmap_icons_pal.loadFromImage(img)
        updateProgress(self._pct)

        with resourceOpener("Logos/ProducedBy", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("Logos/ProducedBy is not an indexed PNG.")
            self._produced_pal.loadFromImage(img)
            self._produced_arr.readFromImage(img, self._produced_pal,
                    self._produced_gfx)
        updateProgress(self._pct)
        with resourceOpener("Logos/PresentedBy", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("Logos/PresentedBy is not an indexed PNG.")
            self._presented_pal.loadFromImage(img)
            self._presented_arr.readFromImage(img, self._presented_pal, 
                    self._presented_gfx)
        updateProgress(self._pct)

        with resourceOpener("Logos/GasStation1", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("Logos/GasStation1 is not an indexed PNG.")
            self._gas_arr.readFromImage(img, self._gas_pal1, self._gas_gfx)
        with resourceOpener("Logos/GasStation2", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("Logos/GasStation2 is not an indexed PNG.")
            self._gas_pal2.loadFromImage(img)
        with resourceOpener("Logos/GasStation3", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("Logos/GasStation3 is not an indexed PNG.")
            self._gas_pal3.loadFromImage(img)
        updateProgress(self._pct)
    def upgradeProject(self, oldVersion, newVersion, rom, resourceOpenerR,
            resourceOpenerW):
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion <= 2:
            self.readTownMapIconsFromRom(rom)
            self.writeTownMapIconsToProject(resourceOpenerW)

            self.readProducedPresentedFromRom(rom)
            self.writeProducedPresentedToProject(resourceOpenerW)

            self.readGasFromRom(rom)
            self.writeGasToProject(resourceOpenerW)

            self.upgradeProject(3, newVersion, rom, resourceOpenerR,
                                        resourceOpenerW)
        else:
            self.upgradeProject(oldVersion+1, newVersion, rom, resourceOpenerR,
                                                            resourceOpenerW)
