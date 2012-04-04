import EbModule

from modules.Progress import updateProgress

class CccInterfaceModule(EbModule.EbModule):
    _name = "CCScript"

    def __init__(self):
        self._usedRange = None
    def writeToProject(self, resourceOpener):
        # Just create an empty compilation summary file
        f = resourceOpener('ccscript/summary', 'txt')
        f.close()
        updateProgress(50)
    def readFromProject(self, resourceOpener):
        # Read the summary file
        sumFile = resourceOpener('ccscript/summary', 'txt')
        summary = sumFile.readlines()
        sumFile.close()
        # Only do anything if the summary file is not empty
        if len(summary) > 0:
            self._usedRange = (EbModule.toRegAddr(int(summary[7][30:36], 16)),
                    EbModule.toRegAddr(int(summary[8][30:36], 16)))

            modName = None
            inModuleSection = False # False = before section, True = in section
            for line in summary:
                if inModuleSection:
                    if line.startswith('-'):
                        inModuleSection = False
                    else:
                        labelKey = modName + "." + line.split(' ',1)[0]
                        labelVal = int(line[-7:-1],16)
                        EbModule.labelsDict[labelKey] = labelVal
                elif line.startswith("-") and modName != None:
                    inModuleSection = True
                elif line.startswith("Labels in module "):
                    modName = line[17:-1]
        updateProgress(50)
    def writeToRom(self, rom):
        if self._usedRange != None:
            # Mark the range as used in the Rom object
            rom.markRangeAsNotFree(self._usedRange)
        updateProgress(50)
