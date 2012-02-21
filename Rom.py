import array
import os
import yaml

class Rom:
    _data = array.array('B')
    _type = "Unknown"
    _type_map = { }
    def __init__(self):
        self._data = array.array('B')
        self._type = "Unknown"
        self._type_map = { }
    def __init__(self,romtypeFname):
        self._data = array.array('B')
        self._type = "Unknown"
        self._type_map = { }
        self.loadRomTypes(romtypeFname)
    def loadRomTypes(self, fname):
        with open(fname, 'r') as f:
            self._type_map = yaml.load(f)
    def checkRomType(self):
        for t, d in self._type_map.iteritems():
            offset, data = d['offset'], d['data']
            if self[offset:offset+len(data)] == data:
                return (t, False)
            # Check for a headered ROM
            elif self[offset+0x200:offset+0x200+len(data)] == data:
                return (t, True)
        else:
            return ("Unknown", False)
    def load(self, f):
        if type(f) == str:
            f = fopen(f,'rb')
        if (len(self._data)) > 0:
            print "WOAH ALREADY LOADED"
        else:
            print "ok"
        size = os.path.getsize(f.name)
        self._data.fromfile(f, size)
        f.close()
        self._type, has_header = self.checkRomType()
        # Trim headered ROM
        if has_header:
            self._data = self._data[0x200:]
    def save(self, fname):
        with open(fname, 'wb') as f:
            self._data.tofile(f)
    def type(self):
        return _type
    # Reading methods
    def read(self, i):
        return self._data[i]
    def read(self, i, len):
        return self._data[i:i+len]
    def readMulti(self, i, len):
        # Note: reads in reverse endian
        d = self[i:i+len]
        d.reverse()
        return reduce(lambda x,y: (x<<4)|y, d)
    def __getitem__(self, key):
        if (type(key) == slice):
            return self._data[key].tolist()
        else:
            return self._data[key]
    # Writing methods
    def write(self, i, data):
        if (type(data) == list):
            self[i:i+len(data)] = data
        elif (type(data) == int):
            self[i] = data
    def __setitem__(self, key, item):
        if (type(key) == slice):
            self._data[key] = array.array('B',item)
        else:
            self._data[key] = item
    def __len__(self):
        return len(self._data)
