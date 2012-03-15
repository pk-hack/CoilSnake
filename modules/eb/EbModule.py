from modules.GenericModule import GenericModule

try:
    from modules.eb import NativeComp
    hasNativeComp = True
except ImportError:
    hasNativeComp = False

import Rom

class EbModule(GenericModule):
    def compatibleWithRomtype(self, romtype):
        return romtype == "Earthbound"

# Helper functions

def toRegAddr(addr):
    if (addr >= 0xc00000):
        return addr - 0xc00000
    else:
        return addr

def toSnesAddr(addr):
    if (addr >= 0x400000):
        return addr
    else:
        return addr + 0xc00000

# [A9 ZZ YY 85 0E A9 XX WW] <-> $WWXXYYZZ
def readAsmPointer(rom, addr):
    part1 = rom[addr+1] | (rom[addr+2] << 8)
    part2 = rom[addr+6] | (rom[addr+7] << 8)
    return part1 | (part2 << 16)

def writeAsmPointer(rom, addr, ptr):
    rom[addr] = 0xa9
    rom[addr+1] = ptr & 0xff
    rom[addr+2] = (ptr >> 8) & 0xff
    rom[addr+3] = 0x85
    rom[addr+4] = 0x0e
    rom[addr+5] = 0xa9
    rom[addr+6] = (ptr >> 16) & 0xff
    rom[addr+7] = (ptr >> 24) & 0xff

# From JHack
def read2BPPArea(target, source, off, x, y, bitOffset=-1):
    if bitOffset < 0:
        bitOffset = 0
    offset = off
    for i in range(0, 8):
        for k in range(0, 2):
            b = source[offset]
            offset += 1
            for j in range(0, 8):
                target[7-j + x][i+y] |= (((b & (1 << j)) >> j) << (k +
                    bitOffset))
    return offset - off

# From JHack
def read4BPPArea(target, source, off, x, y, bitOffset=-1):
    if bitOffset < 0:
        bitOffset = 0
    read2BPPArea(target, source, off, x, y, bitOffset)
    read2BPPArea(target, source, off + 16, x, y, bitOffset + 2)
    return 32

# From JHack
def read8BPPArea(target, source, off, x, y):
    for i in range(0,4):
        read2BPPArea(target, source, off + 16 * i, x, y, 2 * i)
    return 64

# From JHack
def write2BPPArea(source, target, off, x, y, bitOffset=0):
    if bitOffset < 0:
        bitOffset = 0
    offset = off
    for i in range(0, 8):
        for k in range(0, 2):
            target[offset] = 0
            for j in range(0,8):
                target[offset] |= ((source[7 - j + x][i + y]
                    & (1 << (k + bitOffset))) >> (k + bitOffset)) << j
            offset += 1
    return offset - off

# From JHack
def write4BPPArea(source, target, off, x, y, bitOffset=0):
    if bitOffset < 0:
        bitOffset = 0
    write2BPPArea(source, target, off, x, y, bitOffset)
    write2BPPArea(source, target, off + 16, x, y, bitOffset + 2)
    return 32

def readPaletteColor(rom, addr):
    bgrBlock = ((rom[addr] & 0xff) | ((rom[addr+1] & 0xff) << 8)) & 0x7FFF
    return ((bgrBlock & 0x001f) * 8,
            ((bgrBlock & 0x03e0) >> 5) * 8,
            (bgrBlock >> 10) * 8)

def readPalette(rom, addr, ncolors):
    return map(lambda x: readPaletteColor(rom, addr+2*x), range(0,ncolors))

def writePaletteColor(rom, addr, color):
    (r, g, b) = color
    bgrBlock = (((r >> 3) & 0x1f)
            | (((g >> 3) & 0x1f) << 5)
            | (((b >> 3) & 0x1f) << 10)) & 0x7fff
    rom.write(addr, bgrBlock & 0xff)
    rom.write(addr+1, bgrBlock >> 8)

