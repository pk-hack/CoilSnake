import EbModule
from EbTablesModule import EbTable, TextTableEntry
from EbDataBlocks import EbCompressedData
from CompressedGraphicsModule import EbTileGraphics, EbArrangement, EbPalettes
from modules.Progress import updateProgress

from PIL import Image

# Preview Arrangement Palette
#[0, 0, 0, 0, 1, 1, 1, 4, 4, 4, 4, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 4, 4, 4, 4, 6, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 6, 0, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 6, 6, 6, 6, 3, 3, 6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 0, 0, 7, 7, 7, 7, 7, 7, 7 ]
class WindowGraphicsModule(EbModule.EbModule):
    _name = "Window Graphics"
    _ASMPTR_1 = 0x47c47
    _ASMPTR_2 = 0x47caa
    _ASMPTRS_NAMES = [0x1F70F, 0x1F72A, 0x1F745, 0x1F760, 0x1F77B]
    _PREVIEW_SUBPALS = [0, 0, 0, 0, 1, 1, 1, 4, 4, 4, 4, 6, 6, 6, 6, 6, 7, 7, 7,
            7, 7, 7, 7, 4, 4, 4, 4, 6, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 6, 0,
            1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 6, 6, 6,
            6, 3, 3, 6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 6, 3, 3, 3,
            3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0,
            0, 0, 0, 1, 0, 0 ]
    def __init__(self):
        self._gfx1 = EbTileGraphics(416, 8, 2)
        self._gfx2 = EbTileGraphics(7, 8, 2)
        self._flavPals = [EbPalettes(8,4) for i in range(7)]
        self._flavNames = [(i,TextTableEntry(None, 25)) for i in self._ASMPTRS_NAMES]
    def freeRanges(self):
        return [(0x200000, 0x20079f)] # Graphics
    def readFromRom(self, rom):
        with EbCompressedData() as tgb1:
            tgb1.readFromRom(rom, EbModule.toRegAddr(
                EbModule.readAsmPointer(rom, self._ASMPTR_1)))
            self._gfx1.readFromBlock(tgb1)
        updateProgress(20)
        with EbCompressedData() as tgb2:
            tgb2.readFromRom(rom, EbModule.toRegAddr(
                EbModule.readAsmPointer(rom, self._ASMPTR_2)))
            self._gfx2.readFromBlock(tgb2)
        updateProgress(20)
        # Read palettes
        loc = 0x201fc8
        for pal in self._flavPals:
            pal.readFromBlock(rom, loc=loc)
            loc += 64
        updateProgress(5)
        # Read names
        for ptr, field in self._flavNames:
            field.readFromRom(rom, EbModule.toRegAddr(
                EbModule.readAsmPointer(rom, ptr)))
        updateProgress(5)
    def writeToRom(self, rom):
        with EbCompressedData(self._gfx1.sizeBlock()) as gb:
            self._gfx1.writeToBlock(gb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_1,
                    EbModule.toSnesAddr(gb.writeToFree(rom)))
        updateProgress(20)
        with EbCompressedData(self._gfx2.sizeBlock()) as gb:
            self._gfx2.writeToBlock(gb)
            EbModule.writeAsmPointer(rom, self._ASMPTR_2,
                    EbModule.toSnesAddr(gb.writeToFree(rom)))
        updateProgress(20)
        # Write pals
        loc = 0x201fc8
        for pal in self._flavPals:
            pal.writeToBlock(rom, loc=loc)
            loc += 64
        updateProgress(5)
        # Write names
        for ptr, field in self._flavNames:
            loc = EbModule.toSnesAddr(field.writeToFree(rom))
            EbModule.writeAsmPointer(rom, ptr, loc)
        updateProgress(5)
    def writeToProject(self, resourceOpener):
        arr1 = EbArrangement(16, 26)
        for i in range(416):
            arr1[i%16,i/16] = (False, False, False, self._PREVIEW_SUBPALS[i], i)
        i = 0
        for pal in self._flavPals:
            with resourceOpener("WindowGraphics/Windows1_" + str(i),
                    "png") as imgFile:
                img1 = arr1.toImage(self._gfx1, pal)
                img1.save(imgFile, "png")
            with resourceOpener("WindowGraphics/Windows2_" + str(i),
                    "png") as imgFile:
                img2 = self._gfx2.dumpToImage(pal.getSubpal(7), width=7)
                img2.save(imgFile, "png")
            i += 1
        updateProgress(40)
        # Write names
        with resourceOpener("WindowGraphics/flavor_names", "txt") as f:
            for ptr, field in self._flavNames:
                print >>f, field.dump()
        updateProgress(10)
    def readFromProject(self, resourceOpener):
        # Read graphics. Just use the first of each image.
        with resourceOpener("WindowGraphics/Windows1_0", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("WindowGraphics/Windows1_0 is not an indexed PNG.")
            self._gfx1.loadFromImage(img)
        updateProgress(20)
        with resourceOpener("WindowGraphics/Windows2_0", "png") as imgFile:
            img = Image.open(imgFile)
            if img.mode != 'P':
                raise RuntimeError("WindowGraphics/Windows2_0 is not an indexed PNG.")
            self._gfx2.loadFromImage(img)
        updateProgress(20)
        # Read pals from Windows1 of each flavor.
        # Read subpal 7 from Windows2 of each flavor.
        i = 0
        for pal in self._flavPals:
            # Read all the palette data from Windows1
            with resourceOpener("WindowGraphics/Windows1_" + str(i),
                    "png") as imgFile:
                img = Image.open(imgFile)
                if img.mode != 'P':
                    raise RuntimeError("WindowGraphics/Windows1_" + str(i) + " is not an indexed PNG.")
                palData = img.getpalette()
                m=0
                for j in range(8):
                    for k in range(4):
                        pal[j,k] = (palData[m], palData[m+1], palData[m+2])
                        m += 3
            # Overwrite subpalette 7 from the palette of Windows2
            with resourceOpener("WindowGraphics/Windows2_" + str(i),
                    "png") as imgFile:
                img = Image.open(imgFile)
                if img.mode != 'P':
                    raise RuntimeError("WindowGraphics/Windows2_" + str(i) + " is not an indexed PNG.")
                palData = img.getpalette()
                m=0
                for k in range(4):
                    pal[7,k] = (palData[m], palData[m+1], palData[m+2])
                    m += 3
            i += 1
        updateProgress(5)
        # Read names
        with resourceOpener("WindowGraphics/flavor_names", "txt") as f:
            for ptr, field in self._flavNames:
                field.load(f.readline()[:-1])
        updateProgress(5)
