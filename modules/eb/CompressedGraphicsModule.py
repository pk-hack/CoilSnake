import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import EbCompressedData, DataBlock

import array
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
                (self.width() * gfx.tileSize(),
                self.height() * gfx.tileSize()),
                None)
        # Have to convert the palette from [[(r,g,b),(r,g,b)]] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x,y: x.__add__(list(y)),
            reduce(lambda x,y: x.__add__(y), pals.getData(), []),
            [])
        img.putpalette(rawPal)
        for y in range(0, self.height()):
            for x in range(0, self.width()):
                vf, hf, pb, pal, tid = self[x,y]
                tile = gfx[tid]
                for ty in range(0, gfx.tileSize()):
                    for tx in range(0, gfx.tileSize()):
                        px , py = tx, ty
                        if vf:
                            py = gfx.tileSize() - py - 1
                        if hf:
                            px = gfx.tileSize() - px - 1
                        img.putpixel(
                            (x*gfx.tileSize() +tx,
                                y*gfx.tileSize()+ty),
                            tile[px][py] + pal*pals.palSize())
        return img
    def readFromImage(self, imgFname, pals, gfx):
        if len(pals) == 1:
            # Only one subpalette, don't need to do pal fitting
            img = Image.open(imgFname)
            palData = img.getpalette()
            imgData = img.getdata()
            imgW, imgH = img.size
            del(img)
            for i in range(0, pals.palSize()):
                pals[0,i] = (palData[i*3], palData[i*3+1], palData[i*3+2])
            for ty in range(self.height()):
                for tx in range(self.width()):
                    vf, hf, tid = gfx.setFromImage(
                            imgData, imgW,
                            tx * gfx.tileSize(), ty * gfx.tileSize(),
                            pals, 0, indexed=True)
                    self[tx,ty] = (vf, hf, False, 0, tid)
        else:
            # Need to do subpalette filling
            img = Image.open(imgFname)
            imgRGB = img.convert("RGB")
            del(img)
            imgRGB.load()
            imgData = list(imgRGB.getdata())
            imgW, imgH = imgRGB.size
            del(imgRGB)

            for ty in range(0, self.height()):
                for tx in range(0, self.width()):
                    subPalNum = pals.addColorsFromTile(
                            imgData, imgW,
                            tx * gfx.tileSize(), ty * gfx.tileSize(),
                            gfx.tileSize(), gfx.tileSize())
                    vf, hf, tid = gfx.setFromImage(
                            imgData, imgW,
                                tx * gfx.tileSize(), ty * gfx.tileSize(),
                            pals, subPalNum)
                    self[tx,ty] = (vf, hf, False, subPalNum, tid)
            pals.fill()

