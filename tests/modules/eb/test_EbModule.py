import array
import os
from zlib import crc32

from nose.tools import nottest
from nose.tools import assert_equal

from coilsnake.modules.eb import EbModule
from coilsnake.model.common.blocks import Rom
from coilsnake.util.eb import native_comp
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR


class TestEbModule(BaseTestCase):
    """
    A test class for the EbModule module
    """

    def setup(self):
        self.rom = Rom()
        self.rom.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_24mbit.smc"))

    @nottest
    def test_decomp(self, decomp):
        onett_map = array.array('B')
        with Rom() as eb_rom:
            eb_rom.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
            onett_map.fromlist(decomp(eb_rom, 0x2021a8))

        assert_equal(len(onett_map), 18496)
        assert_equal(crc32(onett_map), 739047015)

    @nottest
    def test_comp(self, comp, decomp):
        a = array.array('B')
        with open(os.path.join(TEST_DATA_DIR, "binaries", "compressible.bin"), 'rb') as f:
            a.frombytes(f.read())
        assert_equal(len(a), 18496)

        uncompressed_data = a.tolist()
        compressed_data = comp(uncompressed_data)
        assert_equal(len(compressed_data), 58)

        with Rom() as fake_eb_rom:
            fake_eb_rom.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_32mbit.smc"))
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
        self.test_comp(native_comp.comp, native_comp.decomp)

    def test_native_decomp(self):
        self.test_decomp(native_comp.decomp)

    def test_default_comp(self):
        self.test_comp(EbModule.comp, EbModule.decomp)

    def test_default_decomp(self):
        self.test_decomp(EbModule.decomp)