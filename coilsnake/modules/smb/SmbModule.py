from coilsnake.model.common.blocks import ROM_TYPE_NAME_SUPER_MARIO_BROS
from coilsnake.modules.common.GenericModule import GenericModule

def charToByte(c):
    if (c >= '0') and (c <= '9'):
        return ord(c) - 0x30
    elif (c >= 'A') and (c <= 'Z'):
        return ord(c) - 0x37
    elif c == ' ':
        return 0x24
    elif c == '-':
        return 0x28
    elif c == 'x':
        return 0x29
    elif c == '!':
        return 0x2B
    elif c == 'o':
        return 0x2E
    elif c == '@':
        return 0xCF


def byteToChar(b):
    if b <= 9:
        return chr(0x30 + b)
    elif b <= 0x23:
        return chr(0x37 + b)
    elif b == 0x24:
        return ' '
    elif b == 0x28:
        return '-'
    elif b == 0x29:
        return 'x'
    elif b == 0x2A:
        return ' '
    elif b == 0x2B:
        return '!'
    elif b == 0x2E:
        return 'o'
    elif b == 0xCF:
        return '@'


def readText(rom, addr, maxlen):
    t = rom.readList(addr, maxlen)
    str = ''
    for c in t:
        if c == 0:
            return str
        else:
            str += byteToChar(c)
    return str


def writeText(rom, addr, text, maxlen):
    pos = 0
    for i in text:
        if pos >= maxlen:
            break
        rom.write(addr + pos, charToByte(i))
        pos += 1
    if pos < maxlen:
        rom.write(addr + pos, [0x24] * (maxlen - pos))


class SmbModule(GenericModule):
    @staticmethod
    def is_compatible_with_romtype(romtype):
        return romtype == ROM_TYPE_NAME_SUPER_MARIO_BROS
