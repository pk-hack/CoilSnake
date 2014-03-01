def is_in_bank(bank, address):
    return (address >> 16) == bank


def not_in_bank(bank, address):
    return not is_in_bank(bank, address)