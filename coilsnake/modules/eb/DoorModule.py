import yaml
from re import sub

from coilsnake.modules.eb.EbTablesModule import EbTable, PointerTableEntry
from coilsnake.modules.eb.EbDataBlocks import DataBlock
from coilsnake.modules.Table import ValuedIntTableEntry
from coilsnake.Progress import updateProgress
from coilsnake.modules.eb import EbModule


class Door:
    TYPE_NAMES = ["switch", "rope/ladder", "door", "escalator", "stairway", "object", "person"]
    STAIR_DIRECTION_NAMES = ["NW", "NE", "SW", "SE", "Nowhere"]
    DESTINATION_DIRECTION_NAMES = ["Down", "Up", "Right", "Left"]

    def readFromRom(self, rom, addr):
        self._y = rom[addr]
        self._x = rom[addr + 1]
        self._type = rom[addr + 2]
        ptr = rom.readMulti(addr + 3, 2)
        if self._type == 1:  # Rope/Ladder
            self._isRope = (ptr == 0x8000)
        elif (self._type == 3) or (self._type == 4):  # Escalator and Stairs
            if ptr == 0x8000:
                stairDir = 4
            else:
                stairDir = ptr / 0x100
            self._stairDir = ValuedIntTableEntry(None, None, self.STAIR_DIRECTION_NAMES)
            self._stairDir.setVal(stairDir)
        elif self._type == 2:  # Door
            ptr |= 0xF0000
            self._destTextPtr = PointerTableEntry(None, 4)
            self._destTextPtr.setVal(rom.readMulti(ptr, 4))
            if ((self._destTextPtr.val() != 0) and
                    ((self._destTextPtr.val() < 0xc00000)
                     or (self._destTextPtr.val() > 0xffffff))):
                raise ValueError("Invalid Door")
            self._destFlag = rom.readMulti(ptr + 4, 2)
            self._destY = rom[ptr + 6]
            self._destY |= (rom[ptr + 7] & 0x3f) << 8
            self._destDir = ValuedIntTableEntry(None, None, self.DESTINATION_DIRECTION_NAMES)
            self._destDir.setVal((rom[ptr + 7] & 0xc0) >> 6)
            self._destX = rom.readMulti(ptr + 8, 2)
            self._destStyle = rom[ptr + 10]
        elif self._type == 0:  # Switch
            ptr |= 0xF0000
            self._destFlag = rom.readMulti(ptr, 2)
            self._destTextPtr = PointerTableEntry(None, 4)
            self._destTextPtr.setVal(rom.readMulti(ptr + 2, 4))
            if ((self._destTextPtr.val() != 0) and
                    ((self._destTextPtr.val() < 0xc00000) or (self._destTextPtr.val() > 0xffffff))):
                raise ValueError("Invalid Switch")
        elif (self._type == 5) or (self._type == 6):  # Object and Person
            ptr |= 0xF0000
            self._destTextPtr = PointerTableEntry(None, 4)
            self._destTextPtr.setVal(rom.readMulti(ptr, 4))
        else:
            raise ValueError("Unknown type " + str(self._type))

    def getTypeAsString(self):
        if self._type == 1:
            if self._isRope:
                return "rope"
            else:
                return "ladder"
        else:
            return Door.TYPE_NAMES[self._type]

    def setTypeFromString(self, typeStr):
        typeStr = typeStr.lower()
        if typeStr == "rope":
            self._type = 1
            self._isRope = True
        elif typeStr == "ladder":
            self._type = 1
            self._isRope = False
        else:
            self._type = Door.TYPE_NAMES.index(typeStr)

    def dump(self):
        out = {"X": self._x,
               "Y": self._y,
               "Type": self.getTypeAsString()}
        if (self._type == 3) or (self._type == 4):  # Stairs/Escalator
            out["Direction"] = self._stairDir.dump()
        elif self._type == 2:  # Door
            out["Text Pointer"] = self._destTextPtr.dump()
            out["Event Flag"] = self._destFlag
            out["Destination X"] = self._destX
            out["Destination Y"] = self._destY
            out["Direction"] = self._destDir.dump()
            out["Style"] = self._destStyle
        elif self._type == 0:  # Switch
            out["Text Pointer"] = self._destTextPtr.dump()
            out["Event Flag"] = self._destFlag
        elif (self._type == 5) or (self._type == 6):
            out["Text Pointer"] = self._destTextPtr.dump()
        return out

    def load(self, input):
        self._x = input["X"]
        self._y = input["Y"]
        self.setTypeFromString(input["Type"])
        if (self._type == 3) or (self._type == 4):  # Stairs/Escalator
            self._stairDir = ValuedIntTableEntry(None, None,
                                                 ["NW", "NE", "SW", "SE", "Nowhere"])
            self._stairDir.load(input["Direction"])
        elif self._type == 2:  # Door
            self._destTextPtr = PointerTableEntry(None, 4)
            self._destTextPtr.load(input["Text Pointer"])
            self._destFlag = input["Event Flag"]
            self._destX = input["Destination X"]
            self._destY = input["Destination Y"]
            self._destDir = ValuedIntTableEntry(None, None,
                                                ["Down", "Up", "Right", "Left"])
            self._destDir.load(input["Direction"])
            self._destStyle = input["Style"]
        elif self._type == 0:  # Switch
            self._destTextPtr = PointerTableEntry(None, 4)
            self._destTextPtr.load(input["Text Pointer"])
            self._destFlag = input["Event Flag"]
        elif (self._type == 5) or (self._type == 6):
            self._destTextPtr = PointerTableEntry(None, 4)
            self._destTextPtr.load(input["Text Pointer"])

    def writeToRom(self, rom, addr, destWriteLoc, destRangeEnd, destLocs):
        rom[addr] = self._y
        rom[addr + 1] = self._x
        rom[addr + 2] = self._type
        if self._type == 1:  # Rope/Ladder
            rom[addr + 3] = 0
            rom[addr + 4] = (0x80 if self._isRope else 0)
            return 0
        elif (self._type == 3) or (self._type == 4):  # Escalator and Stairs
            rom[addr + 3] = 0
            rom[addr + 4] = (0x80 if (self._stairDir.val() == 4) else
                             self._stairDir.val())
            return 0
        elif self._type == 2:  # Door
            with DataBlock(11) as destBlock:
                # Write data to block
                destTextPtr = self._destTextPtr.val()
                destBlock[0] = destTextPtr & 0xff
                destBlock[1] = (destTextPtr >> 8) & 0xff
                destBlock[2] = (destTextPtr >> 16) & 0xff
                destBlock[3] = (destTextPtr >> 24) & 0xff
                destBlock[4] = self._destFlag & 0xff
                destBlock[5] = (self._destFlag >> 8) & 0xff
                destBlock[6] = self._destY & 0xff
                destBlock[7] = (self._destY >> 8) | (self._destDir.val() << 6)
                destBlock[8] = self._destX & 0xff
                destBlock[9] = self._destX >> 8
                destBlock[10] = self._destStyle
                # Check for any pre-existing matching destinations
                destHash = destBlock.hash()
                try:
                    destAddr = destLocs[destHash]
                    rom[addr + 3] = destAddr & 0xff
                    rom[addr + 4] = destAddr >> 8
                    return 0
                except KeyError:
                    # Need to write a new destination
                    if (destWriteLoc + 11) > destRangeEnd:
                        # TODO Error, not enough space
                        raise RuntimeError("Not enough door destination space")
                    destBlock.writeToRom(rom, destWriteLoc)
                    destLocs[destHash] = destWriteLoc & 0xffff
                    rom[addr + 3] = destWriteLoc & 0xff
                    rom[addr + 4] = (destWriteLoc >> 8) & 0xff
                    return 11
        elif self._type == 0:  # Switch
            with DataBlock(6) as destBlock:
                # Write the data to block
                destBlock[0] = self._destFlag & 0xff
                destBlock[1] = self._destFlag >> 8
                destTextPtr = self._destTextPtr.val()
                destBlock[2] = destTextPtr & 0xff
                destBlock[3] = (destTextPtr >> 8) & 0xff
                destBlock[4] = (destTextPtr >> 16) & 0xff
                destBlock[5] = (destTextPtr >> 24) & 0xff
                # Check for any pre-existing matching destinations
                destHash = destBlock.hash()
                try:
                    destAddr = destLocs[destHash]
                    rom[addr + 3] = destAddr & 0xff
                    rom[addr + 4] = destAddr >> 8
                    return 0
                except KeyError:
                    # Need to write a new destination
                    if (destWriteLoc + 6) > destRangeEnd:
                        # TODO Error, not enough space
                        raise RuntimeError("Not enough door destination space")
                    destBlock.writeToRom(rom, destWriteLoc)
                    destLocs[destHash] = destWriteLoc & 0xffff
                    rom[addr + 3] = destWriteLoc & 0xff
                    rom[addr + 4] = (destWriteLoc >> 8) & 0xff
                    return 6
        elif (self._type == 5) or (self._type == 6):  # Switch
            with DataBlock(4) as destBlock:
                # Write the data to block
                destTextPtr = self._destTextPtr.val()
                destBlock[0] = destTextPtr & 0xff
                destBlock[1] = (destTextPtr >> 8) & 0xff
                destBlock[2] = (destTextPtr >> 16) & 0xff
                destBlock[3] = (destTextPtr >> 24) & 0xff
                # Check for any pre-existing matching destinations
                destHash = destBlock.hash()
                try:
                    destAddr = destLocs[destHash]
                    rom[addr + 3] = destAddr & 0xff
                    rom[addr + 4] = destAddr >> 8
                    return 0
                except KeyError:
                    # Need to write a new destination
                    if (destWriteLoc + 4) > destRangeEnd:
                        # TODO Error, not enough space
                        raise RuntimeError("Not enough door destination space")
                    destBlock.writeToRom(rom, destWriteLoc)
                    destLocs[destHash] = destWriteLoc & 0xffff
                    rom[addr + 3] = destWriteLoc & 0xff
                    rom[addr + 4] = (destWriteLoc >> 8) & 0xff
                    return 4


