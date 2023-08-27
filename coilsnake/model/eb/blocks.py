import hashlib
import os

from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.model.common.blocks import Block, Rom, ROM_TYPE_NAME_EARTHBOUND
from coilsnake.model.common.ips import IpsPatch
from coilsnake.modules.eb.EbModule import comp, decomp
from coilsnake.exceptions.eb.exceptions import InvalidEbCompressedDataError
from coilsnake.root import ASSET_PATH


class EbCompressibleBlock(Block):
    def from_compressed_block(self, block, offset=0):
        self.data = decomp(block, offset)
        if self.data[0] < 0:
            raise InvalidEbCompressedDataError("Couldn't decompress invalid data")
        self.size = len(self.data)

    def compress(self):
        compressed_data = comp(self.to_list())
        self.from_list(compressed_data)


class EbRom(Rom):

    # The MD5 hash for the reference EB ROM (clean, unheadered, unexpanded).
    REFERENCE_MD5 = "a864b2e5c141d2dec1c4cbed75a42a85"

    # The MD5 hashes for the alternative EB ROMs and the associated patches for
    # turning them into the reference ROMs.
    ALT_MD5 = {
        "8c28ce81c7d359cf9ccaa00d41f8ad33": "fix1.ips",
        "b2dcafd3252cc4697bf4b89ea3358cd5": "fix2.ips",
        "0b8c04fc0182e380ff0e3fe8fdd3b183": "fix3.ips",
        "2225f8a979296b7dcccdda17b6a4f575": "fix4.ips",
        "eb83b9b6ea5692cefe06e54ea3ec9394": "fix5.ips",
        "cc9fa297e7bf9af21f7f179e657f1aa1": "fix6.ips"
    }

    def _setup_rom_post_load(self):
        super(EbRom, self)._setup_rom_post_load()
        self._clean()

    def _clean(self):
        """If this is a clean version of one of the variants of the
        EarthBound ROM, patch it so that it becomes a clean version of
        the reference ROM.
        """

        # Truncate the ROM if it is has been expanded
        if len(self) > 0x300000:
            # Change the ExHiROM bytes in case this is an ExHiROM
            self[0x00ffd5] = 0x31
            self[0x00ffd7] = 0x0c

            # Truncate the data
            self.size = 0x300000
            self.data = self.data[:0x300000]

        # Ensure the ROM isn't too small
        elif len(self) < 0x300000:
            raise CoilSnakeError("Not a valid clean EarthBound ROM.")

        # Check if this ROM is already a reference ROM
        hash = self._calc_hash()
        if hash == self.REFERENCE_MD5:
            return

        # Try to fix the ROM with a patch if it is one of the known alternatives
        try:
            patch_filename = self.ALT_MD5[hash]
        except KeyError:
            pass  # Unknown variant
        else:
            patch = IpsPatch()
            patch.load(os.path.join(ASSET_PATH, "rom-fixes", ROM_TYPE_NAME_EARTHBOUND, patch_filename))
            patch.apply(self)
            self._setup_rom_post_load()
            return

        # As a last attempt, try to set the last byte to 0x0, since LunarIPS
        # likes to add 0xff at the end
        self[-1] = 0x0
        if self._calc_hash() == self.REFERENCE_MD5:
            return

        raise CoilSnakeError("Not a valid clean EarthBound ROM.")

    def _calc_hash(self):
        """Calculates the MD5 hash of this ROM's data.
        """

        return hashlib.md5(self.data.tobytes()).hexdigest()