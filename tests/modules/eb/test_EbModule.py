import array
from nose.tools import nottest
import os
from nose.tools import assert_equal, assert_is_none

import modules.eb.EbModule
import modules.eb.NativeComp
from modules import Rom
import coilsnake_test


class TestEbModule(coilsnake_test.CoilSnakeTestCase):
    """
    A test class for the EbModule module
    """

    def setup(self):
        self.rom = Rom.Rom(os.path.join(self.COILSNAKE_RESOURCES_DIR, "romtypes.yaml"))
        self.rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "EB_fake_24mbit.smc"))

    @nottest
    def test_decomp(self, decomp):
        onett_map = array.array('B')
        with Rom.Rom(os.path.join(self.COILSNAKE_RESOURCES_DIR, "romtypes.yaml")) as eb_rom:
            eb_rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "true_EarthBound.smc"))
            onett_map.fromlist(decomp(eb_rom, 0x2021a8))

        onett_map_expect = array.array('B')
        with open(os.path.join(self.TEST_DATA_DIR, "binaries", "onett_map_graphics.smc"), 'rb') as f:
            onett_map_expect.fromstring(f.read())

        assert_equal(len(onett_map), len(onett_map_expect))
        assert_equal(onett_map, onett_map_expect)

    @nottest
    def test_comp(self, comp, decomp):
        a = array.array('B')
        with open(os.path.join(self.TEST_DATA_DIR, "binaries", "onett_map_graphics.smc"), 'rb') as f:
            a.fromstring(f.read())
        uncompressed_data = a.tolist()

        compressed_data = comp(uncompressed_data)
        assert_equal(len(compressed_data), 10877)

        with Rom.Rom(os.path.join(self.COILSNAKE_RESOURCES_DIR, "romtypes.yaml")) as fake_eb_rom:
            fake_eb_rom.load(os.path.join(self.TEST_DATA_DIR, "roms", "EB_fake_32mbit.smc"))
            fake_eb_rom.write(0x300000, compressed_data)
            reuncompressed_data = decomp(fake_eb_rom, 0x300000)

        assert_equal(len(reuncompressed_data), len(uncompressed_data))
        assert_equal(reuncompressed_data, uncompressed_data)

    @nottest
    def _test_python_comp(self):
        self.test_comp(modules.eb.EbModule._comp, modules.eb.EbModule.decomp)

    @nottest
    def _test_python_decomp(self):
        self.test_decomp(modules.eb.EbModule._decomp)

    def test_native_comp(self):
        self.test_comp(modules.eb.NativeComp.comp, modules.eb.EbModule._decomp)

    def test_native_decomp(self):
        self.test_decomp(modules.eb.NativeComp.decomp)

    def test_default_comp(self):
        self.test_comp(modules.eb.EbModule.comp, modules.eb.EbModule.decomp)

    def test_default_decomp(self):
        self.test_decomp(modules.eb.EbModule.decomp)

    def test_palette_IO(self):
        c = (48, 32, 16)
        modules.eb.EbModule.writePaletteColor(self.rom, 0, c)
        c2 = modules.eb.EbModule.readPaletteColor(self.rom, 0)
        assert_equal(c, c2)

        pal = [(176, 232, 24), (40, 152, 88), (216, 208, 136), (160, 0, 88),
                (56, 40, 96), (112, 16, 240), (112, 64, 88), (48, 88, 0), (56,
                    136, 64), (176, 104, 144), (0, 48, 224), (224, 224, 136),
                (56, 248, 168), (56, 216, 80), (184, 48, 248), (200, 112, 32)]
        modules.eb.EbModule.writePalette(self.rom, 0, pal)
        pal2 = modules.eb.EbModule.readPalette(self.rom, 0, 16)
        assert_equal(pal, pal2)

    def test_asm_pointer_IO(self):
        ptr = modules.eb.EbModule.readAsmPointer(self.rom, 0xeefb)
        assert_equal(ptr, 0xe14f2a)

        modules.eb.EbModule.writeAsmPointer(self.rom, 0, 0xabcdef01)
        assert_equal(self.rom.readList(0, 8).tolist(),
                     [ 0x0, 0x01, 0xef, 0x0, 0x0, 0x0, 0xcd, 0xab ])

        ptr2 = modules.eb.EbModule.readAsmPointer(self.rom, 0)
        assert_equal(0xabcdef01, ptr2)