class DoorModule(EbModule.EbModule):
    NAME = "Doors"

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._ptrTbl = EbTable(0xD00000)
        self._entries = []

    def read_from_rom(self, rom):
        self._ptrTbl.readFromRom(rom)
        updateProgress(5)
        pct = 45.0 / (40 * 32)
        for i in range(self._ptrTbl.height()):
            loc = EbModule.toRegAddr(self._ptrTbl[i, 0].val())
            entry = []
            numDoors = rom.readMulti(loc, 2)
            loc += 2
            for j in range(numDoors):
                d = Door()
                try:
                    d.readFromRom(rom, loc)
                except ValueError:
                    # Invalid door entry. Some entries in EB are invalid.
                    # When we encounter one, just assume we've reached the end of this entry.
                    break
                entry.append(d)
                loc += 5
            self._entries.append(entry)
            i += 1
            updateProgress(pct)

    def write_to_project(self, resourceOpener):
        out = dict()
        x = y = 0
        rowOut = dict()
        pct = 45.0 / (40 * 32)
        for entry in self._entries:
            if not entry:
                rowOut[x % 32] = None
            else:
                rowOut[x % 32] = map(lambda z: z.dump(), entry)
            if (x % 32) == 31:
                # Start new row
                out[y] = rowOut
                x = 0
                y += 1
                rowOut = dict()
            else:
                x += 1
            updateProgress(pct)
        with resourceOpener("map_doors", "yml") as f:
            s = yaml.dump(
                out,
                default_flow_style=False,
                Dumper=yaml.CSafeDumper)
            s = sub("Event Flag: (\d+)", lambda i: "Event Flag: " + hex(int(i.group(0)[12:])), s)
            f.write(s)
        updateProgress(5)

    def read_from_project(self, resourceOpener):
        self._entries = []
        pct = 45.0 / (40 * 32)
        with resourceOpener("map_doors", "yml") as f:
            updateProgress(5)
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            for y in input:
                row = input[y]
                for x in row:
                    if row[x] is None:
                        self._entries.append(None)
                    else:
                        entry = []
                        for door in row[x]:
                            d = Door()
                            d.load(door)
                            entry.append(d)
                        self._entries.append(entry)
                    updateProgress(pct)

    def write_to_rom(self, rom):
        self._ptrTbl.clear(32 * 40)
        destWriteLoc = 0xF0000
        destRangeEnd = 0xF58EE  # TODO Is this correct? Can we go more?
        destLocs = dict()
        emptyEntryPtr = EbModule.toSnesAddr(rom.writeToFree([0, 0]))
        pct = 45.0 / (40 * 32)
        i = 0
        for entry in self._entries:
            if (entry is None) or (not entry):
                self._ptrTbl[i, 0].setVal(emptyEntryPtr)
            else:
                entryLen = len(entry)
                writeLoc = rom.getFreeLoc(2 + entryLen * 5)
                self._ptrTbl[i, 0].setVal(EbModule.toSnesAddr(writeLoc))
                rom[writeLoc] = entryLen & 0xff
                rom[writeLoc + 1] = entryLen >> 8
                writeLoc += 2
                for door in entry:
                    destWriteLoc += door.writeToRom(
                        rom, writeLoc, destWriteLoc,
                        destRangeEnd, destLocs)
                    writeLoc += 5
            i += 1
            updateProgress(pct)
        self._ptrTbl.writeToRom(rom)
        # Mark any remaining space as free
        if destWriteLoc < destRangeEnd:
            rom.addFreeRanges([(destWriteLoc, destRangeEnd)])
        updateProgress(5)
