import array
import os


class DataBlock:
    def __init__(self):
        self.data = array.array('B')
        self.size = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self._data

    def from_file(self, filename):
        self.size = int(os.path.getsize(filename))
        with open(filename, 'rb') as f:
            self.data.fromfile(f, self.size)

    def to_file(self, filename):
        with open(filename, 'wb') as f:
            self.data.tofile(f)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, item):
        if isinstance(key, slice):
            self.data[key] = array.array('B', item)
        else:
            self.data[key] = item

    def __len__(self):
        return self.size

    def __eq__(self, other):
        return (isinstance(other, type(self))) and (self.data == other.data)

    def __ne__(self, other):
        return not (self == other)