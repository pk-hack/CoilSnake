from coilsnake.util.eb.pointer import from_snes_address

def is_in_bank(bank, address):
    return (address >> 16) == bank


def not_in_bank(bank, address):
    return not is_in_bank(bank, address)


def patch(rom, size, offset, instructions):
    rom[from_snes_address(offset) : from_snes_address(offset + size)] = instructions
