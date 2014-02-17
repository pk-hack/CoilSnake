from nose.tools import assert_list_equal, assert_equal

from coilsnake.model.common.blocks import Block
from coilsnake.util.eb.graphics import read_1bpp_graphic_from_block, write_1bpp_graphic_to_block


def test_read_1bpp_graphic_from_block():
    source = Block()
    source.from_list([42,
                      0b00000011,
                      0b01110000,
                      0b01001001,
                      0b11110000,
                      0b01001010,
                      0b11001000,
                      0b01110001,
                      0b00000001])
    target = [[0 for x in range(8)] for y in range(8)]
    assert_equal(8, read_1bpp_graphic_from_block(source, target, 1, x=0, y=0, height=8))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 1, 1],
        [0, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 1],
        [1, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 1, 0],
        [1, 1, 0, 0, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 1]])


def test_read_1bpp_graphic_from_block_offset_target():
    source = Block()
    source.from_list([0b00000011,
                      0b01110000,
                      0b01001001,
                      0b11110000,
                      0b01001010,
                      0b11001000,
                      0b01110001,
                      0b00000001])
    target = [[0 for x in range(10)] for y in range(10)]
    assert_equal(8, read_1bpp_graphic_from_block(source, target, 0, x=2, y=1, height=8))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 1],
        [0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
        [0, 0, 1, 1, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])


def test_read_1bpp_graphic_from_block_rectangular_short():
    source = Block()
    source.from_list([42, 0xeb,
                      0b00000011,
                      0b01110000,
                      0b01001001,
                      0b11110000,
                      0b01001010,
                      0b11001000])
    target = [[0 for x in range(8)] for y in range(6)]
    assert_equal(6, read_1bpp_graphic_from_block(source, target, 2, x=0, y=0, height=6))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 1, 1],
        [0, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 1],
        [1, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 1, 0],
        [1, 1, 0, 0, 1, 0, 0, 0]])


def test_read_1bpp_graphic_from_block_rectangular_tall():
    source = Block()
    source.from_list([42, 11, 99,
                      0b00000011,
                      0b01110000,
                      0b01001001,
                      0b11110000,
                      0b01001010,
                      0b11001000,
                      0b01110001,
                      0b00000001,
                      0b00100000,
                      0b00110000,
                      0b00101000,
                      0b00101000,
                      0b01100000,
                      0b11100000,
                      0b11000000,
                      0b00000001,
                      12, 21])
    target = [[0 for x in range(8)] for y in range(16)]
    assert_equal(16, read_1bpp_graphic_from_block(source, target, 3, x=0, y=0, height=16))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 1, 1],
        [0, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 1],
        [1, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 1, 0],
        [1, 1, 0, 0, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1]])


def test_write_1bpp_graphic_to_block():
    source = [[0, 0, 0, 0, 0, 0, 1, 1],
              [0, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 0, 1],
              [1, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 1, 0],
              [1, 1, 0, 0, 1, 0, 0, 0],
              [0, 1, 1, 1, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 1]]
    target = Block()
    target.from_list([32] * 10)
    assert_equal(8, write_1bpp_graphic_to_block(source, target, 1, x=0, y=0, height=8))
    assert_list_equal(target.to_list(), [32,
                                         0b00000011,
                                         0b01110000,
                                         0b01001001,
                                         0b11110000,
                                         0b01001010,
                                         0b11001000,
                                         0b01110001,
                                         0b00000001,
                                         32])


def test_write_1bpp_graphic_to_block_offset_source():
    source = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
              [0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
              [0, 0, 0, 1, 0, 0, 1, 0, 0, 1],
              [0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
              [0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
              [0, 0, 1, 1, 0, 0, 1, 0, 0, 0],
              [0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    target = Block()
    target.from_list([0] * 8)
    assert_equal(8, write_1bpp_graphic_to_block(source, target, 0, x=2, y=1, height=8))
    assert_list_equal(target.to_list(), [0b00000011,
                                         0b01110000,
                                         0b01001001,
                                         0b11110000,
                                         0b01001010,
                                         0b11001000,
                                         0b01110001,
                                         0b00000001])


def test_write_1bpp_graphic_to_block_rectangular_short():
    source = [[0, 0, 0, 0, 0, 0, 1, 1],
              [0, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 0, 1],
              [1, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 1, 0],
              [1, 1, 0, 0, 1, 0, 0, 0]]
    target = Block()
    target.from_list([0xeb] * 8)
    target[0] = 42
    assert_equal(6, write_1bpp_graphic_to_block(source, target, 2, x=0, y=0, height=6))
    assert_list_equal(target.to_list(), [42, 0xeb,
                                         0b00000011,
                                         0b01110000,
                                         0b01001001,
                                         0b11110000,
                                         0b01001010,
                                         0b11001000])


def test_read_1bpp_graphic_from_block_rectangular_tall():
    source = [[0, 0, 0, 0, 0, 0, 1, 1],
              [0, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 0, 1],
              [1, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 1, 0],
              [1, 1, 0, 0, 1, 0, 0, 0],
              [0, 1, 1, 1, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 1],
              [0, 0, 1, 0, 0, 0, 0, 0],
              [0, 0, 1, 1, 0, 0, 0, 0],
              [0, 0, 1, 0, 1, 0, 0, 0],
              [0, 0, 1, 0, 1, 0, 0, 0],
              [0, 1, 1, 0, 0, 0, 0, 0],
              [1, 1, 1, 0, 0, 0, 0, 0],
              [1, 1, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 1]]
    target = Block()
    target.from_list([42, 11, 99, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 112, 113, 114, 115, 116, 12, 21])
    assert_equal(16, write_1bpp_graphic_to_block(source, target, 3, x=0, y=0, height=16))
    assert_list_equal(target.to_list(), [42, 11, 99,
                                         0b00000011,
                                         0b01110000,
                                         0b01001001,
                                         0b11110000,
                                         0b01001010,
                                         0b11001000,
                                         0b01110001,
                                         0b00000001,
                                         0b00100000,
                                         0b00110000,
                                         0b00101000,
                                         0b00101000,
                                         0b01100000,
                                         0b11100000,
                                         0b11000000,
                                         0b00000001,
                                         12, 21])