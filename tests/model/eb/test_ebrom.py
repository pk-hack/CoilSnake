import hashlib
from os import listdir
from os.path import exists, join

from unittest import skipUnless

from coilsnake.model.common.blocks import Rom
from coilsnake.model.eb.blocks import EbRom
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR, earthbound_rom_available


def is_rom_filename(fname):
    return fname.lower().endswith(".smc") or fname.lower().endswith(".sfc")


class TestEbRom(BaseTestCase):
    @skipUnless(earthbound_rom_available(), "real_EarthBound.smc is missing")
    def setUp(self):
        self.reference_rom = Rom()
        self.reference_rom.from_file(join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))

    def tearDown(self):
        del self.reference_rom

    @skipUnless(exists(join(TEST_DATA_DIR, "roms", "variants")), "Variant ROM directory is missing")
    def test_fixing_rom_variants(self):
        for f in listdir(join(TEST_DATA_DIR, "roms", "variants")):
            if is_rom_filename(f):
                variant = EbRom()
                variant.from_file(join(TEST_DATA_DIR, "roms", "variants", f))

                self.assertEqual(self.reference_rom.data, variant.data)
                self.assertEqual(self.reference_rom.size, variant.size)
                self.assertEqual(EbRom.REFERENCE_MD5, hashlib.md5(variant.data.tobytes()).hexdigest())