class EbTileGraphics:
    def __init__(self, numTiles, tileSize, bpp=2):
        self._numTiles = numTiles
        self._tileSize = tileSize
        self._tiles = [ ]
        self._usedTiles = 0
        self._bpp = bpp
    def __eq__(self, other):
        return ((self._numTiles == other._numTiles)
                and (self._tileSize == other._tileSize)
                and (self._tiles == other._tiles))
    def readFromBlock(self, block, loc=0):
        off = loc
        self._tiles = []
        for i in range(0, self._numTiles):
            try:
                tile = [array.array('B', [0]*self._tileSize)
                        for i in range(self._tileSize)]
                if self._bpp == 2:
                    off += EbModule.read2BPPArea(
                        tile, block, off, 0, 0)
                elif self._bpp == 4:
                    off += EbModule.read4BPPArea(
                        tile, block, off, 0, 0)
            except IndexError:
                pass # Load an empty tile if it's out of range of the data
            self._tiles.append(tile)
        self._usedTiles = self._numTiles
    def writeToBlock(self, block, loc=0):
        for t in self._tiles:
            if self._bpp == 2:
                loc += EbModule.write2BPPArea(
                        t, block, loc, 0, 0)
            elif self._bpp == 4:
                loc += EbModule.write4BPPArea(
                        t, block, loc, 0, 0)
    def sizeBlock(self):
        if self._bpp == 2:
            return 16 * self._numTiles
        elif self._bpp == 4:
            return 32 * self._numTiles
    # Returns the tile number
    def setFromImage(self, imgData, imgWidth, x, y, pals, palNum, indexed=False):
        # Check for normal tile
        newTile = None
        if indexed:
            newTile = [
                    array.array('B',
                        map(lambda j: imgData[j*imgWidth + i],
                            range(y, self._tileSize + y)))
                    for i in range(x, self._tileSize + x) ]
        else:
            newTile = [
                    array.array('B', map(
                        lambda j: pals.getColorFromRGB(
                            palNum,
                            imgData[j*imgWidth + i]),
                        range(y, self._tileSize + y)))
                    for i in range(x, self._tileSize + x) ]
        # Note: newTile is an array of columns

        # Check for non-flipped tile
        try:
            tIndex = self._tiles.index(newTile)
            return (False, False, tIndex)
        except ValueError:
            pass

        # Check for only horizontally flipped tile
        newTile.reverse()
        try:
            tIndex = self._tiles.index(newTile)
            return (False, True, tIndex)
        except ValueError:
            pass

        # Check for vertically and horizontally flipped tile
        for col in newTile:
            col.reverse()
        try:
            tIndex = self._tiles.index(newTile)
            return (True, True, tIndex)
        except ValueError:
            pass

        # Check for only vertically flipped tile
        newTile.reverse()
        try:
            tIndex = self._tiles.index(newTile)
            return (True, False, tIndex)
        except ValueError:
            pass

        # We need to add a new tile
        if self._usedTiles >= self._numTiles:
            # TODO ERROR: Not enough room for a new tile
            return (False, False, 0)
        # Remember, newTile is still vflipped
        self._tiles.append(newTile)
        self._usedTiles += 1
        return (True, False, len(self._tiles)-1)
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
    def sizeBlock(self):
        return 2 * self._numColors * self._numPalettes
    # Adjusts the palette so the the colors in a given portion of an image are
    # added to this palette such that all the colors in the tile can be
    # found in a single subpalette
    # Returns the subpalette number to use for this tile
    def addColorsFromTile(self, imgData, imgWidth, x, y, width, height):
        # Set of unique colors in this tile
        # List of colors in this tile
        colors = [imgData[j*imgWidth + i]
                            for i in range(x,x+width) for j in
                            range(y,y+height)]
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
    def __len__(self):
        return self._numPalettes
    def palSize(self):
        return self._numColors

