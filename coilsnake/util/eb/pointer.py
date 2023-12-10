from coilsnake.exceptions.common.exceptions import InvalidArgumentError


def from_snes_address(address):
    if address < 0:
        raise InvalidArgumentError("Invalid snes address[{:#x}]".format(address))
    elif address >= 0xc00000:
        return address - 0xc00000
    else:
        return address


def to_snes_address(address):
    if address >= 0x400000:
        return address
    else:
        return address + 0xc00000


def read_asm_pointer(block, offset):
    part1 = block[offset + 1] | (block[offset + 2] << 8)
    part2 = block[offset + 6] | (block[offset + 7] << 8)
    return part1 | (part2 << 16)


def write_asm_pointer(block, offset, pointer):
    block[offset + 1] = pointer & 0xff
    block[offset + 2] = (pointer >> 8) & 0xff
    block[offset + 6] = (pointer >> 16) & 0xff
    block[offset + 7] = (pointer >> 24) & 0xff

def write_xl_pointer(block, offset, pointer):
    block[offset + 1] = pointer & 0xff
    block[offset + 2] = (pointer >> 8) & 0xff
    block[offset + 3] = (pointer >> 16) & 0xff
