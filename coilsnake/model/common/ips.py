from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.util.common.helper import to_bytes


class IpsPatch(object):
    def __init__(self):
        self.instructions = []
        self.last_offset_used = 0

    def load(self, filename, global_offset=0):
        self.last_offset_used = 0
        try:
            with open(filename, 'rb') as ips:
                ips.seek(0)
                if ips.read(5) != 'PATCH':
                    raise CoilSnakeError("Not an IPS file: " + filename)
                # Read in the records
                while True:
                    offset = ips.read(3)
                    if offset == 'EOF':
                        break
                    offset_int = ord(offset[0]) << 16
                    offset_int |= ord(offset[1]) << 8
                    offset_int |= ord(offset[2])
                    offset_int -= global_offset
                    size = ord(ips.read(1)) << 8
                    size |= ord(ips.read(1))
                    if size == 0:
                        # RLE data
                        rle_size = ord(ips.read(1)) << 8
                        rle_size |= ord(ips.read(1))
                        value = ord(ips.read(1))
                        if offset_int >= 0:
                            # This happens if we're trying to write to before the global_offset.
                            # IE: If the IPS was writing to the header
                            self.instructions.append(("RLE", (offset_int, rle_size, value)))
                            self.last_offset_used = max(self.last_offset_used, offset_int + rle_size - 1)
                    else:
                        # Record data
                        data = map(lambda x: ord(x), list(ips.read(size)))
                        if offset_int >= 0:
                            # This happens if we're trying to write to before the global_offset.
                            # IE: If the IPS was writing to the header
                            self.instructions.append(("RECORD", (offset_int, size, data)))
                            self.last_offset_used = max(self.last_offset_used, offset_int + size - 1)
        except:
            raise CoilSnakeError("Not a valid IPS file: " + filename)

    def apply(self, rom):
        if self.last_offset_used >= rom.size:
            raise CoilSnakeError("Your ROM must be expanded such that it is at least {size} ({size:#x}) bytes long"
                                 .format(size=self.last_offset_used + 1))
        for instruction, args in self.instructions:
            if instruction == 'RLE':
                offset, size, value = args
                for i in range(offset, offset + size):
                    rom[i] = value
            elif instruction == 'RECORD':
                offset, size, data = args
                rom[offset:offset + size] = data

    def is_applied(self, rom):
        if self.last_offset_used >= rom.size:
            return False

        for instruction, args in self.instructions:
            if instruction == 'RLE':
                offset, size, value = args
                for offset in range(offset, offset + size):
                    if rom[offset] != value:
                        return False
            elif instruction == 'RECORD':
                offset, size, data = args
                if rom[offset:offset + size] != data:
                    return False
        return True

    def create(self, clean_rom, hacked_rom, patch_path):
        """Creates an IPS patch from the source and target ROMs."""

        # Create the records.
        i = None
        records = {}
        with open(clean_rom, "rb") as cr, open(hacked_rom, "rb") as hr:
        # do stuff with `cr` and `hr`
            cr.seek(0)
            hr.seek(0)
            s = cr.read(1)
            t = hr.read(1)
            while t:
                if t == s and i is not None:
                    i = None
                elif t != s:
                    if i is not None:
                        # Check that the record's size can fit in 2 bytes.
                        if hr.tell() - 1 - i == 0xFFFF:
                            i = None
                            continue
                        records[i] += t
                    else:
                        i = hr.tell() - 1
                        # Check that the offset isn't EOF. If it is, go back one
                        # byte to work around this IPS limitation.
                        if to_bytes(i, 3) != b"EOF":
                            records[i] = t
                        else:
                            i -= 1
                            records[i] = hacked_rom.getvalue()[i]
                s = cr.read(1)
                t = hr.read(1)

        # Write the patch.
        with open(patch_path, "wb") as pfile:
            pfile.seek(0)
            pfile.write(b"PATCH")
            for r in sorted(records):
                pfile.write(to_bytes(r, 3))
                pfile.write(to_bytes(len(records[r]), 2))
                pfile.write(records[r])
            pfile.write(b"EOF")
            pfile.close()