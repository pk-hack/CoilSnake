import hashlib
from os import listdir
from os.path import join

from nose.tools import assert_equal

from coilsnake.model.common.blocks import Rom
from coilsnake.model.eb.blocks import EbRom
from tests.coilsnake_test import BaseTestCase, TEST_DATA_DIR


def is_rom_filename(fname):
    return fname.lower().endswith(".smc") or fname.lower().endswith(".sfc")


class TestEbRom(BaseTestCase):

    def setup(self):
        self.reference_rom = Rom()
        self.reference_rom.from_file(join(TEST_DATA_DIR, "roms", "real_EarthBound.smc"))

    def teardown(self):
        del self.reference_rom

    def test_fixing_rom_variants(self):
        for f in listdir(join(TEST_DATA_DIR, "roms", "variants")):
            if is_rom_filename(f):
                variant = EbRom()
                variant.from_file(join(TEST_DATA_DIR, "roms", "variants", f))

                assert_equal(self.reference_rom.data, variant.data)
                assert_equal(self.reference_rom.size, variant.size)
                assert_equal(EbRom.REFERENCE_MD5, hashlib.md5(variant.data.tostring()).hexdigest())