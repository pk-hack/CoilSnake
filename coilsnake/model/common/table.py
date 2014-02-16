import re
import yaml


class IntTableEntry:
    def __init__(self, name, size):
        self.name = name
        self._size = size

    def size(self):
        return self._size

    def readFromRom(self, rom, addr):
        self._data = rom.read_multi(addr, self._size)
        pass

    def writeToRom(self, rom, addr):
        rom.write_multi(addr, self._data, self._size)

    def load(self, data):
        if isinstance(data, str):
            self._data = int(data)
        else:
            self._data = data

    def dump(self):
        return self._data

    def setVal(self, val):
        self._data = val

    def val(self):
        return self._data


class OneBasedIntTableEntry(IntTableEntry):
    def load(self, data):
        if data is None:
            self._data = 0
        else:
            self._data = data + 1

    def dump(self):
        if self._data == 0:
            return None
        else:
            return self._data - 1


class HexIntTableEntry(IntTableEntry):
    def load(self, data):
        if isinstance(data, str):
            self._data = int(data, 16)
        else:
            self._data = data


class ValuedIntTableEntry(IntTableEntry):
    def __init__(self, name, size, values):
        IntTableEntry.__init__(self, name, size)
        self._values = map(lambda x: str(x).lower(), values)

    def load(self, data):
        try:
            self._data = self._values.index(str(data).lower())
        except ValueError:
            if isinstance(data, int):
                self._data = data
            else:
                # TODO Error, no match and not int
                self._data = 0

    def dump(self):
        try:
            return self._values[self._data]
        except IndexError:
            return self._data


class BitFieldTableEntry(IntTableEntry):
    def __init__(self, name, size, values):
        IntTableEntry.__init__(self, name, size)
        values = map(lambda x: str(x).lower(), values)
        self._values = {}
        self._reverseValues = {}
        i = 0
        for value in values:
            self._values[value] = i
            self._reverseValues[i] = value
            i += 1

    def load(self, data):
        if isinstance(data, list):
            self._data = 0
            for bit in data:
                if isinstance(bit, str):
                    bit = bit.lower()
                    if bit in self._values:
                        self._data |= (1 << self._values[bit])
                elif isinstance(bit, int):
                    self._data |= (1 << bit)
        elif isinstance(data, int):
            self._data = data
        else:
            self._data = 0

    def dump(self):
        out = []
        for x in xrange(0, 8 * self._size):
            if self._data & (1 << x):
                if x in self._reverseValues:
                    out.append(self._reverseValues[x])
                else:
                    out.append(x)
        return out


class ByteArrayTableEntry:
    def __init__(self, name, size):
        self.name = name
        self._size = size

    def size(self):
        return self._size

    def readFromRom(self, rom, addr):
        self._data = rom[addr:addr + self._size].to_list()

    def writeToRom(self, rom, addr):
        rom[addr:addr + self._size] = self._data

    def load(self, data):
        self._data = data

    def dump(self):
        return self._data

    def setVal(self, val):
        self._data = val

    def val(self):
        return self._data


class BooleanTableEntry:
    def __init__(self, name):
        self.name = name

    def size(self):
        return 1

    def readFromRom(self, rom, addr):
        self._data = rom.read[addr]

    def writeToRom(self, rom, addr):
        rom[addr] = self._data

    def load(self, data):
        self._data = 1 if data else 0

    def dump(self):
        return self._data != 0

    def setVal(self, val):
        self._data = val

    def val(self):
        return self._data


# For easiness of reading


def _return(x):
    return x


