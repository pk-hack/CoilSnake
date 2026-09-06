import array
import os
from zlib import crc32

from unittest import skip

from coilsnake.modules.eb import EbModule
from coilsnake.model.common.blocks import Rom
from coilsnake.util.eb import native_comp
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR, earthbound_rom_available


class TestEbModule(BaseTestCase):
    """
    A test class for the EbModule module
    """

    def setUp(self):
        self.rom = Rom()
        self.rom.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_24mbit.smc"))

    def impl_test_decomp(self, decomp):
        if not earthbound_rom_available():
            self.skipTest("real_EarthBound.smc is missing")
        onett_map = array.array('B')
        with Rom() as eb_rom:
            eb_rom.from_file(os.path.join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))
            onett_map.fromlist(decomp(eb_rom, 0x2021a8))

        self.assertEqual(len(onett_map), 18496)
        self.assertEqual(crc32(onett_map), 739047015)

    def impl_test_comp(self, comp, decomp):
        a = array.array('B')
        with open(os.path.join(TEST_DATA_DIR, "binaries", "compressible.bin"), 'rb') as f:
            a.frombytes(f.read())
        self.assertEqual(len(a), 18496)

        uncompressed_data = a.tolist()
        compressed_data = comp(uncompressed_data)
        self.assertLessEqual(len(compressed_data), 40)

        with Rom() as fake_eb_rom:
            fake_eb_rom.from_file(os.path.join(TEST_DATA_DIR, "roms", "EB_fake_32mbit.smc"))
            fake_eb_rom[0x300000:0x300000 + len(compressed_data)] = compressed_data
            reuncompressed_data = decomp(fake_eb_rom, 0x300000)

        self.assertEqual(len(reuncompressed_data), len(uncompressed_data))
        self.assertEqual(reuncompressed_data, uncompressed_data)

    @skip("Python compression fallback is unimplemented")
    def test_python_comp(self):
        self.impl_test_comp(EbModule._comp, EbModule.decomp)

    @skip("Python compression fallback is unimplemented")
    def test_python_decomp(self):
        self.impl_test_decomp(EbModule._decomp)

    def test_native_comp(self):
        self.impl_test_comp(native_comp.comp, native_comp.decomp)

    def test_native_decomp(self):
        self.impl_test_decomp(native_comp.decomp)

    def test_default_comp(self):
        self.impl_test_comp(EbModule.comp, EbModule.decomp)

    def test_default_decomp(self):
        self.impl_test_decomp(EbModule.decomp)
