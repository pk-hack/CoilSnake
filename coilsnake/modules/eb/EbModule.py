import logging
from zlib import crc32
import sys

from coilsnake.modules.common.GenericModule import GenericModule


log = logging.getLogger(__name__)


try:
    from coilsnake.util.eb import native_comp

    hasNativeComp = True
except ImportError:
    hasNativeComp = False

if not hasNativeComp:
    print "WARNING: Could not load native EarthBound compression library"
    raise NotImplementedError("WARNING: Could not load native EarthBound compression library")

address_labels = dict()


class EbModule(GenericModule):
    @staticmethod
    def is_compatible_with_romtype(romtype):
        return romtype == "Earthbound"


# Helper functions


def toRegAddr(addr):
    if addr >= 0xc00000:
        return addr - 0xc00000
    else:
        return addr


def toSnesAddr(addr):
    if addr >= 0x400000:
        return addr
    else:
        return addr + 0xc00000


# [A9 ZZ YY 85 0E A9 XX WW] <-> $WWXXYYZZ


def readAsmPointer(rom, addr):
    part1 = rom[addr + 1] | (rom[addr + 2] << 8)
    part2 = rom[addr + 6] | (rom[addr + 7] << 8)
    return part1 | (part2 << 16)


def writeAsmPointer(rom, addr, ptr):
    rom[addr + 1] = ptr & 0xff
    rom[addr + 2] = (ptr >> 8) & 0xff
    rom[addr + 6] = (ptr >> 16) & 0xff
    rom[addr + 7] = (ptr >> 24) & 0xff


def writeAsmPointers(rom, addrs, ptr):
    for addr in addrs:
        writeAsmPointer(rom, addr, ptr)


# Used for hashing 2BPP/4BPP areas that have been read to a list of arrays


def hashArea(source):
    csum = 0
    for col in source:
        csum = crc32(col, csum)
    return csum


# From JHack
# h = height of the image


def read1BPPArea(target, source, off, h, x, y):
    for i in xrange(h):
        b = source[off]
        off += 1
        for j in xrange(8):
            target[7 - j + x][i + y] = (b & (1 << j)) >> j
    return h


# From JHack


def write1BPPArea(source, target, off, h, x, y):
    for i in xrange(h):
        b = 0
        for j in xrange(8):
            b |= (source[7 - j + x][i + y] & 1) << j
        target[off] = b
        off += 1
    return h


# From JHack


def read2BPPArea(target, source, off, x, y, bitOffset=-1):
    if bitOffset < 0:
        bitOffset = 0
    tmp1 = 0
    for i in xrange(y, y + 8):
        for k in xrange(0, 2):
            b = source[off]
            off += 1
            tmp1 = k + bitOffset
            for j in xrange(0, 8):
                target[7 - j + x][i] |= ((b & (1 << j)) >> j) << tmp1
    return 16


# From JHack


def read4BPPArea(target, source, off, x, y, bitOffset=-1):
    if bitOffset < 0:
        bitOffset = 0
    read2BPPArea(target, source, off, x, y, bitOffset)
    read2BPPArea(target, source, off + 16, x, y, bitOffset + 2)
    return 32


# From JHack


def read8BPPArea(target, source, off, x, y):
    for i in range(0, 4):
        read2BPPArea(target, source, off + 16 * i, x, y, 2 * i)
    return 64


# From JHack


def write2BPPArea(source, target, off, x, y, bitOffset=0):
    if bitOffset < 0:
        bitOffset = 0
    tmp1 = tmp2 = tmp3 = 0
    for i in xrange(0, 8):
        for k in xrange(0, 2):
            tmp1 = k + bitOffset
            tmp2 = 1 << tmp1
            tmp3 = 0
            for j in xrange(0, 8):
                # target[offset] |= ((source[7 - j + x][i + y]
                #    & (1 << (k + bitOffset))) >> (k + bitOffset)) << j
                # target[offset] |= not not (source[7 - j + x][i + y] & (1 << (k +
                #    bitOffset))) << j
                tmp3 |= ((source[7 - j + x][i + y] & tmp2) >> tmp1) << j
            target[off] = tmp3
            off += 1
    return 16


# From JHack


def write4BPPArea(source, target, off, x, y, bitOffset=0):
    if bitOffset < 0:
        bitOffset = 0
    write2BPPArea(source, target, off, x, y, bitOffset)
    write2BPPArea(source, target, off + 16, x, y, bitOffset + 2)
    return 32


# From JHack


def write8BPPArea(source, target, off, x, y):
    for i in range(0, 4):
        write2BPPArea(source, target, off + 16 * i, x, y, 2 * i)
    return 64


def readPaletteColor(rom, addr):
    bgrBlock = ((rom[addr] & 0xff) | ((rom[addr + 1] & 0xff) << 8)) & 0x7FFF
    return ((bgrBlock & 0x001f) * 8,
            ((bgrBlock & 0x03e0) >> 5) * 8,
            (bgrBlock >> 10) * 8)


def readPalette(rom, addr, ncolors):
    return (
        map(lambda x: readPaletteColor(rom, addr + 2 * x), range(0, ncolors))
    )


def writePaletteColor(rom, addr, color):
    (r, g, b) = color
    bgrBlock = (((r >> 3) & 0x1f)
                | (((g >> 3) & 0x1f) << 5)
                | (((b >> 3) & 0x1f) << 10)) & 0x7fff
    rom[addr] = bgrBlock & 0xff
    rom[addr + 1] = (bgrBlock >> 8) & 0xff


def writePalette(rom, addr, pals):
    for i in range(0, len(pals)):
        writePaletteColor(rom, addr + i * 2, pals[i])


def readStandardText(rom, addr, maxlen):
    t = rom[addr:(addr+maxlen)].to_list()
    str = ''
    for c in t:
        if c == 0:
            return str
        else:
            str += chr(c - 0x30)
    return str


def writeStandardText(rom, addr, text, maxlen):
    pos = 0
    for i in text:
        if pos >= maxlen:
            break
        rom[addr + pos] = ord(i) + 0x30
        pos += 1
    if pos < maxlen:
        rom[addr + pos] = 0


# Comp/Decomp

def _decomp(rom, cdata):
    raise NotImplementedError("Python decomp not implemented")

def _comp(udata):
    raise NotImplementedError("Python comp not implemented")


# Frontends


def decomp(rom, cdata):
    try:
        if hasNativeComp:
            return native_comp.decomp(rom, cdata)
        else:
            return _decomp(rom, cdata)
    except SystemError:
        print >> sys.stderr, "Could not decompress data @ " + hex(cdata)
        raise


def comp(udata):
    if hasNativeComp:
        return native_comp.comp(udata)
    else:
        return _comp(udata)
