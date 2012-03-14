#! /usr/bin/env python

import argparse
import sys
import os

import Project
import Rom

def loadModules():
    modules = []
    with open('modulelist.txt', 'r') as f:
        for line in f:
            line = line.rstrip('\n')
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

    modules = loadModules()
    romtype = ""
    # Load data into modules
    if os.path.splitext(args.input.name)[1] == ".csp":
        proj = Project.Project()
        proj.load(args.input)
        print "Importing from Project", args.input.name, "(", proj.type(), ")"
        for (n,m) in filter(
                lambda (x,y): y.compatibleWithRomtype(proj.type()), modules):
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.readFromProject(lambda x,y: proj.getResource(n,x,y,'r'))
            print "DONE"
        romtype = proj.type()
    else:
        input = Rom.Rom("romtypes.yaml")
        input.load(args.input)
        print "Importing from", args.input.name, "(", input.type(), ")"
        for (n,m) in filter(
                lambda (x,y): y.compatibleWithRomtype(input.type()), modules):
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.readFromRom(input)
            print "DONE"
        romtype = input.type()

    # Save data from modules
    if output_is_proj:
        proj = Project.Project()
        proj.load(args.output, romtype)
        print "Exporting as Project to", args.output, "(", romtype, ")"
        for (n,m) in filter(
                lambda (x,y): y.compatibleWithRomtype(romtype), modules):
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.writeToProject(lambda x,y: proj.getResource(n,x,y,'w'))
            print "DONE"
        proj.write(args.output)
    else:
        output = Rom.Rom("romtypes.yaml")
        output.load(args.cleanrom)
        print "Loaded", args.cleanrom.name, "(", output.type(), ")"
        print "Exporting to", args.output, "(", output.type(), ")"
        for (n,m) in filter(
                lambda (x,y): y.compatibleWithRomtype(output.type()), modules):
            print "-", m.name(), "Module\t...",
            sys.stdout.flush()
            m.writeToRom(output)
            print "DONE"
        output.save(args.output)

if (__name__ == '__main__'):
    sys.exit(main())
