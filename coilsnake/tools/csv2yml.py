#! /usr/bin/env python

import sys
import argparse
import csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='INPUT', type=argparse.FileType('rb'), help="csv file")
    parser.add_argument('output', metavar='OUTPUT', type=argparse.FileType('wb'), help="yml file")

    args = parser.parse_args()

    csvreader = csv.reader(args.input)
    column_names = next(csvreader)
    i = 0
    f = args.output
    for row in csvreader:
        f.write(str(i) + ":\n")
        i += 1
        j = 0
        for attr in row:
            if len(attr) == 0:
                print("WARNING! Entry #" + str(i) + "'s \"" + column_names[j] + "\" is null")
            f.write("  " + column_names[j] + ": " + attr + "\n")
            j += 1

if __name__ == '__main__':
    sys.exit(main())