def genericEntryGenerator(spec, table_map):
    if "type" not in spec or spec["type"] == 'int':
        if 'values' in spec:
            return ValuedIntTableEntry(spec["name"], spec["size"],
                                       spec["values"])
        else:
            return IntTableEntry(spec["name"], spec["size"])
    elif spec["type"] == 'hexint':
        return HexIntTableEntry(spec["name"], spec["size"])
    elif spec["type"] == 'bytearray':
        return ByteArrayTableEntry(spec["name"], spec["size"])
    elif spec["type"] == 'boolean':
        return BooleanTableEntry(spec["name"])
    elif spec["type"] == 'one-based int':
        return OneBasedIntTableEntry(spec["name"], spec["size"])
    elif spec["type"] == "bitfield":
        if 'bitvalues' in spec:
            return (
                BitFieldTableEntry(
                    spec["name"],
                    spec["size"],
                    spec["bitvalues"])
            )
        else:
            return BitFieldTableEntry(spec["name"], spec["size"], [])
    else:
        raise RuntimeError("Unknown data entry type " + spec["type"])


class Table:
    tableEntryGenerator = staticmethod(genericEntryGenerator)

    def __init__(self, addr, table_map):
        self._addr = addr
        self._name = table_map[addr]['name'].lower()
        self._size = table_map[addr]['size']
        self._format = table_map[addr]['entries']
        self._data = []
        self._table_map = table_map

    def readFromRom(self, rom, addr=None):
        if addr is None:
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
        del self._data
        self._data = map(lambda x:
                         map(lambda y: self.tableEntryGenerator(y, self._table_map),
                             self._format),
                         range(height))

    def writeToRom(self, rom, addr=None, limitSize=True):
        if addr is None:
            addr = self._addr
        # First check to see if we're gonna go OOB
        dataSize = sum(
            map(lambda y: sum(map(lambda x: x.size(), y)), self._data))
        if (not limitSize) or ((dataSize <= self._size)
                               or (addr != self._addr)):
            i = 0
            for row in self._data:
                for entry in row:
                    entry.writeToRom(rom, addr + i)
                    i += entry.size()
        else:
            raise RuntimeError(
                self._name +
                ": Cannot write outside table range")

    def writeToFree(self, rom):
        dataSize = sum(map(lambda y: sum(map(lambda x: x.size(), y)),
                           self._data))
        addr = rom.allocate(size=dataSize)
        self.writeToRom(rom, addr=addr, limitSize=False)
        return addr

    def readFromProject(self, resourceOpener, name=None):
        if name is None:
            name = self.name()
        f = resourceOpener(name, 'yml')
        contents = f.read()
        f.close()
        self.load(contents)

    def writeToProject(self, resourceOpener, hiddenColumns=None):
        if not hiddenColumns:
            hiddenColumns = []
        f = resourceOpener(self.name(), 'yml')
        f.write(self.dump(hiddenColumns))
        f.close()

    def dump(self, hiddenColumns=None):
        if not hiddenColumns:
            hiddenColumns = []
        out = {}
        for i in range(0, len(self._data)):
            outRow = {}
            for j in range(len(self._data[i])):
                entry = self._data[i][j]
                if j not in hiddenColumns:
                    outRow[entry.name] = entry.dump()
            out[i] = outRow
        s = yaml.dump(out, default_flow_style=False, Dumper=yaml.CSafeDumper)
        # Make hexints output to hex
        # Have to do this regex hack since PyYAML doesn't let us
        for field in filter(
                lambda x: 'type' in x and (x['type'] == 'hexint'),
                self._format):
            s = re.sub(re.escape(field['name']) + ": (\d+)",
                       lambda i: field['name'] + ': ' +
                                 hex(int(i.group(0)[i.group(0).find(': ') + 2:])), s)
        return s

    def load(self, inputRaw):
        input = yaml.load(inputRaw, Loader=yaml.CSafeLoader)
        self._data = []
        for i in range(0, len(input)):
            row = []
            for entrySpec in self._format:
                entry = self.tableEntryGenerator(entrySpec, self._table_map)
                try:
                    entry.load(input[i][entry.name])
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
        (row, col) = index
        return self._data[row][col]

    def __setitem__(self, index, entry):
        (row, col) = index
        self._data[row][col] = entry
