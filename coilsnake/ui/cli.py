#! /usr/bin/env python

from subprocess import Popen, PIPE, STDOUT
from shutil import copyfile
import argparse
import os
import sys
import time
import logging

from coilsnake import Project, Rom
from coilsnake.Progress import setProgress
from coilsnake.ui import information


logging.basicConfig(format="%(name)s:%(levelname)s:\t%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CoilSnake:
    def __init__(self):
        self._all_modules = self.load_modules()

    def load_modules(self):
        all_modules = []
        with open(os.path.join(os.path.dirname(__file__), 'resources', 'modulelist.txt'), 'r') as f:
            for line in f:
                line = line.rstrip('\n')
                if line[0] == '#':
                    continue
                mod = __import__("modules." + line)
                components = line.split('.')
                for comp in components:
                    mod = getattr(mod, comp)
                all_modules.append((line, getattr(mod, components[-1])))
        return all_modules

    def upgradeProject(self, baseRomFname, inputFname):
        # Open project
        proj = Project.Project()
        proj.load(os.path.join(inputFname, Project.PROJECT_FILENAME))
        # Print
        print "Upgrading Project : ", inputFname, "(", proj.type(), ")"
        print "From              : CoilSnake", \
            Project.getVersionName(proj.version())
        print "To                : CoilSnake", \
            Project.getVersionName(Project.FORMAT_VERSION)
        # Check that this project needs upgrading
        if proj.version() > Project.FORMAT_VERSION:
            print "Project '" + inputFname + "' is not compatible" \
                                             " with this version of CoilSnake.\nPlease use this" \
                                             " project with a newer version of CoilSnake."
            return False
        elif proj.version() == Project.FORMAT_VERSION:
            print "This Project is already up-to-date.\nUpgrade cancelled."
            return False
        else:
            # Perform the upgrade:

            # Open rom
            rom = Rom.Rom()
            rom.load(baseRomFname)
            # Make sure project type matches romtype
            if rom.type() != proj.type():
                print "Rom type '" + rom.type() + "' does not match" \
                                                  " Project type '" + proj.type() + "'"
                return False

            compatible_modules = (x for x in self._all_modules if x[1].is_compatible_with_romtype(rom.type()))
            for (module_name, module_class) in compatible_modules:
                setProgress(0)
                start_time = time.time()
                print "-", module_class.NAME, "...   0.00%",
                sys.stdout.flush()
                with module_class() as module:
                    logger.info("Upgrading Project for module[%s]", module_name)
                    module.upgrade_project(proj.version(), Project.FORMAT_VERSION, rom,
                                           lambda x, y: proj.getResource(module_name, x, y, 'rb'),
                                           lambda x, y: proj.getResource(module_name, x, y, 'wb'),
                                           lambda x: proj.deleteResource(module_name, x))
                    logger.info("Completed module[%s]", module_name)
                print "(%0.2fs)" % (time.time() - start_time)

            proj.setVersion(Project.FORMAT_VERSION)
            proj.write(os.path.join(inputFname, Project.PROJECT_FILENAME))
            return True

    def projToRom(self, inputFname, cleanRomFname, outRomFname, ccc=None):
        # Open project
        proj = Project.Project()
        proj.load(os.path.join(inputFname, Project.PROJECT_FILENAME))
        # Check that the project is readable by this version of CS
        if proj.version() > Project.FORMAT_VERSION:
            print "Project '" + inputFname + "' is not compatible" \
                                             " with this version of CoilSnake.\nPlease use this" \
                                             " project with a newer version of CoilSnake."
            return False
        elif proj.version() < Project.FORMAT_VERSION:
            print "Project '" + inputFname + "' is not compatible" \
                                             " with this version of CoilSnake.\nPlease upgrade this" \
                                             " project before trying to use it."
            return False
        # Compile scripts using CCScript
        if cleanRomFname != outRomFname:
            copyfile(cleanRomFname, outRomFname)
        if ccc:
            scriptFnames = [os.path.join(inputFname, "ccscript", x)
                            for x in os.listdir(os.path.join(inputFname, "ccscript"))
                            if x.endswith('.ccs')]
            print "Calling external CCScript Compiler...",
            process = Popen(
                [ccc, "-n", "-o", outRomFname, "-s", "F10000",
                 "--summary", os.path.join(inputFname, "ccscript", "summary.txt")] +
                scriptFnames, stdout=PIPE, stderr=STDOUT)
            process.wait()
            if process.returncode == 0:
                print "Done"
            else:
                print
                print process.stdout.read(),
                raise RuntimeError("There is an error in your CCScript code."
                                   + " Scroll up to see the error message.")
        # Open rom
        rom = Rom.Rom()
        rom.load(outRomFname)
        # Make sure project type matches romtype
        if rom.type() != proj.type():
            print "Rom type '" + rom.type() + "' does not match" \
                                              " Project type '" + proj.type() + "'"
            return False

        compatible_modules = list(x for x in self._all_modules if x[1].is_compatible_with_romtype(rom.type()))
        new_free_ranges = []
        for (module_name, module_class) in compatible_modules:
            new_free_ranges += module_class.FREE_RANGES
        rom.addFreeRanges(new_free_ranges)
        print "From Project : ", inputFname, "(", proj.type(), ")"
        print "To       ROM : ", outRomFname, "(", rom.type(), ")"
        for (module_name, module_class) in compatible_modules:
            setProgress(0)
            start_time = time.time()
            print "-", module_class.NAME, "...   0.00%",
            sys.stdout.flush()
            with module_class() as module:
                logger.info("Reading from Project for module[%s]", module_name)
                module.read_from_project(lambda x, y: proj.getResource(module_name, x, y, 'rb'))
                logger.info("Writing to ROM for module[%s]", module_name)
                module.write_to_rom(rom)
                logger.info("Finished module[%s]", module_name)
            print "(%0.2fs)" % (time.time() - start_time)
        rom.save(outRomFname)
        return True

    def romToProj(self, inputRomFname, outputFname):
        # Load the ROM
        rom = Rom.Rom()
        rom.load(inputRomFname)
        # Load the Project
        proj = Project.Project()
        proj.load(os.path.join(outputFname, Project.PROJECT_FILENAME), rom.type())

        print "From   ROM :", inputRomFname, "(", rom.type(), ")"
        print "To Project :", outputFname, "(", proj.type(), ")"
        compatible_modules = (x for x in self._all_modules if x[1].is_compatible_with_romtype(rom.type()))
        for (module_name, module_class) in compatible_modules:
            setProgress(0)
            start_time = time.time()
            print "-", module_class.NAME, "...   0.00%",
            sys.stdout.flush()
            with module_class() as module:
                logger.info("Reading from ROM for module[%s]", module_name)
                module.read_from_rom(rom)
                logger.info("Writing to Project for module[%s]", module_name)
                module.write_to_project(lambda x, y: proj.getResource(module_name, x, y, 'wb'))
                logger.info("Finished module[%s]", module_name)
            print "(%0.2fs)" % (time.time() - start_time)
        proj.write(os.path.join(outputFname, Project.PROJECT_FILENAME))
        return True


def main():
    print "CoilSnake", information.VERSION, "(" + information.RELEASE_DATE + ")"
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--compile', action='store', nargs=3,
                       dest="compileInfo", help="Compile from Project to ROM",
                       metavar=("ProjectDirectory", "BaseROM", "OutputROM"))
    group.add_argument('-d', '--decompile', action='store', nargs=2,
                       dest="decompileInfo", help="Decompile from ROM to Project",
                       metavar=("ROM", "ProjectDirectory"))
    group.add_argument('-u', '--upgrade', action='store', nargs=2,
                       dest="upgradeInfo", help="Upgrade a Project to be compatible with"
                                                + " this version of CoilSnake",
                       metavar=("BaseROM", "ProjectDirectory"))
    parser.add_argument("--ccc", help="Path to CCScript Compiler Executable")
    args = parser.parse_args()

    if args.compileInfo is not None:
        # Compile
        cs = CoilSnake()
        cs.projToRom(args.compileInfo[0],
                     args.compileInfo[1], args.compileInfo[2],
                     args.ccc)
    elif args.decompileInfo is not None:
        # Decompile
        cs = CoilSnake()
        cs.romToProj(args.decompileInfo[0],
                     args.decompileInfo[1])
    elif args.upgradeInfo is not None:
        # Upgrade
        cs = CoilSnake()
        cs.upgradeProject(args.upgradeInfo[0],
                          args.upgradeInfo[1])


if __name__ == '__main__':
    main()