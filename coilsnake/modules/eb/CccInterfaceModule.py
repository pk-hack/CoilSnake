import logging

from coilsnake.Progress import updateProgress
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.model.eb.pointers import EbPointer
from coilsnake.util.eb.pointer import from_snes_address


log = logging.getLogger(__name__)


class CccInterfaceModule(EbModule):
    NAME = "CCScript"

    SUMMARY_RESOURCE_NAME = 'ccscript/summary'
    SUMMARY_RESOURCE_EXTENSION = 'txt'

    def __init__(self):
        super(CccInterfaceModule, self).__init__()
        self.used_range = None

    def write_to_project(self, resource_open):
        log.info("Creating empty CCScript compilation summary file")
        f = resource_open(CccInterfaceModule.SUMMARY_RESOURCE_NAME, CccInterfaceModule.SUMMARY_RESOURCE_EXTENSION)
        f.close()
        updateProgress(50)

    def read_from_project(self, resource_open):
        EbPointer.label_address_map.clear()
        # Read and parse the summary file
        with resource_open(CccInterfaceModule.SUMMARY_RESOURCE_NAME, CccInterfaceModule.SUMMARY_RESOURCE_NAME) as \
                summary_file:
            summary_file_lines = summary_file.readlines()
            if summary_file_lines:
                compilation_start_address = int(summary_file_lines[7][30:], 16)
                compilation_end_address = int(summary_file_lines[8][30:], 16)
                if compilation_start_address != 0xffffffff and compilation_end_address != 0xffffffff:
                    self.used_range = (from_snes_address(compilation_start_address),
                                       from_snes_address(compilation_end_address))
                    log.info("Found range[(%#06x,%#06x)] used during compilation",
                             self.used_range[0], self.used_range[1])
                else:
                    log.info("Found no space used during compilation")

                module_name = None
                in_module_section = False  # False = before section, True = in section
                for line in summary_file_lines:
                    line = line.rstrip()
                    if in_module_section:
                        if line.startswith("-"):
                            in_module_section = False
                        else:
                            label_key = module_name + "." + line.split(' ', 1)[0]
                            label_val = int(line[-6:], 16)
                            EbPointer.label_address_map[label_key] = label_val
                            log.debug("Adding CCScript label[%s] in with address[%06x] in module[%s]", label_key,
                                      label_val, module_name)
                    elif line.startswith("-") and module_name is not None:
                        in_module_section = True
                    elif line.startswith("Labels in module "):
                        module_name = line[17:]
                        log.debug("Found CCScript module[%s]", module_name)
        log.info("Found %d CCScript labels", len(EbPointer.label_address_map))
        updateProgress(50)

    def write_to_rom(self, rom):
        if self.used_range:
            log.info("Marking (%#x,%#x) as allocated by CCScript", self.used_range[0], self.used_range[1])
            rom.mark_allocated(self.used_range)
        updateProgress(50)
