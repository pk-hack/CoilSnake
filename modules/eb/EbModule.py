from modules.GenericModule import GenericModule

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

# Comp/Decomp

def initBitrevs():
    bitrevs = range(0,256)
    bitrevs = map(lambda x: (((x >> 1) & 0x55) | ((x << 1) & 0xAA)), bitrevs)
    bitrevs = map(lambda x: (((x >> 2) & 0x33) | ((x << 2) & 0xCC)), bitrevs)
    bitrevs = map(lambda x: (((x >> 4) & 0x0F) | ((x << 4) & 0xF0)), bitrevs)
    return bitrevs

_bitrevs = initBitrevs()

# Adapted from JHack
def decomp(rom, cdata):
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
