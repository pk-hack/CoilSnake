from nose.tools import assert_equal, assert_list_equal
from nose.tools.nontrivial import raises

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.util.eb.pointer import from_snes_address, write_asm_pointer, read_asm_pointer, to_snes_address


def test_from_snes_address():
    assert_equal(from_snes_address(0xc00000), 0)
    assert_equal(from_snes_address(0xcf1234), 0xf1234)
    assert_equal(from_snes_address(0xeabc4f), 0x2abc4f)
    assert_equal(from_snes_address(0xffffff), 0x3fffff)
    assert_equal(from_snes_address(0x400000), 0x400000)
    assert_equal(from_snes_address(0x4daa34), 0x4daa34)
    assert_equal(from_snes_address(0x5fffff), 0x5fffff)


@raises(InvalidArgumentError)
def test_from_snes_address_negative():
    from_snes_address(-1)


def test_to_snes_address():
    assert_equal(to_snes_address(0), 0xc00000)
    assert_equal(to_snes_address(0xf1234), 0xcf1234)
    assert_equal(to_snes_address(0x2abc4f), 0xeabc4f)
    assert_equal(to_snes_address(0x3fffff), 0xffffff)
    assert_equal(to_snes_address(0x400000), 0x400000)
    assert_equal(to_snes_address(0x4daa34), 0x4daa34)
    assert_equal(to_snes_address(0x5fffff), 0x5fffff)


def test_read_asm_pointer():
    block = Block()
    block.from_list([0xee, 0xee, 0x12, 0x34, 0xee, 0xee, 0xee, 0x56, 0x78])
    assert_equal(read_asm_pointer(block, 1), 0x78563412)


def test_write_asm_pointer():
    block = Block()
    block.from_list([0xee] * 9)
    write_asm_pointer(block, 1, 0xabcdef12)
    assert_list_equal(block.to_list(), [0xee, 0xee, 0x12, 0xef, 0xee, 0xee, 0xee, 0xcd, 0xab])