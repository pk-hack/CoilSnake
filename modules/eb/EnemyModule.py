from modules.GenericModule import replaceField
import EbModule
from EbTablesModule import EbTable
from EbDataBlocks import EbCompressedData
from CompressedGraphicsModule import EbPalettes
from modules.Progress import updateProgress

from array import array
from PIL import Image
import yaml
from functools import reduce


class EbSprite:

    def __init__(self):
        self._sprite = None
        self._spriteHash = None
        self._width = None
        self._height = None

    def __eq__(self, other):
        return ((self._width == other._width)
                and (self._height == other._height)
                and (self._spriteHash == other._spriteHash))

    def sizeBlock(self):
        return (self._width / 32) * (self._height / 32) * 4 * 4 * 32

    def readFromBlock(self, block, width, height, loc=0):
        self._width = width
        self._height = height
        self._sprite = map(lambda x: array('B', [0] * height),
                           range(0, width))
        offset = loc
        for q in range(0, height / 32):
            for r in range(0, width / 32):
                for a in range(0, 4):
                    for j in range(0, 4):
                        EbModule.read4BPPArea(self._sprite, block, offset,
                                              (j + r * 4) * 8, (a + q * 4) * 8)
                        offset += 32
        self._spriteHash = EbModule.hashArea(self._sprite)

    def writeToBlock(self, block, loc=0):
        offset = loc
        for q in range(0, self._height / 32):
            for r in range(0, self._width / 32):
                for a in range(0, 4):
                    for j in range(0, 4):
                        EbModule.write4BPPArea(
                            self._sprite, block, offset,
                            (j + r * 4) * 8, (a + q * 4) * 8)
                        offset += 32

    def toImage(self, pal):
        img = Image.new("P", (self._width, self._height), None)
        # Have to convert the palette from [(r,g,b),(r,g,b)] to [r,g,b,r,g,b]
        rawPal = reduce(lambda x, y: x.__add__(list(y)), pal, [])
        img.putpalette(rawPal)
        imgData = img.load()
        for x in range(0, self._width):
            for y in range(0, self._height):
                imgData[x, y] = self._sprite[x][y]
        return img

    def fromImage(self, img):
        self._width, self._height = img.size
        self._sprite = []
        imgData = img.load()
        for x in range(0, self._width):
            col = array('B', [0] * self._height)
            for y in range(0, self._height):
                col[y] = imgData[x, y]
            self._sprite.append(col)
        self._spriteHash = EbModule.hashArea(self._sprite)

    def width(self):
        return self._width

    def height(self):
        return self._height

    def __getitem__(self, key):
        x, y = key
        return self._sprite[x][y]


class EbBattleSprite:
    SIZES = [(0, 0), (32, 32), (64, 32), (32, 64),
             (64, 64), (128, 64), (128, 128)]

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
        self._sprite.writeToBlock(block)

    def writeToProject(self, resourceOpener, enemyNum, palette):
        img = self._sprite.toImage(palette)
        imgFile = resourceOpener(
            "BattleSprites/" + str(enemyNum).zfill(3), 'png')
        img.save(imgFile, 'png', transparency=0)
        imgFile.close()

    def readFromProject(self, resourceOpener, enemyNum, pal):
        f = resourceOpener("BattleSprites/" + str(enemyNum).zfill(3), 'png')
        fname = f.name
        f.close()
        img = Image.open(fname)
        if img.mode != 'P':
            raise RuntimeError(
                "BattleSprites/" + str(enemyNum).zfill(3) + " is not an indexed PNG.")
        self._sprite.fromImage(img)
        self._size = self.SIZES.index(
            (self._sprite.width(), self._sprite.height()))
        palData = img.getpalette()
        del img
        for i in range(pal.palSize()):
            pal[0,
                i] = (
                palData[i * 3],
                palData[i * 3 + 1],
                palData[i * 3 + 2])


