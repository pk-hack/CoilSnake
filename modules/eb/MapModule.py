import EbModule

class MapModule(EbModule.EbModule):
    _name = "Map"
    _MAP_PTRS_PTR_ADDR = 0xa1db
    _LOCAL_TSET_ADDR = 0x175000
    _MAP_HEIGHT = 256
    _MAP_WIDTH = 320

    _tiles = []

    def __init__(self):
        self._tiles = []
    def readFromRom(self, rom):
        map_ptrs_addr = \
            EbModule.toRegAddr(rom.readMulti(self._MAP_PTRS_PTR_ADDR, 3))
        map_addrs = map(lambda x: \
            EbModule.toRegAddr(rom.readMulti(map_ptrs_addr+x*4,4)), \
            range(8))
        self._tiles = map(lambda y: rom.readList(map_addrs[y%8] + ((y>>3)<<8),
            self._MAP_WIDTH), range(self._MAP_HEIGHT))
        k = self._LOCAL_TSET_ADDR
        for i in range(self._MAP_HEIGHT>>3):
            for j in range(self._MAP_WIDTH):
                self._tiles[i<<3][j] |= (rom[k] & 3) << 8
                self._tiles[(i<<3)|1][j] |= ((rom[k] >> 2) & 3) << 8
                self._tiles[(i<<3)|2][j] |= ((rom[k] >> 4) & 3) << 8
                self._tiles[(i<<3)|3][j] |= ((rom[k] >> 6) & 3) << 8
                self._tiles[(i<<3)|4][j] |= (rom[k+0x3000] & 3) << 8
                self._tiles[(i<<3)|5][j] |= ((rom[k+0x3000] >> 2) & 3) << 8
                self._tiles[(i<<3)|6][j] |= ((rom[k+0x3000] >> 4) & 3) << 8
                self._tiles[(i<<3)|7][j] |= ((rom[k+0x3000] >> 6) & 3) << 8
                k += 1

    def writeToRom(self, rom):
        map_ptrs_addr = \
            EbModule.toRegAddr(rom.readMulti(self._MAP_PTRS_PTR_ADDR, 3))
        map_addrs = map(lambda x: \
            EbModule.toRegAddr(rom.readMulti(map_ptrs_addr+x*4,4)), \
            range(8))
        for i in range(self._MAP_HEIGHT):
            rom.write(map_addrs[i%8] + ((i>>3)<<8), map(lambda x: x & 0xff,
                self._tiles[i]))
        k = self._LOCAL_TSET_ADDR
        for i in range(self._MAP_HEIGHT>>3):
            for j in range(self._MAP_WIDTH):
                c = ((self._tiles[i<<3][j] >> 8)
                        | ((self._tiles[(i<<3)|1][j] >> 8) << 2)
                        | ((self._tiles[(i<<3)|2][j] >> 8) << 4)
                        | ((self._tiles[(i<<3)|3][j] >> 8) << 6))
                rom.write(k, c)
                c = ((self._tiles[(i<<3)|4][j] >> 8)
                        | ((self._tiles[(i<<3)|5][j] >> 8) << 2)
                        | ((self._tiles[(i<<3)|6][j] >> 8) << 4)
                        | ((self._tiles[(i<<3)|7][j] >> 8) << 6))
                rom.write(k+0x3000, c)
                k += 1
        rom[0] = 0x69
