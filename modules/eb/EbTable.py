import EbModule

from modules.Table import Table, TableEntry, _return, genericEntryGenerator

def ebEntryGenerator(spec):
    if not spec.has_key("type"):
        return genericEntryGenerator(spec)
    elif spec['type'] == 'pointer':
        # TODO ccscript label integration
        readF = lambda r,a: r.readMulti(a,spec["size"])
        writeF = lambda r,a,d: r.writeMulti(a, d, spec["size"])
        sizeF = lambda d: spec["size"]
        loadF = lambda x: int(x[1:], 16)
        dumpF = lambda x: '$' + hex(x)[2:]
        return TableEntry(spec["name"], readF, writeF, sizeF, loadF, dumpF)
    else:
        return genericEntryGenerator(spec)

class EbTable(Table):
    tableEntryGenerator = staticmethod(ebEntryGenerator)
    def __init__(self, addr, spec):
        Table.__init__(self,addr,spec)
        self._addr = EbModule.toRegAddr(self._addr)
