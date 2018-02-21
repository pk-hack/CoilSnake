from array import array

from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.model.common.blocks import Rom
from io import BytesIO
import os


class IpsPatch(object):
    def __init__(self):
        self.instructions = []
        self.last_offset_used = 0

    def load(self, filename, global_offset=0):
        self.last_offset_used = 0
        try:
            with open(filename, 'rb') as ips:
                ips.seek(0)
                if ips.read(5) != b'PATCH':
                    raise CoilSnakeError("Not an IPS file: " + filename)
                # Read in the records
                while True:
                    offset = ips.read(3)
                    if offset == b'EOF':
                        break
                    offset_int = offset[0] << 16
                    offset_int |= offset[1] << 8
                    offset_int |= offset[2]
                    offset_int -= global_offset
                    size = ips.read(1)[0] << 8
                    size |= ips.read(1)[0]
                    if size == 0:
                        # RLE data
                        rle_size = ips.read(1)[0] << 8
                        rle_size |= ips.read(1)[0]
                        value = ips.read(1)[0]
                        if offset_int >= 0:
                            # This happens if we're trying to write to before the global_offset.
                            # IE: If the IPS was writing to the header
                            self.instructions.append((b"RLE", (offset_int, rle_size, value)))
                            self.last_offset_used = max(self.last_offset_used, offset_int + rle_size - 1)
                    else:
                        # Record data
                        data = array('B', ips.read(size))

                        if offset_int >= 0:
                            # This happens if we're trying to write to before the global_offset.
                            # IE: If the IPS was writing to the header
                            self.instructions.append((b"RECORD", (offset_int, size, data)))
                            self.last_offset_used = max(self.last_offset_used, offset_int + size - 1)
        except Exception as e:
            raise CoilSnakeError("Not a valid IPS file: " + filename) from e

    def apply(self, rom):
        if self.last_offset_used >= rom.size:
            raise CoilSnakeError("Your ROM must be expanded such that it is at least {size} ({size:#x}) bytes long"
                                 .format(size=self.last_offset_used + 1))
        for instruction, args in self.instructions:
            if instruction == b'RLE':
                offset, size, value = args
                for i in range(offset, offset + size):
                    rom[i] = value
            elif instruction == b'RECORD':
                offset, size, data = args
                rom[offset:offset + size] = data

    def is_applied(self, rom):
        if self.last_offset_used >= rom.size:
            return False

        for instruction, args in self.instructions:
            if instruction == b'RLE':
                offset, size, value = args
                for offset in range(offset, offset + size):
                    if rom[offset] != value:
                        return False
            elif instruction == b'RECORD':
                offset, size, data = args
                if rom[offset:offset + size].to_array() != data:
                    return False
        return True

    def create(self, clean_rom, hacked_rom, patch_path):
        """Creates an IPS patch from the source and target ROMs."""

        with Rom() as cr, Rom() as hr:
            cr.from_file(clean_rom)
            hr.from_file(hacked_rom)
            
            if cr.__len__() > hr.__len__():
                if hr.__len__() <= 0x400000 and hr.__len__() > 0x300000:
                    raise CoilSnakeError("Clean ROM greater in size than hacked ROM. Please use a 3 Megabyte or 4 Megabyte clean ROM.")
                if hr.__len__() <= 0x300000:
                    raise CoilSnakeError("Clean ROM greater in size than hacked ROM. Please use a 3 Megabyte clean ROM.")
            
            # Expand clean ROM as necessary.
            if cr.__len__() < hr.__len__():
                if hr.__len__() == 0x400000:
                    cr.expand(0x400000)
                elif hr.__len__() == 0x600000:
                    cr.expand(0x600000)
                else:
                    cr.expand(patch.last_offset_used)
            
            # Create the records.
            i = None
            records = {}
            index = 0
            # Get the first byte of each ROM so that the loop works correctly.
            s = cr.__getitem__(index).to_bytes(1, byteorder='big')
            t = hr.__getitem__(index).to_bytes(1, byteorder='big')
            index += 1
            while index <= cr.__len__() and index <= hr.__len__():
                if t == s and i is not None:
                    i = None
                elif t != s:
                    if i is not None:
                        # Check that the record's size can fit in 2 bytes.
                        if index - 1 - i == 0xFFFF:
                            i = None
                            continue
                        records[i] += t
                    else:
                        i = index - 1
                        # Check that the offset isn't EOF. If it is, go back one
                        # byte to work around this IPS limitation.
                        if i.to_bytes(3, byteorder='big') != b"EOF":
                            records[i] = t
                        else:
                            i -= 1
                            records[i] = hr.to_list()[i]
                if index < cr.__len__() and index < hr.__len__():
                    s = cr.__getitem__(index).to_bytes(1, byteorder='big')
                    t = hr.__getitem__(index).to_bytes(1, byteorder='big')
                index += 1

        # Write the patch.
        with open(patch_path, "wb") as pfile:
            pfile.seek(0)
            pfile.write(b"PATCH")
            for r in sorted(records):
                pfile.write(r.to_bytes(3, byteorder='big'))
                pfile.write(len(records[r]).to_bytes(2, byteorder='big'))
                pfile.write(records[r])
            pfile.write(b"EOF")
            pfile.close()