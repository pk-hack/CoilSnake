import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import DataBlock

import array
import copy
import yaml
from PIL import Image

class EbRegSprite:
    def __init__(self):
        self._w = self._h = 0
        self._data = None
    def __eq__(self, other):
        return ((self._w == other._w)
                and (self._h == other._h)
                and (self._data == other._data))
    def readFromBlock(self, block, width, height, loc=0):
        self._w = width
        self._h = height
        self._data = map(lambda x: array.array('B', [0] * self._h),
                range(self._w))
        for i in range(self._h / 8):
            for j in range(self._w / 8):
                EbModule.read4BPPArea(self._data, block, loc, j*8, i*8)
                loc += 32
    def writeToBlock(self, block, loc=0):
        for i in range(self._h / 8):
            for j in range(self._w / 8):
                EbModule.write4BPPArea(self._data, block, loc, j*8, i*8)
                loc += 32
    def drawToImage(self, img, x, y):
        imgData = img.load()
        for dx in range(self._w):
            for dy in range(self._h):
                imgData[x+dx,y+dy] = self._data[dx][dy]
    def readFromImage(self, img, x, y, w, h):
        self._w = w
        self._h = h
        self._data = map(lambda x: array.array('B', [0] * self._h),
                range(self._w))
        imgData = img.load()
        for dx in range(self._w):
            for dy in range(self._h):
                self._data[dx][dy] = imgData[x+dx, y+dy]
    def hflip(self):
        self._data.reverse()
    def width(self):
        return self._w
    def height(self):
        return self._h
    def blockSize(self):
        return self._w / 8 * self._h / 8 * 32