def writePalette(rom, addr, pals):
    for i in range(0,len(pals)):
        writePaletteColor(rom, addr + i*2, pals[i])

def readStandardText(rom, addr, maxlen):
    t = rom.readList(addr, maxlen)
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
        rom.write(addr + pos, ord(i)+0x30)
        pos += 1

# Comp/Decomp

def initBitrevs():
    bitrevs = range(0,256)
    bitrevs = map(lambda x: (((x >> 1) & 0x55) | ((x << 1) & 0xAA)), bitrevs)
    bitrevs = map(lambda x: (((x >> 2) & 0x33) | ((x << 2) & 0xCC)), bitrevs)
    bitrevs = map(lambda x: (((x >> 4) & 0x0F) | ((x << 4) & 0xF0)), bitrevs)
    return bitrevs

_bitrevs = initBitrevs()

# Adapted from JHack
def _decomp(rom, cdata):
    start = cdata
    bpos = 0
    bpos2 = 0
    tmp = None
    buffer = []
    while rom.read(cdata) != 0xff:
        if cdata >= len(rom):
            return [-8, 0]
        cmdtype = rom.read(cdata) >> 5
        len_ = (rom.read(cdata) & 0x1f) + 1
        if cmdtype == 7:
            cmdtype = (rom.read(cdata) & 0x1c) >> 2
            len_ = ((rom.read(cdata) & 3) << 8) + rom.read(cdata+1) + 1
            cdata += 1
        if bpos + len_ < 0:
            return [ -1, cdata - start + 1 ]
        cdata += 1
        if cmdtype >= 4:
            bpos2 = (rom.read(cdata) << 8) + rom.read(cdata + 1)
            if (bpos2 < 0):
                return [ -2, cdata - start + 1 ]
            cdata += 2

        if cmdtype == 0:
            buffer += rom.readList(cdata, len_)
            bpos += len_
            cdata += len_
        elif cmdtype == 1:
            buffer += [ rom.read(cdata) ] * len_
            bpos += len_
            cdata += 1
        elif cmdtype == 2:
            if bpos < 0:
                return [-3, cdata - start + 1]
            while len_ != 0:
                len_ -= 1
                buffer += rom.readList(cdata, 2)
            cdata += 2
        elif cmdtype == 3:
            tmp = rom.read(cdata)
            cdata += 1
            while len_ != 0:
                len_ -= 1
                buffer.append(tmp)
                tmp += 1
        elif cmdtype == 4:
            if bpos2 < 0:
                return [ -4, cdata - start + 1 ]
            buffer += buffer[bpos2:bpos2+len_]
            bpos += len_
        elif cmdtype == 5:
            if bpos2 < 0:
                return [ -5, cdata - start + 1 ]
            while len_ != 0:
                len_ -= 1
                buffer.append(_bitrevs[buffer[bpos2]])
                bpos2 += 1
                bpos += 1
        elif cmdtype == 6:
            if bpos - len_ + 1 < 0:
                return [ -6, cdata - start + 1]
            while len_ != 0:
                len_ -= 1
                buffer.append(buffer[bpos2])
                bpos += 1
                bpos2 -= 1
        elif cmdtype == 7:
            return [ -7, cdata - start + 1 ]
    return buffer

# Appends values to the buffer
def encode(buffer, length, type):
    if length > 32:
        buffer.append(0xe0 + 4 * type + ((length - 1) >> 8))
        buffer.append((length - 1) & 0xff)
    else:
        buffer.append(0x20 * type + length - 1)

def rencode(buffer, length, udata, pos):
    if length <= 0:
        return
    encode(buffer, length, 0)
    buffer += udata[pos:pos+length]

def memchr(st, needle, len_, haystack):
    len_ += st
    for i in range(st, st+len_):
        if haystack[i] == needle:
            return i
    return -1

