import os

class Ips:
    def load(self, fname, globalOffset = 0):
        self._instructions = []
        self._lastOffsetUsed = 0
        try:
            with open(fname, 'rb') as ips:
                ips.seek(0)
                if (ips.read(5) != 'PATCH'):
                    raise RuntimeError("Not an IPS file: " + fname)
                # Read in the records
                while True:
                    offset = ips.read(3)
                    if offset == 'EOF':
                        break
                    offsetInt = ord(offset[0])<<16
                    offsetInt |= ord(offset[1])<<8
                    offsetInt |= ord(offset[2])
                    offsetInt -= globalOffset
                    size = ord(ips.read(1)) << 8
                    size |= ord(ips.read(1))
                    if size == 0:
                        # RLE data
                        rleSize = ord(ips.read(1))
                        rleSize |= ord(ips.read(1)) << 8
                        value = ord(ips.read(1))
                        self._instructions.append(
                                ('RLE', (offsetInt, rleSize, value)))

                        self._lastOffsetUsed = max(self._lastOffsetUsed,
                                offsetInt + rleSize - 1)
                    else:
                        # Record data
                        data = map(lambda x: ord(x), list(ips.read(size)))
                        self._instructions.append(
                                ('RECORD', (offsetInt, size, data)))

                        self._lastOffsetUsed = max(self._lastOffsetUsed,
                                offsetInt + size - 1)
        except:
            raise RuntimeError("Not a valid IPS file: " + fname)
    def apply(self, rom):
        if self._lastOffsetUsed >= len(rom):
            raise RuntimeError("Your ROM must be expanded such that it is at" +
                    " least " + str(self._lastOffsetUsed + 1) + " (" +
                    hex(self._lastOffsetUsed + 1) + ") bytes long.")
        for (instr, args) in self._instructions:
            if instr == 'RLE':
                offset, size, value = args
                for offset in range(offset, offset+size):
                    rom[offset] = value
                #print (instr, hex(offset), hex(offset+size), hex(value))
            elif instr == 'RECORD':
                offset, size, data = args
                rom.write(offset, data)
                #print (instr, hex(offset), hex(offset+size), map(hex, data))
    def isApplied(self, rom):
        if self._lastOffsetUsed >= len(rom):
            return False
        for (instr, args) in self._instructions:
            if instr == 'RLE':
                offset, size, value = args
                for offset in range(offset, offset+size):
                    if rom[offset] != value:
                        return False
            elif instr == 'RECORD':
                offset, size, data = args
                if rom[offset:offset+size] != data:
                    return False
        return True
