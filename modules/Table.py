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
    def intval(self):
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
            valuesDict = dict((spec['values'][i],i) \
                    for i in range(0,len(spec['values'])))
            loadF = lambda x: valuesDict[x]
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
    def readFromRom(self, rom):
        self._data = []
        i = 0
        # TODO better OOB checking
        # Assume that an entry won't reach past the bounds
        while i < self._size:
            row = []
            for entrySpec in self._format:
                entry = self.tableEntryGenerator(entrySpec, self._table_map)
                entry.readFromRom(rom, self._addr + i)
                i += entry.size()
                row.append(entry)
            self._data.append(row)
    def writeToRom(self, rom):
        # First check to see if we're gonna go OOB
        dataSize = sum(map(lambda y: sum(map(lambda x: x.size(), y)), self._data))
        if dataSize <= self._size:
            i = 0
            for row in self._data:
                for entry in row:
                    entry.writeToRom(rom, self._addr + i)
                    i += entry.size()
        else:
            raise RuntimeError("Cannot write outside table range")
    def dump(self):
        out = { }
        for i in range(0,len(self._data)):
            outRow = { }
            for entry in self._data[i]:
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
                entry.set(input[i][entry.name])
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