class SpriteGroup:
    def __init__(self, numSprites):
        self._w = self._h = self._pal = 0
        self._unknownA = 0
        self._unknownB = [0,0,0,0]
        self._numSprites = max(0,numSprites)

        # For writing to ROM
        self._bank = 0
        self._spritePtrs = None
    def blockSize(self):
        return 9 + self._numSprites*2
    def palette(self):
        return self._pal
    def setPalette(self, palNum):
        self._pal = palNum
    def readFromRom(self, rom, loc):
        self._sprites = [
                [EbRegSprite(),False] for i in range(self._numSprites)]
        self._h = rom[loc]
        self._w = rom[loc+1] >> 4
        self._unknownA = rom[loc+2]
        self._pal = (rom[loc+3] >> 1) & 0x7
        self._unknownB = rom[loc+4:loc+8]

        bank = rom[loc+8] << 16
        i = loc+9
        for spff in self._sprites:
            ptr = bank | rom.readMulti(i, 2)
            spff[1] = (ptr & 2) != 0
            spff[0].readFromBlock(rom, self._w*8, self._h*8,
                    EbModule.toRegAddr(ptr&0xfffffc))
            if (ptr & 1) != 0:
                spff[0].hflip()
            i += 2
    def writeToBlock(self, block, loc=0):
        block[loc] = self._h
        block[loc+1] = self._w << 4
        block[loc+2] = self._unknownA
        block[loc+3] = self._pal << 1
        block[loc+4:loc+8] = self._unknownB
        block[loc+8] = self._bank
        for i in range(len(self._spritePtrs)):
            block[loc+9+2*i] = self._spritePtrs[i] & 0xff
            block[loc+9+2*i+1] = self._spritePtrs[i] >> 8
    def writeSpritesToFree(self, rom):
        if self._numSprites == 0:
            self._spritePtrs = []
            return
        spritePtrs = [ ]
        # Make a set of unique sprites
        uniqueSprites = [ ]
        for spf in self._sprites:
            sp = spf[0]
            try:
                spritePtrs.append((uniqueSprites.index(sp), False))
            except ValueError:
                # Regular sprite not in uniques
                sp.hflip()
                try:
                    spritePtrs.append((uniqueSprites.index(sp), True))
                except ValueError:
                    # Flipped sprite not in uniques
                    uniqueSprites.append(sp)
                    spritePtrs.append((uniqueSprites.index(sp), True))
        # Find a free block
        loc = rom.getFreeLoc(sum(map(lambda x: x.blockSize(), uniqueSprites)),15)
        self._bank = EbModule.toSnesAddr(loc) >> 16
        locStart = loc & 0xffff
        # Write each sprite
        uniqueSpriteAddrs = [ ]
        spBlockSize = uniqueSprites[0].blockSize()
        for uS in uniqueSprites:
            uS.writeToBlock(rom, loc)
            loc += spBlockSize
        # Output a list of pointers
        self._spritePtrs = map(lambda (n,f): (locStart + n*spBlockSize) | f, spritePtrs)
        for i in range(len(spritePtrs)):
            self._spritePtrs[i] |= (self._sprites[i][1]<<1)
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
                    img, x*spff[0].width(), y*spff[0].height())
            x += 1
            if x >= 4:
                y += 1
                x = 0
        return img
    def fromImage(self, img):
        x = y = 0
        imgW, imgH = img.size
        spW, spH = imgW/4, imgH/4
        self._w, self._h = spW/8, spH/8
        for spff in self._sprites:
            spff[0].readFromImage(img, x*spW, y*spH, spW, spH)
            x += 1
            if x >= 4:
                y += 1
                x = 0
    def dump(self):
        return { 'Unknown A': self._unknownA,
                'Unknown B': self._unknownB,
                'Swim Flags': map(lambda (a,x): x, self._sprites),
                'Length': self._numSprites
                }
    def load(self, d):
        self._numSprites = d['Length']
        self._sprites = [
                [EbRegSprite(),False] for i in range(self._numSprites)]
        self._unknownA = d['Unknown A']
        self._unknownB = d['Unknown B']
        sf = d['Swim Flags']
        i = 0
        try:
            for spff in self._sprites:
                spff[1] = sf[i]
                i += 1
        except IndexError:
            pass

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
        yaml.dump(out, resourceOpener("sprite_groups", "yml"))
    def readFromProject(self, resourceOpener):
        input = yaml.load(resourceOpener("sprite_groups", "yml"))
        numGroups = len(input)
        self._groups = []
        pals = []
        for i in range(numGroups):
            g = SpriteGroup(16)
            g.load(input[i])
            img = Image.open(
                    resourceOpener("SpriteGroups/" + str(i).zfill(3), "png"))
            g.fromImage(img)
            palData = img.getpalette()
            del(img)
            self._groups.append(g)

            # Read the palette from the image
            pal = [(0,0,0)]
            for i in range(1, 16):
                pal.append((palData[i*3], palData[i*3+1], palData[i*3+2]))
            # Assign the palette number to the sprite
            try:
                # Use a pre-existing palette number
                g.setPalette(pals.index(pal))
            except ValueError:
                # Uses a unique palette
                if len(pals) >= 8:
                    # Too many palettes! Just fall back to palette 0
                    g.setPalette(0)
                else:
                    pals.append(pal)
                    g.setPalette(len(pals)-1)

        self._grPalTbl.clear(8)
        # Save the palettes to the table
        for i in range(len(pals)):
            self._grPalTbl[i,0].setVal(pals[i])
        # Fill the rest of the table in case we didn't use all the palettes
        for i in range(len(pals),self._grPalTbl.height()):
            self._grPalTbl[i,0].setVal([(0,0,0)] * 16)
            
    def writeToRom(self, rom):
        numGroups = len(self._groups)
        self._grPtrTbl.clear(numGroups)
        block = DataBlock(sum(map(lambda x: x.blockSize(), self._groups)))
        block.clear()
        loc = 0
        i = 0
        # Write all the groups to the block, and sprites to rom
        for g in self._groups:
            g.writeSpritesToFree(rom)
            g.writeToBlock(block, loc)
            self._grPtrTbl[i,0].setVal(loc)
            loc += g.blockSize()
            i += 1
        # Write the block to rom and correct the group pointers
        addr = EbModule.toSnesAddr(block.writeToFree(rom))
        for i in range(self._grPtrTbl.height()):
            self._grPtrTbl[i,0].setVal(
                    self._grPtrTbl[i,0].val() + addr)
        # Write the pointer table
        self._grPtrTbl.writeToRom(rom)
        # Write the palettes
        self._grPalTbl.writeToRom(rom)
