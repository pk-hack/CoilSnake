import array
import os

from nose.tools import nottest
from nose.tools import assert_equal

from coilsnake.modules.eb import EbModule, NativeComp
from coilsnake.model.common.blocks import Rom
from tests.coilsnake_test import CoilSnakeTestCase


class TestEbModule(CoilSnakeTestCase):
    """
    A test class for the EbModule module
    """

    def setup(self):
        self.rom = Rom()
        self.rom.from_file(os.path.join(self.TEST_DATA_DIR, "roms", "EB_fake_24mbit.smc"))

    @nottest
    def test_decomp(self, decomp):
        onett_map = array.array('B')
        with Rom() as eb_rom:
            eb_rom.from_file(os.path.join(self.TEST_DATA_DIR, "roms", "true_EarthBound.smc"))
            onett_map.fromlist(decomp(eb_rom, 0x2021a8))

        onett_map_expect = array.array('B')
        with open(os.path.join(self.TEST_DATA_DIR, "binaries", "true_onett_map_graphics.smc"), 'rb') as f:
            onett_map_expect.fromstring(f.read())

        assert_equal(len(onett_map), len(onett_map_expect))
        assert_equal(onett_map, onett_map_expect)

    @nottest
    def test_comp(self, comp, decomp):
        a = array.array('B')
        with open(os.path.join(self.TEST_DATA_DIR, "binaries", "true_onett_map_graphics.smc"), 'rb') as f:
            a.fromstring(f.read())
        uncompressed_data = a.tolist()

        compressed_data = comp(uncompressed_data)
        assert_equal(len(compressed_data), 10877)

        with Rom() as fake_eb_rom:
            fake_eb_rom.from_file(os.path.join(self.TEST_DATA_DIR, "roms", "EB_fake_32mbit.smc"))
            fake_eb_rom[0x300000:0x300000 + len(compressed_data)] = compressed_data
            reuncompressed_data = decomp(fake_eb_rom, 0x300000)

        assert_equal(len(reuncompressed_data), len(uncompressed_data))
        assert_equal(reuncompressed_data, uncompressed_data)

    @nottest
    def _test_python_comp(self):
        self.test_comp(EbModule._comp, EbModule.decomp)

    @nottest
    def _test_python_decomp(self):
        self.test_decomp(EbModule._decomp)

    def test_native_comp(self):
        self.test_comp(NativeComp.comp, NativeComp.decomp)

    def test_native_decomp(self):
        self.test_decomp(NativeComp.decomp)

    def test_default_comp(self):
        self.test_comp(EbModule.comp, EbModule.decomp)

    def test_default_decomp(self):
        self.test_decomp(EbModule.decomp)

    def test_palette_IO(self):
        c = (48, 32, 16)
        EbModule.writePaletteColor(self.rom, 0, c)
        c2 = EbModule.readPaletteColor(self.rom, 0)
        assert_equal(c, c2)

        pal = [(176, 232, 24), (40, 152, 88), (216, 208, 136), (160, 0, 88),
               (56, 40, 96), (112, 16, 240), (112, 64, 88), (48, 88, 0), (56,
                                                                          136, 64), (176, 104, 144), (0, 48, 224),
               (224, 224, 136),
               (56, 248, 168), (56, 216, 80), (184, 48, 248), (200, 112, 32)]
        EbModule.writePalette(self.rom, 0, pal)
        pal2 = EbModule.readPalette(self.rom, 0, 16)
        assert_equal(pal, pal2)

    def test_asm_pointer_IO(self):
        ptr = EbModule.readAsmPointer(self.rom, 0xeefb)
        assert_equal(ptr, 0xe14f2a)

        EbModule.writeAsmPointer(self.rom, 0, 0xabcdef01)
        assert_equal(self.rom[0:8].to_list(), [0x0, 0x01, 0xef, 0x0, 0x0, 0x0, 0xcd, 0xab])

        ptr2 = EbModule.readAsmPointer(self.rom, 0)
        assert_equal(0xabcdef01, ptr2)