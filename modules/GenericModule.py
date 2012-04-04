from modules.Progress import updateProgress

class GenericModule:
    def name(self):
        return self._name
    def compatibleWithRomtype(self, romtype):
        return True
    def free(self):
        pass
    def freeRanges(self):
        return []
    def readFromRom(self, rom):
        updateProgress(50)
    def writeToRom(self, rom):
        updateProgress(50)
    def readFromProject(self, resourceOpener):
        updateProgress(50)
    def writeToProject(self, resourceOpener):
        updateProgress(50)
