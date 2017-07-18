from zlib import crc32


##### The logic for the following code that reads/writes to tile-based graphical data is borrowed from HackModule.java
##### in JHack, written by AnyoneEB.
def read_1bpp_graphic_from_block(source, target, offset, x=0, y=0, height=8):
    """Reads an graphic stored in the 1 bit-per-pixel format from a block to a 2D array of pixels.
    :param source: block to read from
    :param target: 2D pixel array to write to
    :param offset: offset in the block from where to read the graphical data
    :param x: x offset on the target image to write to
    :param y: y offset on the target image to write to
    :param height: the height in pixels of the graphic to read"""
    for i in range(height):
        b = source[offset]
        offset += 1
        for j in range(8):
            target[i + y][7 - j + x] = (b & (1 << j)) >> j
    return height


def write_1bpp_graphic_to_block(source, target, offset, x=0, y=0, height=8):
    """Writes an 8x8 graphic stored in the 1 bits-per-pixel format to a block from the specified area in the image.
    :param source: 2D pixel array to read from
    :param target: block to write to
    :param offset: offset in the block where to write the graphical data
    :param x: x offset on the source image to read from
    :param y: y offset on the source image to read from
    :param height: the height in pixels of the graphic to write"""
    for i in range(height):
        b = 0
        for j in range(8):
            b |= (source[i + y][7 - j + x] & 1) << j
        target[offset] = b
        offset += 1
    return height


def read_2bpp_graphic_from_block(target, source, offset, x=0, y=0, bit_offset=0):
    """Reads an 8x8 graphic stored in the 2 bits-per-pixel format from a block to a 2D array of pixels.
    :param target: 2D pixel array to write to
    :param source: block to read from
    :param offset: offset in the block from where to read the graphical data
    :param x: x offset on the target image to write to
    :param y: y offset on the target image to write to
    :param bit_offset: number of bits to shift each color data before writing it to the target"""
    tmp1 = 0
    for i in range(y, y + 8):
        for k in range(0, 2):
            b = source[offset]
            offset += 1
            tmp1 = k + bit_offset
            for j in range(0, 8):
                target[i][7 - j + x] |= ((b & (1 << j)) >> j) << tmp1
    return 16


def write_2bpp_graphic_to_block(source, target, offset, x=0, y=0, bit_offset=0):
    """Writes an 8x8 graphic stored in the 2 bits-per-pixel format to a block from the specified area in the image.
    :param source: 2D pixel array to read from
    :param target: block to write to
    :param offset: offset in the block from where to read the graphical data
    :param x: x offset on the source image to read from
    :param y: y offset on the source image to read from
    :param bit_offset: number of bits to shift the color data before writing it to the target"""
    bit_offset = max(0, bit_offset)
    tmp1 = tmp2 = tmp3 = 0
    for i in range(0, 8):
        for k in range(0, 2):
            tmp1 = k + bit_offset
            tmp2 = 1 << tmp1
            tmp3 = 0
            for j in range(0, 8):
                tmp3 |= ((source[i + y][7 - j + x] & tmp2) >> tmp1) << j
            target[offset] = tmp3
            offset += 1
    return 16


def read_4bpp_graphic_from_block(target, source, offset, x=0, y=0, bit_offset=0):
    """Reads an 8x8 graphic stored in the 4 bits-per-pixel format from a block to a 2D array of pixels.
    :param target: 2D pixel array to write to
    :param source: block to read from
    :param offset: offset in the block where the graphical data should be written
    :param x: x offset on the target image to read from
    :param y: y offset on the target image to read from
    :param bit_offset: number of bits to shift the color data before writing it to the target"""
    read_2bpp_graphic_from_block(target, source, offset, x, y, bit_offset)
    read_2bpp_graphic_from_block(target, source, offset + 16, x, y, bit_offset + 2)
    return 32


def write_4bpp_graphic_to_block(source, target, offset, x=0, y=0, bit_offset=0):
    """Writes an 8x8 graphic stored in the 4 bits-per-pixel format to a block from the specified area in the image.
    :param target: block to write to
    :param source: 2D pixel array to read from
    :param offset: offset in the block from where to read the graphical data
    :param x: x offset on the target image to write to
    :param y: y offset on the target image to write to
    :param bit_offset: number of bits to shift the color data before writing it to the target"""
    write_2bpp_graphic_to_block(source, target, offset, x, y, bit_offset)
    write_2bpp_graphic_to_block(source, target, offset + 16, x, y, bit_offset + 2)
    return 32


def read_8bpp_graphic_from_block(target, source, offset, x=0, y=0):
    """Reads an 8x8 graphic stored in the 8 bits-per-pixel format from a block to a 2D array of pixels.
    :param target: 2D pixel array to write to
    :param source: block to read from
    :param offset: offset in the block from where to read the graphical data
    :param x: x offset on the target image to write to
    :param y: y offset on the target image to write to
    :param bit_offset: number of bits to shift each color data before writing it to the target"""
    for i in range(0, 4):
        read_2bpp_graphic_from_block(target, source, offset + 16 * i, x, y, 2 * i)
    return 64


def write_8bpp_graphic_to_block(source, target, offset, x=0, y=0):
    """Reads an 8x8 graphic stored in the 8 bits-per-pixel format from a block to a 2D array of pixels.
    :param target: 2D pixel array to write to
    :param source: block to read from
    :param offset: offset in the block where the graphical data should be written
    :param x: x offset on the target image to read from
    :param y: y offset on the target image to read from
    :param bit_offset: number of bits to shift the color data before writing it to the target"""
    for i in range(0, 4):
        write_2bpp_graphic_to_block(source, target, offset + 16 * i, x, y, 2 * i)
    return 64


def hash_tile(tile):
    csum = 0
    for col in tile:
        # Generate same crc across python versions
        # https://docs.python.org/3/library/zlib.html#zlib.crc32
        csum = crc32(col, csum) & 0xffffffff
    return csum