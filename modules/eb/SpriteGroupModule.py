import EbModule
from EbTablesModule import EbTable

import array
import yaml
from PIL import Image

class EbRegSprite:
    def __init__(self):
        self._w = self._h = 0
        self._data = None
    def readFromBlock(self, block, width, height, loc=0):
        self._w = width
        self._h = height
        self._data = map(lambda x: array.array('B', [0] * self._h),
                range(self._w))
        for i in range(self._h / 8):
            for j in range(self._w / 8):
                EbModule.read4BPPArea(self._data, block, loc,
                        j*8, i*8)
                loc += 32
    def drawToImage(self, img, x, y, hflip):
        for dx in range(self._w):
            for dy in range(self._h):
                if hflip:
                    img.putpixel((x+dx,y+dy), self._data[self._w-1-dx][dy])
                else:
                    img.putpixel((x+dx,y+dy), self._data[dx][dy])
    def width(self):
        return self._w
    def height(self):
        return self._h

class SpriteGroup:
    def __init__(self, numSprites):
        self._w = self._h = self._pal = 0
        self._unknownA = 0
        self._unknownB = [0,0,0,0]
        self._numSprites = numSprites
        # [Sprite,Flip,NoSink]
        self._sprites = [[EbRegSprite(),False,False] for i in range(numSprites)]
    def palette(self):
        return self._pal
    def readFromRom(self, rom, loc):
        self._h = rom[loc]
        self._w = rom[loc+1] >> 4
        self._unknownA = rom[loc+2]
        self._pal = (rom[loc+3] >> 1) & 0x7
        self._unknownB = rom[loc+4:loc+8]

        bank = rom[loc+8] << 16
        i = loc+9
        for spff in self._sprites:
            ptr = bank | rom.readMulti(i, 2)
            spff[1] = (ptr & 1) != 0
            spff[2] = (ptr & 2) != 0 
            spff[0].readFromBlock(rom, self._w*8, self._h*8,
                    EbModule.toRegAddr(ptr&0xfffffc))
            i += 2
    def toImage(self, pal):
        # Image will be a 4x4 grid of sprites
        img = Image.new("P", (self._w*8*4, self._h*8*4), 0)
        # Have to convert the palette from [(r,g,b),(r,g,b)] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x,y: x.__add__(list(y)), pal, [])
        img.putpalette(rawPal)

        # Draw the sprites
        x = y = 0
        for spff in self._sprites:
            spff[0].drawToImage(
                    img, x*spff[0].width(), y*spff[0].height(),
                    spff[1])
            x += 1
            if x >= 4:
                y += 1
                x = 0
        return img
    def dump(self):
        return { 'Unknown A': self._unknownA,
                'Unknown B': self._unknownB,
                'Swim Flags': map(lambda (a,b,x): x, self._sprites)
                }

class SpriteGroupModule(EbModule.EbModule):
    _name = "Sprite Groups"
    def __init__(self):
        self._grPtrTbl = EbTable(0xef133f)
        self._grPalTbl = EbTable(0xc30000)
        self._groups = None
    def freeRanges(self):
        return [(0x2f1a7f, 0x2f4a3f),
                (0x110000, 0x11ffff),
                (0x120000, 0x12ffff),
                (0x130000, 0x13ffff),
                (0x140000, 0x14ffff),
                (0x150000, 0x154fff)]
    def free(self):
        del(self._grPtrTbl)
        del(self._grPalTbl)
    def readFromRom(self, rom):
        self._grPtrTbl.readFromRom(rom)
        self._grPalTbl.readFromRom(rom)

        # Load the sprite groups
        self._groups = []
        for i in range(self._grPtrTbl.height()):
            # Note: this assumes that the SPT is written contiguously
            numSprites = 8
            # Assume that the last group only has 8 sprites
            if i < self._grPtrTbl.height()-1:
                numSprites = (self._grPtrTbl[i+1,0].val() -
                        self._grPtrTbl[i,0].val() - 9) / 2

            g = SpriteGroup(numSprites)
            g.readFromRom(rom, EbModule.toRegAddr(self._grPtrTbl[i,0].val()))
            self._groups.append(g)
    def writeToProject(self, resourceOpener):
        out = { }
        i = 0
        for g in self._groups:
            out[i] = g.dump()
            img = g.toImage(self._grPalTbl[g.palette(),0].val())
            imgFile = resourceOpener("SpriteGroups/" + str(i).zfill(3), 'png')
            img.save(imgFile, 'png', transparency=0)
            imgFile.close()
            del(img)
            i += 1
        yaml.dump(out, resourceOpener("sprite_groups", ".yml"))
