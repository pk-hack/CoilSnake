from modules.GenericModule import GenericModule

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

class EbModule(GenericModule):
    def compatibleWithRomtype(self, romtype):
        return romtype == "Earthbound"
