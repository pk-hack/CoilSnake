import os

import EbModule
from modules.Progress import updateProgress


class CccInterfaceModule(EbModule.EbModule):
    SUMMARY_FILENAME = os.path.join('ccscript', 'summary')
    SUMMARY_FILENAME_EXTENSION = 'txt'

    NAME = "CCScript"

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._used_range = None

    def write_to_project(self, resource_open):
        # Just create an empty compilation summary file
        f = resource_open(CccInterfaceModule.SUMMARY_FILENAME, CccInterfaceModule.SUMMARY_FILENAME_EXTENSION)
        f.close()
        updateProgress(50)

    def read_from_project(self, resource_open):
        # Clear the labels dict
        EbModule.labelsDict.clear()
        # Read and parse the summary file
        with resource_open(CccInterfaceModule.SUMMARY_FILENAME, CccInterfaceModule.SUMMARY_FILENAME_EXTENSION) as \
                summary_file:
            summary_file_lines = summary_file.readlines()
            if summary_file_lines:
                module_name = None
                in_module_section = False  # False = before section, True = in section
                for line in summary_file:
                    line = line.rstrip()
                    if in_module_section:
                        if line.startswith('-'):
                            in_module_section = False
                        else:
                            label_key = module_name + "." + line.split(' ', 1)[0]
                            label_val = int(line[-6:], 16)
                            EbModule.labelsDict[label_key] = label_val
                    elif line.startswith("-") and module_name is not None:
                        in_module_section = True
                    elif line.startswith("Labels in module "):
                        module_name = line[17:]
        updateProgress(50)

    def write_to_rom(self, rom):
        if self._used_range:
            # Mark the range as used in the Rom object
            rom.markRangeAsNotFree(self._used_range)
        updateProgress(50)
