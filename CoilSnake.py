#! /usr/bin/env python

import argparse
import os
import sys
import time

from modules import Project, Rom
from modules.Progress import setProgress

#from meliae import scanner

class CoilSnake:
    def __init__(self):
        self.loadModules()
    def loadModules(self):
        self._modules = []
        with open('modulelist.txt', 'r') as f:
            for line in f:
                line = line.rstrip('\n')
                if line[0] == '#':
                    continue
                mod = __import__("modules." + line)
                components = line.split('.')
                for comp in components:
                    mod = getattr(mod, comp)
                self._modules.append((line, getattr(mod,components[-1])()))
        #scanner.dump_all_objects('loadmod.json')
    def upgradeProject(self, baseRomFname, inputFname):
        # Open project
        proj = Project.Project()
        proj.load(inputFname + os.sep + Project.PROJECT_FILENAME)
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
            rom = Rom.Rom("romtypes.yaml")
            rom.load(baseRomFname)
            # Make sure project type matches romtype
            if rom.type() != proj.type():
                print "Rom type '" + rom.type() + "' does not match" \
                      " Project type '" + proj.type() + "'"
                return False
            # Make list of compatible modules
            curMods = filter(lambda (x,y): y.compatibleWithRomtype(rom.type()),
                    self._modules)

            for (n,m) in curMods:
                setProgress(0)
                startTime = time.time()
                print "-", m.name(), "...   0.00%",
                sys.stdout.flush()
                m.upgradeProject(proj.version(), Project.FORMAT_VERSION, rom,
                        lambda x,y: proj.getResource(n,x,y,'rb'),
                        lambda x,y: proj.getResource(n,x,y,'wb'))
                print "(%0.2fs)" % (time.time() - startTime)
            proj.setVersion(Project.FORMAT_VERSION)
            proj.write(inputFname + os.sep + Project.PROJECT_FILENAME)
            return True
    def projToRom(self, inputFname, cleanRomFname, outRomFname):
        # Open project
        proj = Project.Project()
        proj.load(inputFname + os.sep + Project.PROJECT_FILENAME)
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
        # Open rom
        rom = Rom.Rom("romtypes.yaml")
        rom.load(cleanRomFname)
        # Make sure project type matches romtype
        if rom.type() != proj.type():
            print "Rom type '" + rom.type() + "' does not match" \
                  " Project type '" + proj.type() + "'"
            return False
        # Make list of compatible modules
        curMods = filter(lambda (x,y): y.compatibleWithRomtype(rom.type()),
                self._modules)
        # Add the ranges from the compatible modules to the free range list
        newRanges = []
        for (n,m) in curMods:
            newRanges += m.freeRanges()
        rom.addFreeRanges(newRanges)

        print "From Project : ", inputFname, "(", proj.type(), ")"
        print "To       ROM : ", outRomFname, "(", rom.type(), ")"
        for (n,m) in curMods:
            setProgress(0)
            startTime = time.time()
            print "-", m.name(), "...   0.00%",
            sys.stdout.flush()
            m.readFromProject(lambda x,y: proj.getResource(n,x,y,'rb'))
            m.writeToRom(rom)
            m.free()
            print "(%0.2fs)" % (time.time() - startTime)
        rom.save(outRomFname)
        return True
    def romToProj(self, inputRomFname, outputFname):
        # Load the ROM
        rom = Rom.Rom("romtypes.yaml")
        rom.load(inputRomFname)
        # Load the Project
        proj = Project.Project()
        proj.load(outputFname + os.sep + Project.PROJECT_FILENAME, rom.type())

        print "From   ROM :", inputRomFname, "(", rom.type(), ")"
        print "To Project :", outputFname, "(", proj.type(), ")"
        curMods = filter(lambda (x,y): y.compatibleWithRomtype(rom.type()),
                self._modules)
        for (n,m) in curMods:
            setProgress(0)
            startTime = time.time()
            print "-", m.name(), "...   0.00%",
            sys.stdout.flush()
            m.readFromRom(rom)
            m.writeToProject(lambda x,y: proj.getResource(n,x,y,'wb'))
            m.free()
            #scanner.dump_all_objects( m.name() + '.json' )
            print "(%0.2fs)" % (time.time() - startTime)
        #scanner.dump_all_objects( 'complete.json' )
        proj.write(outputFname + os.sep + Project.PROJECT_FILENAME)
        return True


def main():
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
    args = parser.parse_args()

    if args.compileInfo != None:
        # Compile
        cs = CoilSnake()
        cs.projToRom(args.compileInfo[0],
                args.compileInfo[1], args.compileInfo[2])
    elif args.decompileInfo != None:
        # Decompile
        cs = CoilSnake()
        cs.romToProj(args.decompileInfo[0],
                args.decompileInfo[1])
    elif args.upgradeInfo != None:
        # Upgrade
        cs = CoilSnake()
        cs.upgradeProject(args.upgradeInfo[0],
                args.upgradeInfo[1])

#import cProfile
if (__name__ == '__main__'):
    sys.exit(main())
    #cProfile.run('main()', 'main.prof')
    #sys.exit(0)
