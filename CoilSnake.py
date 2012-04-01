#! /usr/bin/env python

import argparse
import sys
import os

from modules import Project
from modules import Rom

def loadModules():
    modules = []
    with open('modulelist.txt', 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if line[0] == '#':
                continue
            mod = __import__("modules." + line)
            components = line.split('.')
            for comp in components:
                mod = getattr(mod, comp)
            modules.append((line, getattr(mod,components[-1])()))
    return modules

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cleanrom', dest='cleanrom', required=False,
        type=argparse.FileType('rb'), help="a clean, unmodified ROM")
    parser.add_argument('input', metavar='INPUT', type=argparse.FileType('r'),
        help="either a ROM or a CoilSnake project file")
    parser.add_argument('output', metavar='OUTPUT',
        help="either a ROM or a CoilSnake project file")
    args = parser.parse_args()

    output_is_proj = os.path.splitext(args.output)[1] == ".csp"
    if (not output_is_proj) and (args.cleanrom == None):
        print >> sys.stderr, "ERROR: Need a clean ROM to export to ROM"
        return
    input_is_proj = os.path.splitext(args.input.name)[1] == ".csp"

    modules = loadModules()
    romtype = ""
    # Load data into modules
    if input_is_proj and not output_is_proj:
        # Open project
        proj = Project.Project()
        proj.load(args.input)
        # Open rom
        rom = Rom.Rom("romtypes.yaml")
        rom.load(args.cleanrom)
        # Make sure project type matches romtype
        assert(rom.type() == proj.type())
        # Make list of compatible modules
        curMods = filter(lambda (x,y): y.compatibleWithRomtype(rom.type()), modules)
        # Add the ranges from the compatible modules to the free range list
        newRanges = []
        for (n,m) in curMods: 
            newRanges += m.freeRanges()
        rom.addFreeRanges(newRanges)

        print "Project:", args.input.name, " -> ROM:", args.output, "(", proj.type(), ")"
        for (n,m) in curMods:
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.readFromProject(lambda x,y: proj.getResource(n,x,y,'r'))
            m.writeToRom(rom)
            m.free()
            print "DONE"
        rom.save(args.output)
    elif not input_is_proj and output_is_proj:
        # Load the ROM
        rom = Rom.Rom("romtypes.yaml")
        rom.load(args.input)
        # Load the Project
        proj = Project.Project()
        proj.load(args.output, rom.type())

        print "ROM:", args.input.name, "-> Project:", args.output, "(", rom.type(), ")"
        for (n,m) in filter(
                lambda (x,y): y.compatibleWithRomtype(rom.type()), modules):
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.readFromRom(rom)
            m.writeToProject(lambda x,y: proj.getResource(n,x,y,'w'))
            m.free()
            print "DONE"
        proj.write(args.output)

#import cProfile
if (__name__ == '__main__'):
    sys.exit(main())
    #cProfile.run('main()', 'mainprof')
    #sys.exit(0)
