import json

from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.model.common.ips import IpsPatch


class EbpPatch(object):

    def __init__(self):

        self.patch = IpsPatch()
        self.metadata = None

    @property
    def last_offset_used(self):

        return self.patch.last_offset_used
    
    def load(self, filename):

        try:
            self.patch.load(filename)

            with open(filename, 'rb') as ebp:
                # Skip to the end of the IPS part of the patch
                ebp.seek(
                    5 + sum([3+2+i[1][1]+(2 if i[0] == 'RLE' else 0) for i in self.patch.instructions]) + 3
                )

                # Load the metadata, if available
                try:
                    self.metadata = json.loads(ebp.read().decode("utf-8"))
                except ValueError:
                    self.metadata = None
        except:
            raise CoilSnakeError("Not a valid EBP file: " + filename)

    def apply(self, rom):

        self.patch.apply(rom)

    def is_applied(self, rom):

        return self.patch.is_applied(rom)

    def create(self, clean_rom, hacked_rom, patch_path, metadata):

        self.patch.create(clean_rom, hacked_rom, patch_path)
        
        with open(patch_path, "ab") as pfile:
            pfile.write(bytes(metadata, 'utf8'))
            pfile.close()