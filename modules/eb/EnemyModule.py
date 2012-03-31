import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import DataBlock, EbCompressedData
from CompressedGraphicsModule import EbPalettes

import array
import copy
from PIL import Image

class EbSprite:
    def __init__(self):
        self._sprite = None
        self._width = None
        self._height = None
    def __eq__(self, other):
        return ((self._width == other._width)
                and (self._height == other._height)
                and (self._sprite == other._sprite))
    def sizeBlock(self):
        return (self._width/32)*(self._height/32)*4*4*32
    def readFromBlock(self, block, width, height, loc=0):
        self._width = width
        self._height = height
        self._sprite = map(lambda x: array.array('B', [0] * height),
                range(0, width))
        offset = loc
        for q in range(0, height/32):
            for r in range(0, width/32):
                for a in range(0, 4):
                    for j in range(0, 4):
                        EbModule.read4BPPArea(self._sprite, block, offset,
                                (j + r * 4) * 8, (a + q * 4) * 8)
                        offset += 32
    def writeToBlock(self, block, loc=0):
        offset = loc
        for q in range(0, self._height/32):
            for r in range(0, self._width/32):
                for a in range(0, 4):
                    for j in range(0,4):
                        EbModule.write4BPPArea(
                                self._sprite, block, offset,
                                (j + r * 4) * 8, (a + q * 4) * 8)
                        offset += 32
    def toImage(self, pal):
        img = Image.new("P", (self._width, self._height), None)
        # Have to convert the palette from [(r,g,b),(r,g,b)] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x,y: x.__add__(list(y)), pal, [])
        img.putpalette(rawPal)
        for x in range(0, self._width):
            for y in range(0, self._height):
                img.putpixel((x,y), self._sprite[x][y])
        return img
    def fromImage(self, image):
        self._width, self._height = image.size
        self._sprite = []
        for x in range(0, self._width):
            col = array.array('B', [0]*self._height)
            for y in range(0, self._height):
                col[y] = image.getpixel((x,y))
            self._sprite.append(col)
    def width(self):
        return self._width
    def height(self):
        return self._height
    def __getitem__(self, key):
        x, y = key
        return sprite[x][y]

