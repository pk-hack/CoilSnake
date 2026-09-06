from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.util.eb.pointer import from_snes_address, write_asm_pointer, read_asm_pointer, to_snes_address

from tests.coilsnake_test import BaseTestCase

class EbPointerUtilTestCase(BaseTestCase):
    def test_from_snes_address(self):
        self.assertEqual(from_snes_address(0xc00000), 0)
        self.assertEqual(from_snes_address(0xcf1234), 0xf1234)
        self.assertEqual(from_snes_address(0xeabc4f), 0x2abc4f)
        self.assertEqual(from_snes_address(0xffffff), 0x3fffff)
        self.assertEqual(from_snes_address(0x400000), 0x400000)
        self.assertEqual(from_snes_address(0x4daa34), 0x4daa34)
        self.assertEqual(from_snes_address(0x5fffff), 0x5fffff)


    def test_from_snes_address_negative(self):
        with self.assertRaises(InvalidArgumentError):
            from_snes_address(-1)


    def test_to_snes_address(self):
        self.assertEqual(to_snes_address(0), 0xc00000)
        self.assertEqual(to_snes_address(0xf1234), 0xcf1234)
        self.assertEqual(to_snes_address(0x2abc4f), 0xeabc4f)
        self.assertEqual(to_snes_address(0x3fffff), 0xffffff)
        self.assertEqual(to_snes_address(0x400000), 0x400000)
        self.assertEqual(to_snes_address(0x4daa34), 0x4daa34)
        self.assertEqual(to_snes_address(0x5fffff), 0x5fffff)


    def test_read_asm_pointer(self):
        block = Block()
        block.from_list([0xee, 0xee, 0x12, 0x34, 0xee, 0xee, 0xee, 0x56, 0x78])
        self.assertEqual(read_asm_pointer(block, 1), 0x78563412)


    def test_write_asm_pointer(self):
        block = Block()
        block.from_list([0xee] * 9)
        write_asm_pointer(block, 1, 0xabcdef12)
        self.assertListEqual(block.to_list(), [0xee, 0xee, 0x12, 0xef, 0xee, 0xee, 0xee, 0xcd, 0xab])
