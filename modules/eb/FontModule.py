import EbModule
from modules.Progress import updateProgress

from array import array

from PIL import Image
import yaml

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
            charGfx = [ array('B', [0] * self._charH)
                    for k in range(self._charW) ]
            for j in range(0, self._charW, 8):
                addr += EbModule.read1BPPArea(charGfx, rom, addr,
                        self._charH, j, 0)
            self._chars.append(charGfx)
        self._charWidths = rom[self._widthsAddr:self._widthsAddr+96]
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
        img.putpalette([255,255,255,0,0,0])
        # Draw the characters
        imgData = img.load()
        for i in range(16):
            for j in range(6):
                for y in range(self._charH):
                    for x in range(self._charW):
                        imgData[i*self._charW+x, j*self._charH+y] = \
                            self._chars[i+j*16][x][y]
        return img
    def fromImage(self, img):
        self._chars = [ [ array('B', [0] * self._charH) for k in
            range(self._charW) ] for j in range(0,96) ]
        imgData = img.load()
        for i in range(16):
            for j in range(6):
                for y in range(self._charH):
                    for x in range(self._charW):
                        self._chars[i+j*16][x][y] = imgData[
                                i*self._charW+x,
                                j*self._charH+y] & 1
    def dumpWidths(self):
        out = dict()
        for i in range(96):
            out[i] = self._charWidths[i]
        return out
    def loadWidths(self, input):
        self._charWidths = [0]*96
        for i in range(96):
            self._charWidths[i] = input[i]

class FontModule(EbModule.EbModule):
    _name = "Fonts"
    def __init__(self):
        self._fonts = [
                Font(0x210cda, 0x210c7a, 16, 16),
                Font(0x2013b9, 0x201359, 16, 16),
                Font(0x2122fa, 0x21229a, 16, 16),
                Font(0x21193a, 0x2118da, 8, 16),
                Font(0x211f9a, 0x211f3a, 8, 8)
                ]
        self._pct = 50.0/len(self._fonts)
    def readFromRom(self, rom):
        for f in self._fonts:
            f.readFromRom(rom)
            updateProgress(self._pct)
    def writeToRom(self, rom):
        for f in self._fonts:
            f.writeToRom(rom)
            updateProgress(self._pct)
    def writeToProject(self, resourceOpener):
        out = dict()
        i=0
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
    def readFromProject(self, resourceOpener):
        i = 0
        for font in self._fonts:
            with resourceOpener("Fonts/" + str(i), "png") as imgFile:
                img = Image.open(imgFile)
                if img.mode != 'P':
                    raise RuntimeError("Fonts/" + str(i) + " is not an indexed PNG.")
                font.fromImage(img)
            with resourceOpener("Fonts/" + str(i) + "_widths", "yml") as f:
                input = yaml.load(f, Loader=yaml.CSafeLoader)
                font.loadWidths(input)
            i += 1
            updateProgress(self._pct)