class EbBattleSprite:
    SIZES = [ (0,0), (32,32), (64,32), (32,64), (64,64), (128,64), (128, 128) ]
    def __init__(self):
        self._sprite = EbSprite()
        self._size = 0
    def __eq__(self, other):
        return (self._size == other._size) and (self._sprite == other._sprite)
    def size(self):
        return self._size
    def sizeBlock(self):
        return self._sprite.sizeBlock()
    def readFromBlock(self, block, size):
        self._size = size
        w, h = self.SIZES[size]
        self._sprite.readFromBlock(block, w, h)
    def writeToBlock(self, block):
        block.clear(self._sprite.width() * self._sprite.height() / 2)
        self._sprite.writeToBlock(block)
    def writeToProject(self, resourceOpener, enemyNum, palette):
        img = self._sprite.toImage(palette)
        imgFile = resourceOpener(
                "BattleSprites/" + str(enemyNum).zfill(3), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
    def readFromProject(self, resourceOpener, enemyNum, pal):
        f = resourceOpener("BattleSprites/" + str(enemyNum).zfill(3), 'png')
        fname = f.name
        f.close()
        img = Image.open(fname)
        self._sprite.fromImage(img)
        self._size = self.SIZES.index(
                (self._sprite.width(),self._sprite.height()))
        palData = img.getpalette()
        del(img)
        for i in range(pal.palSize()):
            pal[0,i] = (palData[i*3], palData[i*3+1], palData[i*3+2])

class EnemyModule(EbModule.EbModule):
    _name = "Enemy"
    _ASMPTR_GFX = 0x2ee0b
    _REGPTR_GFX = [ 0x2ebe0, 0x2f014, 0x2f065 ]
    _ASMPTR_PAL = 0x2ef74
    def __init__(self):
        self._enemyCfgTable = EbTable(0xd59589)
        self._bsPtrTbl = EbTable(0xce62ee)
        self._bsPalsTable = EbTable(0xce6514)

        self._bsprites = [ ]
        self._bsPals = [ ]
    def free(self):
        del(self._enemyCfgTable)
        del(self._bsPalsTable)
        del(self._bsprites)
    def readFromRom(self, rom):
        self._enemyCfgTable.readFromRom(rom)
        self._bsPalsTable.readFromRom(rom,
                EbModule.toRegAddr(EbModule.readAsmPointer(rom,
                    self._ASMPTR_PAL)))
        self._bsPtrTbl.readFromRom(rom,
                EbModule.toRegAddr(EbModule.readAsmPointer(rom,
                    self._ASMPTR_GFX)))
        # Read the palettes
        for i in range(self._bsPalsTable.height()):
            pal = EbPalettes(1,16)
            pal.set(0, self._bsPalsTable[i,0].val())
            self._bsPals.append(pal)
        # Read the sprites
        for i in range(self._bsPtrTbl.height()):
            bsb = EbCompressedData()
            bsb.readFromRom(rom,
                    EbModule.toRegAddr(self._bsPtrTbl[i,0].val()))
            bs = EbBattleSprite()
            bs.readFromBlock(bsb, self._bsPtrTbl[i,1].val())
            self._bsprites.append(bs)
            del(bsb)
    def freeRanges(self):
        return [(0x0d0000, 0x0dffff), (0x0e0000, 0x0e6913)]
    def writeToRom(self, rom):
        # Write the main table
        self._enemyCfgTable.writeToRom(rom)
        # Write the gfx ptr table
        self._bsPtrTbl.clear(len(self._bsprites))
        i = 0
        for bs in self._bsprites:
            bsb = EbCompressedData()
            bsb.clear(bs.sizeBlock())
            bs.writeToBlock(bsb)
            self._bsPtrTbl[i,0].setVal(EbModule.toSnesAddr(
                bsb.writeToFree(rom)))
            self._bsPtrTbl[i,1].setVal(bs.size())
            i += 1
        gfxAddr = EbModule.toSnesAddr(self._bsPtrTbl.writeToFree(rom))
        EbModule.writeAsmPointer(rom, self._ASMPTR_GFX, gfxAddr)
        for p in self._REGPTR_GFX:
            rom.writeMulti(p, gfxAddr, 3)
        # Write the pal table
        self._bsPalsTable.clear(len(self._bsPals))
        i = 0
        for p in self._bsPals:
            self._bsPalsTable[i,0].setVal(p.getSubpal(0))
            i += 1
        EbModule.writeAsmPointer(rom, self._ASMPTR_PAL,
                EbModule.toSnesAddr(self._bsPalsTable.writeToFree(rom)))
    def writeToProject(self, resourceOpener):
        # First, write the Enemy Configuration Table
        self._enemyCfgTable.writeToProject(resourceOpener, [4,14])

        # Next, write the battle sprite images
        for i in range(self._enemyCfgTable.height()):
            if self._enemyCfgTable[i,4].val() > 0:
                self._bsprites[self._enemyCfgTable[i,4].val()-1].writeToProject(
                        resourceOpener, i,
                        self._bsPals[self._enemyCfgTable[i,14].val()].getSubpal(0))
    def readFromProject(self, resourceOpener):
        # TODO
        # First, read the Enemy Configuration Table
        self._enemyCfgTable.readFromProject(resourceOpener)

        # Second, read the Battle Sprites TODO
        for i in range(self._enemyCfgTable.height()):
            bs = EbBattleSprite()
            pal = EbPalettes(1,16)
            try:
                bs.readFromProject(resourceOpener, i, pal)
                # Add the battle sprite
                try:
                    self._enemyCfgTable[i,4].set(self._bsprites.index(bs))
                except ValueError:
                    self._bsprites.append(bs)
                    self._enemyCfgTable[i,4].set(len(self._bsprites))
                # Add the palette
                try:
                    self._enemyCfgTable[i,14].set(self._bsPals.index(pal))
                except ValueError:
                    self._bsPals.append(pal)
                    self._enemyCfgTable[i,14].set(len(self._bsPals)-1)
            except IOError:
                # No battle sprite PNG
                self._enemyCfgTable[i,4].set(0)
                self._enemyCfgTable[i,14].set(0)
