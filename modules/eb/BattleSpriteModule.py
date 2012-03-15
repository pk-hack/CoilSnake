import EbModule
from modules.Table import TableEntry, _return
from EbTablesModule import EbTable

import array
import copy
from PIL import Image

def readSpriteFromBuffer(buffer, w, h):
    sprite = map(lambda x: array.array('B', [0]*h), range(0,w))
    offset = 0
    for q in range(0, h/32):
        for r in range(0, w/32):
            for a in range(0, 4):
                for j in range(0, 4):
                    EbModule.read4BPPArea(sprite, buffer, offset,
                            (j + r * 4) * 8, (a + q * 4) * 8)
                    offset += 32
    return sprite

def getBytesFromSprite(sprite, w, h):
    buffer = array.array('B', [0] * (w * h / 2))
    offset = 0
    for q in range(0, h/32):
        for r in range(0, w/32):
            for a in range(0, 4):
                for j in range(0,4):
                    EbModule.write4BPPArea(
                            sprite, buffer, offset,
                            (j + r * 4) * 8, (a + q * 4) * 8)
                    offset += 32
    return buffer

def readSpriteFromImage(image):
    imgW, imgH = image.size

    sprite = []
    for x in range(0,imgW):
        col = array.array('B', [0]*imgH)
        for y in range(0,imgH):
            col[y] = image.getpixel((x,y))
        sprite.append(col)

    return sprite

def makeImageFromSprite(sprite, pal):
    w, h = len(sprite), len(sprite[0])
    img = Image.new("P", (w, h), None)
    img.putpalette(pal)
    for x in range(0, w):
        for y in range(0, h):
            img.putpixel((x,y), sprite[x][y])

    return img

defaultPal = [
        64, 64, 56,
        240, 240, 240,
        208, 208, 208,
        144, 160, 128,
        160, 136, 240,
        0, 144, 112,
        80, 112, 96,
        240, 176, 144,
        208, 160, 128,
        240, 144, 144,
        240, 0, 96,
        144, 0, 48,
        56, 80, 80,
        88, 88, 88,
        24, 0, 24,
        48, 32, 32 ]

class BattleSpriteModule(EbModule.EbModule):
    _name = "Battle Sprite"
    _battleSpriteSizes = [ (0,0), (32,32), (64,32), (32,64), (64,64), (128,64),
            (128, 128) ]
    def __init__(self):
        self._table = EbTable(0xce62ee)
    def readFromRom(self, rom):
        self._table.readFromRom(rom)
    def writeToRom(self, rom):
        self._table.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        # Write the table, with the data block pointers replaced with filenames
        tmpTable = copy.deepcopy(self._table)
        fakeEntryGen = lambda a,b: TableEntry(
                a, None, None, None, None,
                lambda x: "BattleSprites/" + str(b).zfill(3))
        for i in range(0,tmpTable.height()):
            # Replace the compressed pointer table entry with a filename entry
            tmpTable[i,0] = fakeEntryGen(tmpTable[i,0].name, i)
            # Write the PNG file
            spriteW, spriteH = self._battleSpriteSizes[self._table[i,1].intval()]
            sprite = readSpriteFromBuffer(
                    self._table[i,0].getBlock().rawData(), spriteW, spriteH)
            img = makeImageFromSprite(sprite, defaultPal)
            imgFile = resourceOpener(tmpTable[i,0].dump(), 'png')
            img.save(imgFile, "png")
            imgFile.close()
        f = resourceOpener(tmpTable.name(), 'yml')
        f.write(tmpTable.dump())
        f.close()
    def readFromProject(self, resourceOpener):
        # Read the EbTable structure from the yml file
        f = resourceOpener(self._table.name(), 'yml')
        contents = f.read()
        f.close()

        # Read the data into another EbTable, with the filename
        tmpTable = copy.deepcopy(self._table)
        def fakeEntryGen(a,b):
            return TableEntry(a["name"],None,None,None,_return,_return)
        tmpTable.tableEntryGenerator = fakeEntryGen
        tmpTable.load(contents)

        # Load data into the real table
        self._table.load(contents)
        for i in range(0, self._table.height()):
            # Read the image from the given filename in tmpTable
            img = Image.open(resourceOpener(tmpTable[i,0].dump(), 'png'))
            # Convert image to a sprite
            spriteW, spriteH = img.size
            sprite = readSpriteFromImage(img)
            # Convert sprite to 4BPP Area
            data = getBytesFromSprite(sprite, spriteW, spriteH)

            self._table[i,0].getBlock().set(data.tostring())
            self._table[i,1].set(tmpTable[i,1].dump())
