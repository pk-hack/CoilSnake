import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import EbCompressedData

import array
import copy
from PIL import Image

class EbSprite:
    def __init__(self):
        self._sprite = None
        self._width = None
        self._height = None
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
    def __init__(self, num, ptrLoc):
        self._num = num
        self._ptrLoc = ptrLoc
        self._gfxBlock = EbCompressedData()
        self._sprite = EbSprite()
    def id(self):
        return self._num
    def name(self):
        return "BattleSprites/" + str(self._num).zfill(3)
    def readFromRom(self, rom):
        self._gfxBlock.readFromRom(rom,
                EbModule.toRegAddr(rom.readMulti(self._ptrLoc, 4)))
        w, h = self.SIZES[rom[self._ptrLoc + 4]]
        self._sprite.readFromBlock(self._gfxBlock, w, h)
    def writeToRom(self, rom):
        self._gfxBlock.clear(
                self._sprite.width() * self._sprite.height() / 2)
        self._sprite.writeToBlock(self._gfxBlock)
        addr = self._gfxBlock.writeToFree(rom)
        rom.writeMulti(self._ptrLoc, EbModule.toSnesAddr(addr), 4)
        rom[self._ptrLoc + 4] = self.SIZES.index(
                (self._sprite.width(), self._sprite.height()))
    def writeToProject(self, resourceOpener, palette):
        img = self._sprite.toImage(palette)
        imgFile = resourceOpener(self.name(), 'png')
        img.save(imgFile, 'png')
        imgFile.close()
    def readFromProject(self, resourceOpener):
        self._sprite.fromImage(
                Image.open(resourceOpener(self.name(), 'png')))

class EnemyModule(EbModule.EbModule):
    _name = "Enemy"
    NUM_BATTLE_SPRITES = 110
    BATTLE_SPRITE_PTRS = zip(
            range(0, NUM_BATTLE_SPRITES),
            range(0x0E62EE, 0x0E62EE + NUM_BATTLE_SPRITES * 5, 5))
    def __init__(self):
        self._enemyCfgTable = EbTable(0xd59589)
        self._bsPalsTable = EbTable(0xce6514)

        self._bsprites = map(lambda (x,y): EbBattleSprite(x,y),
                self.BATTLE_SPRITE_PTRS)
    def readFromRom(self, rom):
        self._enemyCfgTable.readFromRom(rom)
        self._bsPalsTable.readFromRom(rom)
        for bs in self._bsprites:
            bs.readFromRom(rom)
    def writeToRom(self, rom):
        self._enemyCfgTable.writeToRom(rom)
        self._bsPalsTable.writeToRom(rom)
        for bs in self._bsprites:
            bs.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        # First, write the Enemy Configuration Table
        f = resourceOpener(self._enemyCfgTable.name(), 'yml')
        f.write(self._enemyCfgTable.dump())
        f.close()

        # Second, write the Battle Sprite Palettes Table
        f = resourceOpener(self._bsPalsTable.name(), 'yml')
        f.write(self._bsPalsTable.dump())
        f.close()

        # Third, write the Battle Sprites
        for bs in self._bsprites:
            # Find the first palette number used by this battle sprite
            palNum = 0 # Default to palette #0
            for j in range(0,self._enemyCfgTable.height()):
                if self._enemyCfgTable[j,4].dump() == bs.id():
                    palNum = self._enemyCfgTable[j,14].dump()
                    break
            bs.writeToProject(resourceOpener,
                    self._bsPalsTable[palNum,0].val())
    def readFromProject(self, resourceOpener):
        # First, read the Enemy Configuration Table
        f = resourceOpener(self._enemyCfgTable.name(), 'yml')
        contents = f.read()
        f.close()
        self._enemyCfgTable.load(contents)

        # Second, read the Battle Sprites Palettes Table
        f = resourceOpener(self._bsPalsTable.name(), 'yml')
        contents = f.read()
        f.close()
        self._bsPalsTable.load(contents)

        # Third, read the Battle Sprites
        for bs in self._bsprites:
            bs.readFromProject(resourceOpener)
