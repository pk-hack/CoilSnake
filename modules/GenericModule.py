class GenericModule:
    def name(self):
        return self._name
    def compatibleWithRom(self, rom):
        return True
    def readFromRom(self, rom):
        pass
    def writeToRom(self, rom):
        pass
    def readFromFile(self, file):
        pass
    def writeToFile(self, file):
        pass
