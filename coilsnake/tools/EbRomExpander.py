#! /usr/bin/env python

import argparse
import sys

from coilsnake.model.common.blocks import Rom


sys.path.append('./')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='INPUT', type=argparse.FileType('rb'),
                        help="an unexpanded EarthBound ROM")
    parser.add_argument('output', metavar='OUTPUT', type=argparse.FileType('wb'),
                        help="the expanded EarthBound ROM")
    parser.add_argument('-ex', action="store_true", default=False,
                        help="expand again to 48 megabits")

    args = parser.parse_args()

    r = Rom.Rom()
    r.load(args.input)

    if args.ex:
        r.expand(0x600000)
    else:
        r.expand(0x400000)

    r.save(args.output)


if __name__ == '__main__':
    sys.exit(main())