class EnemyModule(EbModule.EbModule):
    _name = "Enemies"
    _ASMPTR_GFX = 0x2ee0b
    _REGPTR_GFX = [0x2ebe0, 0x2f014, 0x2f065]
    _ASMPTR_PAL = 0x2ef74

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._enemyCfgTable = EbTable(0xd59589)
        self._bsPtrTbl = EbTable(0xce62ee)
        self._bsPalsTable = EbTable(0xce6514)
        self._enemyGroupTbl = EbTable(0xD0C60D)
        self._enemyGroupBgTbl = EbTable(0xCBD89A)
        self._bsprites = []
        self._bsPals = []
        self._enemyGroups = []

    def readFromRom(self, rom):
        self._bsPtrTbl.readFromRom(rom,
                                   EbModule.toRegAddr(
                                       EbModule.readAsmPointer(rom,
                                                               self._ASMPTR_GFX)))
        self._bsPalsTable.readFromRom(rom,
                                      EbModule.toRegAddr(
                                          EbModule.readAsmPointer(rom,
                                                                  self._ASMPTR_PAL)))
        pct = 45.0 / (self._bsPtrTbl.height()
                      + self._bsPalsTable.height() + 1)
        self._enemyCfgTable.readFromRom(rom)
        updateProgress(pct)
        # Read the palettes
        for i in range(self._bsPalsTable.height()):
            pal = EbPalettes(1, 16)
            pal.set(0, self._bsPalsTable[i, 0].val())
            self._bsPals.append(pal)
            updateProgress(pct)
        # Read the sprites
        for i in range(self._bsPtrTbl.height()):
            with EbCompressedData() as bsb:
                bsb.readFromRom(rom,
                                EbModule.toRegAddr(self._bsPtrTbl[i, 0].val()))
                bs = EbBattleSprite()
                bs.readFromBlock(bsb, self._bsPtrTbl[i, 1].val())
                self._bsprites.append(bs)
            updateProgress(pct)

        # Read the group data
        self._enemyGroupTbl.readFromRom(rom)
        self._enemyGroupBgTbl.readFromRom(rom)
        self._enemyGroups = []
        pct = 5.0 / self._enemyGroupTbl.height()
        for i in range(self._enemyGroupTbl.height()):
            group = []
            ptr = EbModule.toRegAddr(self._enemyGroupTbl[i, 0].val())
            while rom[ptr] != 0xff:
                group.append((rom.readMulti(ptr + 1, 2), rom[ptr]))
                ptr += 3
            self._enemyGroups.append(group)
            updateProgress(pct)

    def freeRanges(self):
        return [(0x0d0000, 0x0dffff),  # Battle Sprites
                (0x0e0000, 0x0e6913),  # Battle Sprites Cont'd & Btl Spr. Pals
                (0x10d52d, 0x10dfb3)]  # Enemy Group Data

    def writeToRom(self, rom):
        pct = 40.0 / (len(self._bsprites) + len(self._bsPals) + 3)
        # Write the main table
        self._enemyCfgTable.writeToRom(rom)
        updateProgress(pct)
        # Write the gfx ptr table
        self._bsPtrTbl.clear(len(self._bsprites))
        i = 0
        for bs in self._bsprites:
            with EbCompressedData(bs.sizeBlock()) as bsb:
                bs.writeToBlock(bsb)
                self._bsPtrTbl[i, 0].setVal(EbModule.toSnesAddr(
                    bsb.writeToFree(rom)))
            self._bsPtrTbl[i, 1].setVal(bs.size())
            i += 1
            updateProgress(pct)
        gfxAddr = EbModule.toSnesAddr(self._bsPtrTbl.writeToFree(rom))
        EbModule.writeAsmPointer(rom, self._ASMPTR_GFX, gfxAddr)
        updateProgress(pct)
        for p in self._REGPTR_GFX:
            rom.writeMulti(p, gfxAddr, 3)
        # Write the pal table
        self._bsPalsTable.clear(len(self._bsPals))
        i = 0
        for p in self._bsPals:
            self._bsPalsTable[i, 0].setVal(p.getSubpal(0))
            i += 1
            updateProgress(pct)
        EbModule.writeAsmPointer(rom, self._ASMPTR_PAL,
                                 EbModule.toSnesAddr(self._bsPalsTable.writeToFree(rom)))
        updateProgress(pct)
        # Write the groups
        self._enemyGroupBgTbl.writeToRom(rom)
        updateProgress(5)
        i = 0
        for group in self._enemyGroups:
            loc = rom.getFreeLoc(len(group) * 3 + 1)
            self._enemyGroupTbl[i, 0].setVal(EbModule.toSnesAddr(loc))
            i += 1
            for enemyID, amount in group:
                rom[loc] = amount
                rom[loc + 1] = enemyID & 0xff
                rom[loc + 2] = enemyID >> 8
                loc += 3
            rom[loc] = 0xff
        self._enemyGroupTbl.writeToRom(rom)
        updateProgress(5)

    def writeToProject(self, resourceOpener):
        pct = 40.0 / (self._enemyCfgTable.height() + 1)
        # First, write the Enemy Configuration Table
        self._enemyCfgTable.writeToProject(resourceOpener, [4, 14])
        updateProgress(pct)

        # Next, write the battle sprite images
        for i in range(self._enemyCfgTable.height()):
            if self._enemyCfgTable[i, 4].val() > 0:
                self._bsprites[self._enemyCfgTable[i, 4].val() - 1].writeToProject(
                    resourceOpener, i,
                    self._bsPals[self._enemyCfgTable[i, 14].val()].getSubpal(0))
            updateProgress(pct)

        # Now write the groups
        out = dict()
        i = 0
        pct = 5.0 / len(self._enemyGroups)
        for group in self._enemyGroups:
            entry = dict()
            for j in range(1, 4):
                field = self._enemyGroupTbl[i, j]
                entry[field.name] = field.dump()
            for j in range(2):
                field = self._enemyGroupBgTbl[i, j]
                entry[field.name] = field.dump()
            enemyList = dict()
            j = 0
            for enemyID, amount in group:
                enemyEntry = dict()
                enemyEntry["Enemy"] = enemyID
                enemyEntry["Amount"] = amount
                enemyList[j] = enemyEntry
                j += 1
            entry["Enemies"] = enemyList
            out[i] = entry
            i += 1
            updateProgress(pct)
        with resourceOpener("enemy_groups", "yml") as f:
            yaml.dump(out, f, Dumper=yaml.CSafeDumper)
        updateProgress(5)

    def readFromProject(self, resourceOpener):
        # First, read the Enemy Configuration Table
        self._enemyCfgTable.readFromProject(resourceOpener)
        pct = 40.0 / (self._enemyCfgTable.height())

        # Second, read the Battle Sprites
        bsHashes = dict()
        bsNextNum = 1
        palNextNum = 0
        for i in range(self._enemyCfgTable.height()):
            bs = EbBattleSprite()
            pal = EbPalettes(1, 16)
            try:
                bs.readFromProject(resourceOpener, i, pal)
                # Add the battle sprite
                try:
                    # self._enemyCfgTable[i,4].set(self._bsprites.index(bs))
                    bsNum = bsHashes[bs._sprite._spriteHash]
                    self._enemyCfgTable[i, 4].setVal(bsNum)
                except KeyError:
                    self._bsprites.append(bs)
                    self._enemyCfgTable[i, 4].setVal(bsNextNum)
                    bsHashes[bs._sprite._spriteHash] = bsNextNum
                    bsNextNum += 1
                # Add the palette
                # TODO should probably use hash table here too?
                #      then again, I don't think it's actually a bottleneck
                try:
                    self._enemyCfgTable[i, 14].setVal(self._bsPals.index(pal))
                except ValueError:
                    self._bsPals.append(pal)
                    self._enemyCfgTable[i, 14].setVal(palNextNum)
                    palNextNum += 1
            except IOError:
                # No battle sprite PNG
                self._enemyCfgTable[i, 4].setVal(0)
                self._enemyCfgTable[i, 14].setVal(0)
            updateProgress(pct)

        # Third, read the groups
        self._enemyGroupTbl.readFromProject(resourceOpener, "enemy_groups")
        updateProgress(2)
        self._enemyGroupBgTbl.readFromProject(resourceOpener, "enemy_groups")
        updateProgress(2)
        self._enemyGroups = []
        pct = 4.0 / 484
        with resourceOpener("enemy_groups", "yml") as f:
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            updateProgress(2)
            for group in input:
                tmp1 = input[group]["Enemies"]
                enemyList = []
                i = 0
                for enemy in tmp1:
                    tmp2 = tmp1[i]
                    enemyList.append((tmp2["Enemy"], tmp2["Amount"]))
                    i += 1
                self._enemyGroups.append(enemyList)
                updateProgress(pct)

    def upgradeProject(self, oldVersion, newVersion, rom, resourceOpenerR,
                       resourceOpenerW, resourceDeleter):
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion == 3:
            replaceField("enemy_configuration_table",
                         '"The" Flag', None,
                         {0: "False",
                          1: "True"},
                         resourceOpenerR, resourceOpenerW)
            replaceField("enemy_configuration_table",
                         "Boss Flag", None,
                         {0: "False",
                          1: "True"},
                         resourceOpenerR, resourceOpenerW)
            replaceField("enemy_configuration_table",
                         "Run Flag", None,
                         {6: "Unknown",
                          7: "True",
                          8: "False"},
                         resourceOpenerR, resourceOpenerW)
            replaceField("enemy_configuration_table",
                         "Item Rarity", None,
                         {0: "1/128",
                          1: "2/128",
                          2: "4/128",
                          3: "8/128",
                          4: "16/128",
                          5: "32/128",
                          6: "64/128",
                          7: "128/128"},
                         resourceOpenerR, resourceOpenerW)
            self.upgradeProject(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)
        else:
            self.upgradeProject(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)
