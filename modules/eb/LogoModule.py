import EbModule

import array
from PIL import Image

class EbCompressedData:
    def __init__(self):
        self._data = None
    def readFromRom(self, rom, addr):
        ucdata = EbModule.decomp(rom, addr)
        if ucdata[0] < 0:
            print "Error decompressing data @", hex(addr)
        else:
            self._data = array.array('B', ucdata)
#    def writeToProject(self, resourceOpener):
#        f = resourceOpener("tile_gfx", "smc")
#        self._data.tofile(f)
#        f.close()
    def writeToFree(self, rom):
        cdata = EbModule.comp(self._data.tolist())
        rom.writeToFree(cdata)
    def __getitem__(self, key):
        if type(key) == slice:
            return self._data[key].tolist()
        else:
            return self._data[key]
    def __setitem__(self, key, val):
        self[key] = val
    def __len__(self):
        return len(self._data)
    def tolist(self):
        return self._data.tolist()

#<Penguin> found it. VHOPPPCC CCCCCCCC
#<Penguin> v for vertical flip, h for horizontal flip, o for priority bit, p for
#          palette number, c for tile id
class EbArrangement:
    # Width/Height is in tiles
    def __init__(self, DataBlockClass, width, height):
        self._data = DataBlockClass()
        self._width = width
        self._height = height
        self._arrBuf = None
    def readFromRom(self, rom, addr):
        self._data.readFromRom(rom, addr)
        self._arrBuf = map(
            lambda x: self._data[x] | (self._data[x+1] << 8),
            range(0, len(self._data), 2))
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

class EbTileGraphics:
    def __init__(self, DataBlockClass, numTiles, tileSize):
        self._data = DataBlockClass()
        self._numTiles = numTiles
        self._tileSize = tileSize
        self._tiles = None
    def readFromRom(self, rom, addr):
        self._data.readFromRom(rom, addr)
        # Read all the tiles into a dict
        self._tiles = []
        off = 0
        for i in range(0, self._numTiles):
            tile = map(
                    lambda x: array.array('B', [0]*self._tileSize),
                    range(0, self._tileSize))
            try:
                off += EbModule.read2BPPArea(tile, self._data, off, 0, 0)
            except IndexError:
                pass # Load an empty tile if it's out of range of the data
            self._tiles.append(tile)
    def tileSize(self):
        return self._tileSize
    def __getitem__(self, key):
        return self._tiles[key]

class EbPalettes:
    def __init__(self, DataBlockClass, numPalettes, numColors):
        self._data = DataBlockClass()
        self._numPalettes = numPalettes
        self._numColors = numColors
        self._pals = None
    def readFromRom(self, rom, addr):
        self._data.readFromRom(rom, addr)
        self._pals = map(
                lambda x: EbModule.readPalette(
                    self._data, x, self._numColors),
                range(0, self._numPalettes*self._numColors*2,
                    self._numColors*2))
    def __getitem__(self, key):
        return self._pals[key]
    def __len__(self):
        return self._numPalettes

class EbLogo:
    def __init__(self, name, gfxPtrLoc, arrPtrLoc, palPtrLoc):
        self._name = name
        self._gfx = EbTileGraphics(EbCompressedData, 256, 8)
        self._arr = EbArrangement(EbCompressedData, 32, 28)
        self._pals = EbPalettes(EbCompressedData, 5, 4)

        self._gfxPtrLoc = gfxPtrLoc
        self._arrPtrLoc = arrPtrLoc
        self._palPtrLoc = palPtrLoc
    def readFromRom(self, rom):
        self._gfx.readFromRom(rom,
                EbModule.toRegAddr(
                    EbModule.readAsmPointer(rom, self._gfxPtrLoc)))
        self._arr.readFromRom(rom,
                EbModule.toRegAddr(
                    EbModule.readAsmPointer(rom, self._arrPtrLoc)))
        self._pals.readFromRom(rom,
                EbModule.toRegAddr(
                    EbModule.readAsmPointer(rom, self._palPtrLoc)))

    def writeToProject(self, resourceOpener):
        img = Image.new("P",
                (self._arr.width() * self._gfx.tileSize(),
                    self._arr.height() * self._gfx.tileSize()),
                None)
        # Have to convert the palette from [(r,g,b),(r,g,b)] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x,y: x.__add__(list(y)),
                reduce(lambda x,y: x.__add__(y),
                    map(lambda x: self._pals[x],
                        range(0, len(self._pals))),
                    []),
                [])
        img.putpalette(rawPal)
        for y in range(0,self._arr.height()):
            for x in range(0,self._arr.width()):
                vf, hf, pb, pal, tid = self._arr[x,y]
                tile = self._gfx[tid]
                for ty in range(0,self._gfx.tileSize()):
                    for tx in range(0,self._gfx.tileSize()):
                        px , py = tx, ty
                        if vf:
                            py = self._gfx.tileSize() - py - 1
                        if hf:
                            px = self._gfx.tileSize() - px - 1
                        img.putpixel(
                                (x*self._gfx.tileSize() +tx,
                                    y*self._gfx.tileSize()+ty),
                                tile[px][py]+pal*4)
        imgFile = resourceOpener(self.name(), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
    def name(self):
        return self._name


class LogoModule(EbModule.EbModule):
    _name = "Logos"
    def __init__(self):
        self._logos = [
                EbLogo("Logos/Nintendo", 0xeea3, 0xeebb, 0xeed3),
                EbLogo("Logos/APE", 0xeefb, 0xef13, 0xef2b),
                EbLogo("Logos/HALKEN", 0xef52, 0xef6a, 0xef82)
                ]
    def readFromRom(self, rom):
        for logo in self._logos:
            logo.readFromRom(rom)
    def writeToProject(self, resourceOpener):
        for logo in self._logos:
            logo.writeToProject(resourceOpener)
