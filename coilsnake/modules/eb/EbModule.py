import sys

from coilsnake.modules.common.GenericModule import GenericModule
from coilsnake.model.common.blocks import ROM_TYPE_NAME_EARTHBOUND

try:
    from coilsnake.util.eb import native_comp

    hasNativeComp = True
except ImportError:
    hasNativeComp = False

if not hasNativeComp:
    print("WARNING: Could not load native EarthBound compression library")
    raise NotImplementedError("WARNING: Could not load native EarthBound compression library")

address_labels = dict()


class EbModule(GenericModule):
    @staticmethod
    def is_compatible_with_romtype(romtype):
        return romtype == ROM_TYPE_NAME_EARTHBOUND


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
        print("Could not decompress data @ " + hex(cdata), file=sys.stderr)
        raise


def comp(udata):
    if hasNativeComp:
        return native_comp.comp(udata)
    else:
        return _comp(udata)
