import yaml

from coilsnake.modules.eb import EbModule
from coilsnake.modules.eb.EbTablesModule import EbTable
from coilsnake.model.common.table import ValuedIntTableEntry
from coilsnake.Progress import updateProgress


class MapModule(EbModule.EbModule):
    NAME = "Map"
    _MAP_PTRS_PTR_ADDR = 0xa1db
    _LOCAL_TSET_ADDR = 0x175000
    _MAP_HEIGHT = 320
    _MAP_WIDTH = 256

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._tiles = []
        self._mapSecTsetPalsTbl = EbTable(0xD7A800)
        self._mapSecMusicTbl = EbTable(0xDCD637)
        self._mapSecMiscTbl = EbTable(0xD7B200)
        self._mapSecTownMapTbl = EbTable(0xEFA70F)
        self.teleport = ValuedIntTableEntry(None, None,
                                            ["Enabled", "Disabled"])
        self.townmap = ValuedIntTableEntry(None, None,
                                           ["None", "Onett", "Twoson", "Threed", "Fourside", "Scaraba",
                                            "Summers", "None 2"])
        self.setting = ValuedIntTableEntry(None, None,
                                           ["None", "Indoors", "Exit Mouse usable",
                                            "Lost Underworld sprites", "Magicant sprites", "Robot sprites",
                                            "Butterflies", "Indoors and Butterflies"])
        self.townmap_image = ValuedIntTableEntry(None, None,
                                                 ["None", "Onett", "Twoson", "Threed", "Fourside", "Scaraba",
                                                  "Summers"])
        self.townmap_arrow = ValuedIntTableEntry(None, None,
                                                 ["None", "Up", "Down", "Right", "Left"])

    def read_from_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        # Read map tiles
        map_ptrs_addr = \
            EbModule.toRegAddr(rom.read_multi(self._MAP_PTRS_PTR_ADDR, 3))
        map_addrs = map(lambda x:
                        EbModule.toRegAddr(
                            rom.read_multi(map_ptrs_addr + x * 4, 4)),
                        range(8))

        def read_row_data(row_number):
            offset = map_addrs[row_number % 8] + ((row_number >> 3) << 8)
            return rom[offset:offset + self._MAP_WIDTH].to_list()

        self._tiles = map(read_row_data, range(self._MAP_HEIGHT))
        k = self._LOCAL_TSET_ADDR
        for i in range(self._MAP_HEIGHT >> 3):
            for j in range(self._MAP_WIDTH):
                self._tiles[i << 3][j] |= (rom[k] & 3) << 8
                self._tiles[(i << 3) | 1][j] |= ((rom[k] >> 2) & 3) << 8
                self._tiles[(i << 3) | 2][j] |= ((rom[k] >> 4) & 3) << 8
                self._tiles[(i << 3) | 3][j] |= ((rom[k] >> 6) & 3) << 8
                self._tiles[(i << 3) | 4][j] |= (rom[k + 0x3000] & 3) << 8
                self._tiles[(i << 3) | 5][j] |= ((rom[k + 0x3000] >> 2) & 3) << 8
                self._tiles[(i << 3) | 6][j] |= ((rom[k + 0x3000] >> 4) & 3) << 8
                self._tiles[(i << 3) | 7][j] |= ((rom[k + 0x3000] >> 6) & 3) << 8
                k += 1
        updateProgress(25)
        # Read sector data
        self._mapSecTsetPalsTbl.readFromRom(rom)
        updateProgress(25.0 / 4)
        self._mapSecMusicTbl.readFromRom(rom)
        updateProgress(25.0 / 4)
        self._mapSecMiscTbl.readFromRom(rom)
        updateProgress(25.0 / 4)
        self._mapSecTownMapTbl.readFromRom(rom)
        updateProgress(25.0 / 4)

    def write_to_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        map_ptrs_addr = \
            EbModule.toRegAddr(rom.read_multi(self._MAP_PTRS_PTR_ADDR, 3))
        map_addrs = map(lambda x:
                        EbModule.toRegAddr(
                            rom.read_multi(map_ptrs_addr + x * 4, 4)),
                        range(8))
        for i in range(self._MAP_HEIGHT):
            offset = map_addrs[i % 8] + ((i >> 3) << 8)
            rom[offset:offset + self._MAP_WIDTH] = map(lambda x: x & 0xff, self._tiles[i])
        k = self._LOCAL_TSET_ADDR
        for i in range(self._MAP_HEIGHT >> 3):
            for j in range(self._MAP_WIDTH):
                c = ((self._tiles[i << 3][j] >> 8)
                     | ((self._tiles[(i << 3) | 1][j] >> 8) << 2)
                     | ((self._tiles[(i << 3) | 2][j] >> 8) << 4)
                     | ((self._tiles[(i << 3) | 3][j] >> 8) << 6))
                rom[k] = c
                c = ((self._tiles[(i << 3) | 4][j] >> 8)
                     | ((self._tiles[(i << 3) | 5][j] >> 8) << 2)
                     | ((self._tiles[(i << 3) | 6][j] >> 8) << 4)
                     | ((self._tiles[(i << 3) | 7][j] >> 8) << 6))
                rom[k + 0x3000] = c
                k += 1
        updateProgress(25)
        # Write sector data
        self._mapSecTsetPalsTbl.writeToRom(rom)
        updateProgress(25.0 / 4)
        self._mapSecMusicTbl.writeToRom(rom)
        updateProgress(25.0 / 4)
        self._mapSecMiscTbl.writeToRom(rom)
        updateProgress(25.0 / 4)
        self._mapSecTownMapTbl.writeToRom(rom)
        updateProgress(25.0 / 4)

    def write_to_project(self, resourceOpener):
        # Write map tiles
        with resourceOpener("map_tiles", "map") as f:
            for row in self._tiles:
                f.write(hex(row[0])[2:].zfill(3))
                for tile in row[1:]:
                    f.write(" ")
                    f.write(hex(tile)[2:].zfill(3))
                f.write("\n")
        updateProgress(25.0)
        # Write sector data
        out = dict()
        for i in range(self._mapSecTsetPalsTbl.height()):
            self.teleport.setVal(self._mapSecMiscTbl[i, 0].val() >> 7)
            self.townmap.setVal((self._mapSecMiscTbl[i, 0].val() >> 3) & 7)
            self.setting.setVal(self._mapSecMiscTbl[i, 0].val() & 7)
            self.townmap_image.setVal(self._mapSecTownMapTbl[i, 0].val() & 0xf)
            self.townmap_arrow.setVal(self._mapSecTownMapTbl[i, 0].val() >> 4)
            out[i] = {
                "Tileset": self._mapSecTsetPalsTbl[i, 0].val() >> 3,
                "Palette": self._mapSecTsetPalsTbl[i, 0].val() & 7,
                "Music": self._mapSecMusicTbl[i, 0].dump(),
                "Teleport": self.teleport.dump(),
                "Town Map": self.townmap.dump(),
                "Setting": self.setting.dump(),
                "Item": self._mapSecMiscTbl[i, 1].dump(),
                "Town Map Image": self.townmap_image.dump(),
                "Town Map Arrow": self.townmap_arrow.dump(),
                "Town Map X": self._mapSecTownMapTbl[i, 1].dump(),
                "Town Map Y": self._mapSecTownMapTbl[i, 2].dump()}
        updateProgress(12.5)
        with resourceOpener("map_sectors", "yml") as f:
            yaml.dump(
                out,
                f,
                Dumper=yaml.CSafeDumper,
                default_flow_style=False)
        updateProgress(12.5)

    def read_from_project(self, resourceOpener):
        # Read map data
        with resourceOpener("map_tiles", "map") as f:
            self._tiles = map(lambda y:
                              map(lambda x: int(x, 16), y.split(" ")),
                              f.readlines())
        updateProgress(25)
        # Read sector data
        self._mapSecTsetPalsTbl.clear(2560)
        self._mapSecMusicTbl.clear(2560)
        self._mapSecMiscTbl.clear(2560)
        self._mapSecTownMapTbl.clear(2560)
        pct = (25.0 / 2560)
        with resourceOpener("map_sectors", "yml") as f:
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            for i in input:
                entry = input[i]
                self._mapSecTsetPalsTbl[i, 0].setVal(
                    (entry["Tileset"] << 3) | entry["Palette"])
                self._mapSecMusicTbl[i, 0].load(entry["Music"])
                self._mapSecMiscTbl[i, 1].load(entry["Item"])
                self.teleport.load(entry["Teleport"])
                self.townmap.load(entry["Town Map"])
                self.setting.load(entry["Setting"])
                self._mapSecMiscTbl[i, 0].setVal((self.teleport.val() << 7)
                                                 | (self.townmap.val() << 3) | self.setting.val())
                self.townmap_image.load(entry["Town Map Image"])
                self.townmap_arrow.load(entry["Town Map Arrow"])
                self._mapSecTownMapTbl[i, 0].setVal(
                    (self.townmap_arrow.val() << 4) |
                    (self.townmap_image.val() & 0xf))
                self._mapSecTownMapTbl[i, 1].load(entry["Town Map X"])
                self._mapSecTownMapTbl[i, 2].load(entry["Town Map Y"])
                updateProgress(pct)

    def upgrade_project(self, oldVersion, newVersion, rom, resourceOpenerR,
                        resourceOpenerW, resourceDeleter):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        global updateProgress

        def replaceField(fname, oldField, newField, valueMap):
            if newField is None:
                newField = oldField
            valueMap = dict((k, v) for k, v in valueMap.iteritems())
            with resourceOpenerR(fname, 'yml') as f:
                data = yaml.load(f, Loader=yaml.CSafeLoader)
                for i in data:
                    if data[i][oldField] in valueMap:
                        data[i][newField] = valueMap[data[i][oldField]].lower()
                    else:
                        data[i][newField] = data[i][oldField]
                    if newField != oldField:
                        del data[i][oldField]
            with resourceOpenerW(fname, 'yml') as f:
                yaml.dump(data, f, Dumper=yaml.CSafeDumper,
                          default_flow_style=False)

        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion <= 2:
            replaceField("map_sectors", "Town Map", None,
                         {"scummers": "summers"})

            # Need to add the Town Map Image/Arrow/X/Y fields
            tmp = updateProgress
            updateProgress = lambda x: None
            self.read_from_rom(rom)
            updateProgress = tmp

            with resourceOpenerR("map_sectors", 'yml') as f:
                data = yaml.load(f, Loader=yaml.CSafeLoader)
                for i in data:
                    self.townmap_image.setVal(
                        self._mapSecTownMapTbl[i, 0].val() & 0xf)
                    self.townmap_arrow.setVal(
                        self._mapSecTownMapTbl[i, 0].val() >> 4)
                    data[i]["Town Map Image"] = self.townmap_image.dump()
                    data[i]["Town Map Arrow"] = self.townmap_arrow.dump()
                    data[i]["Town Map X"] = self._mapSecTownMapTbl[i, 1].dump()
                    data[i]["Town Map Y"] = self._mapSecTownMapTbl[i, 2].dump()
            with resourceOpenerW("map_sectors", 'yml') as f:
                yaml.dump(data, f, Dumper=yaml.CSafeDumper,
                          default_flow_style=False)

            self.upgrade_project(3, newVersion, rom, resourceOpenerR,
                                 resourceOpenerW, resourceDeleter)
        else:
            self.upgrade_project(
                oldVersion + 1, newVersion, rom, resourceOpenerR,
                resourceOpenerW, resourceDeleter)
