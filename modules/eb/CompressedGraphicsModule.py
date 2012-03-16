import EbModule
from EbDataBlocks import EbCompressedData

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
        self._arrBuf = None
    def readFromBlock(self, block, loc=0):
        self._arrBuf = map(
            lambda x: block[loc+x] | (block[loc+x+1] << 8),
            range(0, self._width*self._height*2, 2))
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
        self._arrBuf[y*height + x] = ((vf << 15) # Vertical Flip Flag
                | (hf << 14) # Horizontal Flip Flag
                | (pb << 13) # Priority Flag
                | ((pal & 0x7) << 10) # Palette
                | (tid & 0x3ff)) # Tile id
    def toImage(self, gfx, pals):
        img = Image.new("P",
                (self.width() * gfx.tileSize(),
                self.height() * gfx.tileSize()),
                None)
        # Have to convert the palette from [(r,g,b),(r,g,b)] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x,y: x.__add__(list(y)),
            reduce(lambda x,y: x.__add__(y),
                map(lambda x: pals[x],
                    range(0, len(pals))),
                []),
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

class EbTileGraphics:
    def __init__(self, numTiles, tileSize, bpp=2):
        self._numTiles = numTiles
        self._tileSize = tileSize
        self._tiles = None
        self._bpp = bpp
    def readFromBlock(self, block, loc=0):
        self._tiles = []
        off = loc
        for i in range(0, self._numTiles):
            tile = map(
                    lambda x: array.array('B', [0]*self._tileSize),
                    range(0, self._tileSize))
            try:
                if self._bpp == 2:
                    off += EbModule.read2BPPArea(tile, block, off, 0, 0)
                elif self._bpp == 4:
                    off += EbModule.read4BPPArea(tile, block, off, 0, 0)
            except IndexError:
                pass # Load an empty tile if it's out of range of the data
            self._tiles.append(tile)
    def tileSize(self):
        return self._tileSize
    def __getitem__(self, key):
        return self._tiles[key]

class EbPalettes:
    def __init__(self, numPalettes, numColors):
        self._numPalettes = numPalettes
        self._numColors = numColors
        self._pals = None
    def readFromBlock(self, block, loc=0):
        self._pals = map(
                lambda x: EbModule.readPalette(
                    block, loc+x, self._numColors),
                range(0, self._numPalettes*self._numColors*2,
                    self._numColors*2))
    def __getitem__(self, key):
        return self._pals[key]
    def __len__(self):
        return self._numPalettes
    def palSize(self):
        return self._numColors

class EbTownMap:
    def __init__(self, name, ptrLoc):
        self._name = name
        self._ptrLoc = ptrLoc
        self._block = EbCompressedData()
        self._gfx = EbTileGraphics(1024, 8, 4)
        self._arr = EbArrangement(32, 28)
        self._pals = EbPalettes(2, 16)
    def readFromRom(self, rom):
        self._block.readFromRom(rom,
                EbModule.toRegAddr(
                    rom.readMulti(self._ptrLoc, 4)))

        self._arr.readFromBlock(self._block, 64)
        self._pals.readFromBlock(self._block, 0)
        self._gfx.readFromBlock(self._block, 2048+64)
    def writeToProject(self, resourceOpener):
        img = self._arr.toImage(self._gfx, self._pals)
        imgFile = resourceOpener(self.name(), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
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
    def readFromRom(self, rom):
        for logo in self._logos:
            logo.readFromRom(rom)
        for map in self._townmaps:
            map.readFromRom(rom)
    def writeToProject(self, resourceOpener):
        for logo in self._logos:
            logo.writeToProject(resourceOpener)
        for map in self._townmaps:
            map.writeToProject(resourceOpener)
