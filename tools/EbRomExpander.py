#! /usr/bin/env python

import argparse

import sys
sys.path.append('./')

from modules import Rom

def expandRom(r, ex=False):
   # Expand from 24 mbit to 32 mbit
   if (len(r) == 0x300000):
       r._data.fromlist([0] * 0x100000)
       r._size += 0x100000
       # For the super old text editor, heh
       #for i in range(0,4096):
       #    r[i*256 + 255 + 0x300000] = 2
   # Expand from 32 mbit to 48 mbit
   if ex and (len(r) == 0x400000):
       r[0x00ffd5] = 0x25
       r[0x00ffd7] = 0x0d
       r._data.fromlist([0] * 0x200000)
       r._size += 0x200000
       for i in range(0x8000, 0x8000 + 0x8000):
           r[0x400000 + i] = r[i]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='INPUT', type=argparse.FileType('rb'),
            help="an unexpanded EarthBound ROM")
    parser.add_argument('output', metavar='OUTPUT', type=argparse.FileType('wb'),
            help="the expanded EarthBound ROM")
    parser.add_argument('-ex', action="store_true", default=False,
            help="expand again to 48 megabits") 

    args = parser.parse_args()

    r = Rom.Rom('romtypes.yaml')
    r.load(args.input)

    expandRom(r, args.ex)

    r.save(args.output)

if (__name__ == '__main__'):
    sys.exit(main())
