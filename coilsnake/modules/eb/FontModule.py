from array import array
from PIL import Image
import yaml

from coilsnake.Progress import updateProgress
from coilsnake.modules.eb.EbDataBlocks import EbCompressedData
from coilsnake.modules.eb.CompressedGraphicsModule import EbTileGraphics, EbPalettes, EbArrangement
from coilsnake.modules.eb import EbModule


class Font:
    def __init__(self, gfxAddr, widthsAddr, charW, charH):
        self._gfxAddr = gfxAddr
        self._widthsAddr = widthsAddr
        self._charW = charW
        self._charH = charH
        self._chars = None
        self._charWidths = None

    def readFromRom(self, rom):
        self._chars = []
        addr = self._gfxAddr
        for i in range(96):
            charGfx = [array('B', [0] * self._charH)
                       for k in range(self._charW)]
            for j in range(0, self._charW, 8):
                addr += EbModule.read1BPPArea(charGfx, rom, addr,
                                              self._charH, j, 0)
            self._chars.append(charGfx)
        self._charWidths = rom[self._widthsAddr:self._widthsAddr + 96]

    def writeToRom(self, rom):
        addr = self._gfxAddr
        for char in self._chars:
            for j in range(0, self._charW, 8):
                addr += EbModule.write1BPPArea(char, rom, addr,
                                               self._charH, j, 0)
        rom.write(self._widthsAddr, self._charWidths)

    def toImage(self):
        img = Image.new("P", (self._charW * 16, self._charH * 6), 1)
        # We only need two colors: white and black
        img.putpalette([255, 255, 255, 0, 0, 0])
        # Draw the characters
        imgData = img.load()
        for i in range(16):
            for j in range(6):
                for y in range(self._charH):
                    for x in range(self._charW):
                        imgData[i * self._charW + x, j * self._charH + y] = \
                            self._chars[i + j * 16][x][y]
        return img

    def fromImage(self, img):
        self._chars = [[array('B', [0] * self._charH) for k in
                        range(self._charW)] for j in range(0, 96)]
        imgData = img.load()
        for i in range(16):
            for j in range(6):
                for y in range(self._charH):
                    for x in range(self._charW):
                        self._chars[i + j * 16][x][y] = imgData[
                                                            i * self._charW + x,
                                                            j * self._charH + y] & 1

    def dumpWidths(self):
        out = dict()
        for i in range(96):
            out[i] = self._charWidths[i]
        return out

    def loadWidths(self, input):
        self._charWidths = [0] * 96
        for i in range(96):
            self._charWidths[i] = input[i]


class FontModule(EbModule.EbModule):
    NAME = "Fonts"
    FREE_RANGES = [(0x21e528, 0x21e913)]  # Credits font graphics

    _CREDITS_PREVIEW_SUBPALS = [
        1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1,
        1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    _ASMPTR_CREDITS_GFX = 0x4f1a7
    _ADDR_CREDITS_PAL = 0x21e914

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._fonts = [
            Font(0x210cda, 0x210c7a, 16, 16),
            Font(0x2013b9, 0x201359, 16, 16),
            Font(0x2122fa, 0x21229a, 16, 16),
            Font(0x21193a, 0x2118da, 8, 16),
            Font(0x211f9a, 0x211f3a, 8, 8)
        ]
        self._cfont = EbTileGraphics(192, 8, 2)
        self._cpal = EbPalettes(2, 4)
        self._pct = 50.0 / (len(self._fonts) + 1)

    def readCreditsFontFromRom(self, rom):
        self._cpal.readFromBlock(rom, loc=self._ADDR_CREDITS_PAL)
        with EbCompressedData() as cb:
            cb.readFromRom(rom,
                           EbModule.toRegAddr(
                               EbModule.readAsmPointer(
                                   rom, self._ASMPTR_CREDITS_GFX)))
            self._cfont.readFromBlock(cb)

    def read_from_rom(self, rom):
        for f in self._fonts:
            f.readFromRom(rom)
            updateProgress(self._pct)

        self.readCreditsFontFromRom(rom)
        updateProgress(self._pct)

    def write_to_rom(self, rom):
        for f in self._fonts:
            f.writeToRom(rom)
            updateProgress(self._pct)

        self._cpal.writeToBlock(rom, loc=self._ADDR_CREDITS_PAL)
        with EbCompressedData(self._cfont.sizeBlock()) as cb:
            self._cfont.writeToBlock(cb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_CREDITS_GFX,
                                     EbModule.toSnesAddr(cb.writeToFree(rom)))
        updateProgress(self._pct)

    def writeCreditsFontToProject(self, resourceOpener):
        arr = EbArrangement(16, 12)
        for i in range(192):
            arr[i % 16, i / 16] = (False, False, False,
                                   self._CREDITS_PREVIEW_SUBPALS[i], i)
        img = arr.toImage(self._cfont, self._cpal)
        with resourceOpener("Fonts/credits", "png") as imgFile:
            img.save(imgFile, "png")
            imgFile.close()

    def write_to_project(self, resourceOpener):
        out = dict()
        i = 0
        for font in self._fonts:
            # Write the PNG
            img = font.toImage()
            with resourceOpener("Fonts/" + str(i), 'png') as imgFile:
                img.save(imgFile, 'png')

            # Write the widths
            out = font.dumpWidths()
            with resourceOpener("Fonts/" + str(i) + "_widths", "yml") as f:
                yaml.dump(out, f, default_flow_style=False,
                          Dumper=yaml.CSafeDumper)
            i += 1
            updateProgress(self._pct)

        self.writeCreditsFontToProject(resourceOpener)
        updateProgress(self._pct)

    def read_from_project(self, resourceOpener):
        i = 0
        for font in self._fonts:
            with resourceOpener("Fonts/" + str(i), "png") as imgFile:
                img = Image.open(imgFile)
                if img.mode != 'P':
                    raise RuntimeError(
                        "Fonts/" + str(i) + " is not an indexed PNG.")
                font.fromImage(img)
            with resourceOpener("Fonts/" + str(i) + "_widths", "yml") as f:
                input = yaml.load(f, Loader=yaml.CSafeLoader)
                font.loadWidths(input)
            i += 1
            updateProgress(self._pct)

        with resourceOpener("Fonts/credits", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("Fonts/credits is not an indexed PNG.")
            self._cfont.loadFromImage(img)
            self._cpal.loadFromImage(img)
        updateProgress(self._pct)

    def upgrade_project(self, oldVersion, newVersion, rom, resourceOpenerR,
                        resourceOpenerW, resourceDeleter):
        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion <= 2:
            self.readCreditsFontFromRom(rom)
            self.writeCreditsFontToProject(resourceOpenerW)
            self.upgrade_project(3, newVersion, rom, resourceOpenerR,
                                 resourceOpenerW, resourceDeleter)
        else:
            self.upgrade_project(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)
