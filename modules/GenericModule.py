class GenericModule:
    def name(self):
        return self._name
    def compatibleWithRomtype(self, romtype):
        return True
    def readFromRom(self, rom):
        pass
    def writeToRom(self, rom):
        pass
    def readFromProject(self, resourceOpener):
        pass
    def writeToProject(self, resourceOpener):
        pass