# Adapted from Cabbage's comp()
def _comp(udata):
    pos2 = 0
    pos3 = 0
    pos4 = 0
    tmp = 0
    pos = 0
    limit = len(udata)
    buffer = []
    mainloop_break = False
    while pos < limit:
        mainloop_break = False
        pos2 = pos
        while True:
            if not ((pos2 < limit) and (pos2 < pos + 1024)):
                break

            pos3 = pos2
            while ((pos3 < limit)
                    and (pos3 < pos2 + 1024)
                    and (udata[pos2] == udata[pos3])):
                pos3 += 1

            if (pos3 - pos2) >= 3:
                rencode(buffer, pos2-pos, udata, pos)
                encode(buffer, pos3-pos2, 1)
                buffer.append(udata[pos2])
                pos = pos3
                break

            pos3 = pos2
            while ((pos3 < limit)
                    and (pos3 < pos2 + 2048)
                    and (udata[pos3] == udata[pos2])
                    and (udata[pos3 + 1] == udata[pos2 + 1])):
                pos3 += 2

            if (pos3 - pos2) >= 6:
                rencode(buffer, pos2-pos, udata, pos)
                encode(buffer, (pos3-pos2) / 2, 2)
                buffer.append(udata[pos2])
                buffer.append(udata[pos2 + 1])
                pos = pos3
                break

            tmp = 0
            pos3 = pos2
            while ((pos3 < limit)
                    and (pos3 < pos2 + 1024)
                    and (udata[pos3] == udata[pos2] + tmp)):
                pos3 += 1
                tmp += 1

            if (pos3 - pos2) >= 4:
                rencode(buffer, pos2-pos, udata, pos)
                encode(buffer, pos3-pos2, 3)
                buffer.append(udata[pos2])
                pos = pos3
                break

            pos3 = 0
            while True:
                if not (pos3 < pos2):
                    break

                tmp = 0
                pos4 = pos3
                while ((pos4 < pos2)
                        and (tmp < 1024)
                        and (udata[pos4] == udata[pos2+tmp])):
                    pos4 += 1
                    tmp += 1
                if tmp >= 5:
                    rencode(buffer, pos2-pos, udata, pos)
                    encode(buffer, tmp, 4)
                    buffer.append(pos3 >> 8)
                    buffer.append(pos3 & 0xff)
                    pos = pos2 + tmp
                    mainloop_break = True
                    break

                tmp = 0
                pos4 = pos3
                while ((pos4 < pos2)
                    and (tmp < 1024)
                    and (udata[pos4] == _bitrevs[udata[pos2 + tmp]])):
                    pos4 += 1
                    tmp += 1

                if tmp >= 5:
                    rencode(buffer, pos2-pos, udata, pos)
                    encode(buffer, tmp, 5)
                    buffer.append(pos3 >> 8)
                    buffer.append(pos3 & 0xff)
                    pos = pos2 + tmp
                    mainloop_break = True
                    break

                tmp = 0
                pos4 = pos3
                while ((pos4 >= 0) and (tmp < 1024)
                    and (udata[pos4] == udata[pos2 + tmp])):
                    pos4 -= 1
                    tmp += 1

                if tmp >= 5:
                    rencode(buffer, pos2-pos, udata, pos)
                    encode(buffer, tmp, 6)
                    buffer.append(pos3 >> 8)
                    buffer.append(pos3 & 0xff)
                    pos = pos2 + tmp
                    mainloop_break = True
                    break
                pos3 += 1
            if mainloop_break:
                break

            pos2 += 1

        # Can't compress, so just use 0 (raw)
        rencode(buffer, pos2-pos, udata, pos)
        if pos < pos2:
            pos = pos2


    buffer.append(0xff)
    return buffer

# Frontends
def decomp(rom, cdata):
    if hasNativeComp:
        return NativeComp.decomp(rom, cdata)
    else:
        return _decomp(rom, cdata)

def comp(udata):
    if hasNativeComp:
        return NativeComp.comp(udata)
    else:
        return _comp(udata)