class EbTownMap:
    def __init__(self, name, ptrLoc):
        self._name = name
        self._ptrLoc = ptrLoc
        self._block = EbCompressedData()
        self._gfx = EbTileGraphics(512, 8, 4)
        self._arr = EbArrangement(32, 28)
        self._pals = EbPalettes(2, 16)
    def readFromRom(self, rom):
        self._block.readFromRom(rom,
                EbModule.toRegAddr(
                    rom.readMulti(self._ptrLoc, 4)))

        self._arr.readFromBlock(self._block, 64)
        self._pals.readFromBlock(self._block, 0)
        self._gfx.readFromBlock(self._block, 2048+64)
    def writeToRom(self, rom):
        # Arrangement space is 2048 bytes long since it's 32x32x2 in VRAM
        self._block.clear(
                self._pals.sizeBlock() + 2048
#                + self._arr.sizeBlock()
                + self._gfx.sizeBlock())
        self._pals.writeToBlock(self._block, 0)
        self._arr.writeToBlock(self._block, 64)
        self._gfx.writeToBlock(self._block, 2048+64)

        newAddr = self._block.writeToFree(rom)
        rom.writeMulti(self._ptrLoc, EbModule.toSnesAddr(newAddr), 4)
    def writeToProject(self, resourceOpener):
        img = self._arr.toImage(self._gfx, self._pals)
        imgFile = resourceOpener(self.name(), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
    def readFromProject(self, resourceOpener):
        imgFile = resourceOpener(self.name(), 'png')
        imgFname = imgFile.name
        imgFile.close()
        self._arr.readFromImage(imgFname, self._pals, self._gfx)
    def name(self):
        return self._name

class EbLogo:
    def __init__(self, name, gfxPtrLoc, arrPtrLoc, palPtrLoc):
        self._name = name

        self._gfxBlock = EbCompressedData()
        self._arrBlock = EbCompressedData()
        self._palBlock = EbCompressedData()
        self._gfx = EbTileGraphics(256, 8)
        self._arr = EbArrangement(32, 28)
        self._pals = EbPalettes(5, 4)

        self._gfxPtrLoc = gfxPtrLoc
        self._arrPtrLoc = arrPtrLoc
        self._palPtrLoc = palPtrLoc
    def readFromRom(self, rom):
        self._gfxBlock.readFromRom(rom,
                EbModule.toRegAddr(
                    EbModule.readAsmPointer(rom, self._gfxPtrLoc)))
        self._arrBlock.readFromRom(rom,
                EbModule.toRegAddr(
                    EbModule.readAsmPointer(rom, self._arrPtrLoc)))
        self._palBlock.readFromRom(rom,
                EbModule.toRegAddr(
                    EbModule.readAsmPointer(rom, self._palPtrLoc)))

        self._gfx.readFromBlock(self._gfxBlock)
        self._arr.readFromBlock(self._arrBlock)
        self._pals.readFromBlock(self._palBlock)
    def writeToProject(self, resourceOpener):
        img = self._arr.toImage(self._gfx, self._pals)
        imgFile = resourceOpener(self.name(), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
    def writeToRom(self, rom):
        self._gfxBlock.clear(self._gfx.sizeBlock())
        self._arrBlock.clear(self._arr.sizeBlock())
        self._palBlock.clear(self._pals.sizeBlock())

        self._gfx.writeToBlock(self._gfxBlock)
        self._arr.writeToBlock(self._arrBlock)
        self._pals.writeToBlock(self._palBlock)

        newAddr = self._gfxBlock.writeToFree(rom)
        EbModule.writeAsmPointer(rom, self._gfxPtrLoc,
                EbModule.toSnesAddr(newAddr))
        newAddr = self._arrBlock.writeToFree(rom)
        EbModule.writeAsmPointer(rom, self._arrPtrLoc,
                EbModule.toSnesAddr(newAddr))
        newAddr = self._palBlock.writeToFree(rom)
        EbModule.writeAsmPointer(rom, self._palPtrLoc,
                EbModule.toSnesAddr(newAddr))
    def readFromProject(self, resourceOpener):
        imgFile = resourceOpener(self.name(), 'png')
        imgFname = imgFile.name
        imgFile.close()
        self._arr.readFromImage(imgFname, self._pals, self._gfx)
    def name(self):
        return self._name

class CompressedGraphicsModule(EbModule.EbModule):
    _name = "Compressed Graphics"
    TOWN_MAP_PTRS = zip(
            map(lambda x: "TownMaps/" + x,
                ["Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers"]),
            range(0x202190, 0x202190 + 0x18 * 4, 4))

    def __init__(self):
        self._logos = [
                EbLogo("Logos/Nintendo", 0xeea3, 0xeebb, 0xeed3),
                EbLogo("Logos/APE", 0xeefb, 0xef13, 0xef2b),
                EbLogo("Logos/HALKEN", 0xef52, 0xef6a, 0xef82)
                ]
        self._townmaps = map(lambda (x,y): EbTownMap(x, y), self.TOWN_MAP_PTRS)
    def free(self):
        del(self._logos)
        del(self._townmaps)
    def readFromRom(self, rom):
        for logo in self._logos:
            logo.readFromRom(rom)
        for map in self._townmaps:
            map.readFromRom(rom)
    def freeRanges(self):
        return [(0x2021a8, 0x20ed02)]
    def writeToRom(self, rom):
        for logo in self._logos:
            logo.writeToRom(rom)
        for map in self._townmaps:
            map.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        for logo in self._logos:
            logo.writeToProject(resourceOpener)
        for map in self._townmaps:
            map.writeToProject(resourceOpener)
    def readFromProject(self, resourceOpener):
        for logo in self._logos:
            logo.readFromProject(resourceOpener)
        for map in self._townmaps:
            map.readFromProject(resourceOpener)
