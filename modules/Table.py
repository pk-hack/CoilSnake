import re
import yaml

class TableEntry:
    def __init__(self, name, readF, writeF, sizeF, loadF, dumpF):
        self._data = None
        self.name = name
        self.readF = readF
        self.writeF = writeF
        self.sizeF = sizeF
        self.loadF = loadF
        self.dumpF = dumpF
    def readFromRom(self, rom, addr):
        self._data = self.readF(rom, addr)
    def writeToRom(self, rom, addr):
        self.writeF(rom, addr, self._data)
    def size(self):
        return self.sizeF(self._data)
    def set(self, str):
        self._data = self.loadF(str)
    def dump(self):
        return self.dumpF(self._data)
    def setVal(self, val):
        self._data = val
    def val(self):
        return self._data

# For easiness of reading
def _return(x):
    return x

def genericEntryGenerator(spec, table_map):
    if not spec.has_key("type") or spec["type"] == 'int':
        readF = lambda r,a: r.readMulti(a,spec["size"])
        writeF = lambda r,a,d: r.writeMulti(a, d, spec["size"])
        sizeF = lambda d: spec["size"]
        if spec.has_key('values'):
            valuesLower = map(lambda x: str(x).lower(), spec['values'])
            def loadF(x):
                try:
                    return valuesLower.index(str(x).lower())
                except ValueError:
                    if type(x) == int:
                        return x
                    else:
                        # TODO Error, could not parse input
                        return 0
            dumpF = lambda x: spec['values'][x]
            return TableEntry(spec["name"], readF, writeF, sizeF, loadF, dumpF)
        else:
            return TableEntry(spec["name"], readF, writeF, sizeF, _return, _return)
    elif spec["type"] == 'hexint':
        readF = lambda r,a: r.readMulti(a,spec["size"])
        writeF = lambda r,a,d: r.writeMulti(a, d, spec["size"])
        sizeF = lambda d: spec["size"]
        return TableEntry(spec["name"], readF, writeF, sizeF, _return, _return)
    elif spec["type"] == 'bytearray':
        readF = lambda r,a: r.readList(a,spec['size'])
        writeF = lambda r,a,d: r.write(a,d)
        sizeF = lambda d: spec['size']
        return TableEntry(spec["name"], readF, writeF, sizeF, _return, _return)
    elif spec["type"] == 'boolean':
        readF = lambda r,a: r.read(a)
        writeF = lambda r,a,d: r.write(a,d)
        sizeF = lambda d: 1
        loadF = lambda x: (1 if x else 0)
        dumpF = lambda x: (x != 0)
        return TableEntry(spec["name"], readF, writeF, sizeF, loadF, dumpF)
    else:
        raise RuntimeError("Unknown data entry type " + spec["type"])

class Table:
    tableEntryGenerator = staticmethod(genericEntryGenerator)
    def __init__(self, addr, table_map):
        self._addr = addr
        self._name = table_map[addr]['name']
        self._size = table_map[addr]['size']
        self._format = table_map[addr]['entries']
        self._data = []
        self._table_map = table_map
    def readFromRom(self, rom, addr=None):
        if addr == None:
            addr = self._addr
        self._data = []
        i = 0
        # TODO better OOB checking
        # Assume that an entry won't reach past the bounds
        while i < self._size:
            row = []
            for entrySpec in self._format:
                entry = self.tableEntryGenerator(entrySpec, self._table_map)
                entry.readFromRom(rom, addr + i)
                i += entry.size()
                row.append(entry)
            self._data.append(row)
    def clear(self, height=0):
        del(self._data)
        self._data = map(lambda x:
                map(lambda y: self.tableEntryGenerator(y, self._table_map),
                    self._format),
                range(height))
    def writeToRom(self, rom, addr=None):
        if addr == None:
            addr = self._addr
        # First check to see if we're gonna go OOB
        dataSize = sum(map(lambda y: sum(map(lambda x: x.size(), y)), self._data))
        if (dataSize <= self._size) or (addr != self._addr):
            i = 0
            for row in self._data:
                for entry in row:
                    entry.writeToRom(rom, addr + i)
                    i += entry.size()
        else:
            raise RuntimeError(self._name + ": Cannot write outside table range")
    def writeToFree(self, rom):
        dataSize = sum(map(lambda y: sum(map(lambda x: x.size(), y)),
            self._data))
        addr = rom.getFreeLoc(dataSize)
        self.writeToRom(rom, addr=addr)
        return addr
    def readFromProject(self, resourceOpener):
        f = resourceOpener(self.name(), 'yml')
        contents = f.read()
        f.close()
        self.load(contents)
    def writeToProject(self, resourceOpener, hiddenColumns=[]):
        f = resourceOpener(self.name(), 'yml')
        f.write(self.dump(hiddenColumns))
        f.close()
    def dump(self, hiddenColumns=[]):
        out = { }
        for i in range(0,len(self._data)):
            outRow = { }
            for j in range(len(self._data[i])):
                entry = self._data[i][j]
                if j not in hiddenColumns:
                    outRow[entry.name] = entry.dump()
            out[i] = outRow
        s = yaml.dump(out, default_flow_style=False)
        # Make hexints output to hex
        # Have to do this regex hack since PyYAML doesn't let us
        for field in filter(
                lambda x: x.has_key('type') and (x['type'] == 'hexint'),
                self._format):
            s = re.sub(field['name'] + ": (\d+)",
                    lambda i: field['name'] + ': ' +
                    hex(int(i.group(0)[i.group(0).find(': ')+2:])) ,s)
        return s
    def load(self, inputRaw):
        input = yaml.load(inputRaw)
        self._data = []
        for i in range(0,len(input)):
            row = []
            for entrySpec in self._format:
                entry = self.tableEntryGenerator(entrySpec, self._table_map)
                try:
                    entry.set(input[i][entry.name])
                except KeyError:
                    # Don't set hidden columns
                    pass
                row.append(entry)
            self._data.append(row)
    # Accessing operators
    def name(self):
        return self._name
    def height(self):
        return len(self._data)
    def width(self):
        return len(self._data[0])
    def __getitem__(self, index):
        (row,col) = index
        return self._data[row][col]
    def __setitem__(self, index, entry):
        (row,col) = index
        self._data[row][col] = entry
