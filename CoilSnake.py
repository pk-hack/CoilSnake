#! /usr/bin/env python

import argparse
import sys
import os

from modules import Project
from modules import Rom


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
    def projToRom(self, inputFname, cleanRomFname, outRomFname):
        # Open project
        proj = Project.Project()
        proj.load(inputFname)
        # Open rom
        rom = Rom.Rom("romtypes.yaml")
        rom.load(cleanRomFname)
        # Make sure project type matches romtype
        assert(rom.type() == proj.type())
        # Make list of compatible modules
        curMods = filter(lambda (x,y): y.compatibleWithRomtype(rom.type()), self._modules)
        # Add the ranges from the compatible modules to the free range list
        newRanges = []
        for (n,m) in curMods:
            newRanges += m.freeRanges()
        rom.addFreeRanges(newRanges)

        print "Project:", inputFname, " -> ROM:", outRomFname, "(", proj.type(), ")"
        for (n,m) in curMods:
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.readFromProject(lambda x,y: proj.getResource(n,x,y,'r'))
            m.writeToRom(rom)
            m.free()
            print "DONE"
        rom.save(outRomFname)
    def romToProj(self, inputRomFname, outputFname):
        # Load the ROM
        rom = Rom.Rom("romtypes.yaml")
        rom.load(inputRomFname)
        # Load the Project
        proj = Project.Project()
        proj.load(outputFname, rom.type())

        print "ROM:", inputRomFname, "-> Project:", outputFname, "(", rom.type(), ")"
        for (n,m) in filter(
                lambda (x,y): y.compatibleWithRomtype(rom.type()), self._modules):
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.readFromRom(rom)
            m.writeToProject(lambda x,y: proj.getResource(n,x,y,'w'))
            m.free()
            print "DONE"
        proj.write(outputFname)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cleanrom', dest='cleanrom', required=False,
        type=argparse.FileType('rb'), help="a clean, unmodified ROM")
    parser.add_argument('input', metavar='INPUT', type=argparse.FileType('r'),
        help="either a ROM or a CoilSnake project file")
    parser.add_argument('output', metavar='OUTPUT',
        help="either a ROM or a CoilSnake project file")
    args = parser.parse_args()

    output_is_proj = os.path.splitext(args.output)[1] == ".csproj"
    if (not output_is_proj) and (args.cleanrom == None):
        print >> sys.stderr, "ERROR: Need a clean ROM to export to ROM"
        return
    input_is_proj = os.path.splitext(args.input.name)[1] == ".csproj"

    cs = CoilSnake()
    # Load data into modules
    if input_is_proj and not output_is_proj:
        cs.projToRom(args.input.name, args.cleanrom, args.output)
    elif not input_is_proj and output_is_proj:
        cs.romToProj(args.input.name, args.output)

#import cProfile
if (__name__ == '__main__'):
    sys.exit(main())
    #cProfile.run('main()', 'main.prof')
    #sys.exit(0)
