#! /usr/bin/env python
import argparse
import logging

from coilsnake.ui.common import compile_project, decompile_rom, upgrade_project, decompile_script, create_patch, patch_rom, expand, add_header, strip_header, setup_logging
from coilsnake.model.common.blocks import Rom
from coilsnake.ui.information import coilsnake_about


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("--quiet", help="silence all output", action="store_true")
    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True

    compile_parser = subparsers.add_parser("compile", help="compile from project to rom")
    compile_parser.add_argument("project_directory")
    compile_parser.add_argument("base_rom")
    compile_parser.add_argument("output_rom")
    compile_parser.add_argument('--ccscript-offset')
    compile_parser.set_defaults(func=_compile)

    decompile_parser = subparsers.add_parser("decompile", help="decompile from rom to project")
    decompile_parser.add_argument("rom")
    decompile_parser.add_argument("project_directory")
    decompile_parser.set_defaults(func=_decompile)

    upgrade_parser = subparsers.add_parser("upgrade",
                                           help="upgrade a project which was created by an older version of CoilSnake")
    upgrade_parser.add_argument("base_rom")
    upgrade_parser.add_argument("project_directory")
    upgrade_parser.set_defaults(func=_upgrade)

    decomp_script_parser = subparsers.add_parser("scriptdump", help="Decompile a ROM's script to an already existing project.")

    decomp_script_parser.add_argument("rom_filename")
    decomp_script_parser.add_argument("project_directory")
    decomp_script_parser.set_defaults(func=_scriptdump)

    patch_rom_parser = subparsers.add_parser("patchrom", help="Apply an EBP or IPS patch to a ROM (for headered give true or false)")

    patch_rom_parser.add_argument("clean_rom")
    patch_rom_parser.add_argument("output_rom")
    patch_rom_parser.add_argument("patch")
    patch_rom_parser.add_argument("headered")
    patch_rom_parser.set_defaults(func=_patchrom)

    createpatch_parser = subparsers.add_parser("createpatch", help="Create a patch from a clean ROM and a hacked ROM.")

    createpatch_parser.add_argument("clean_rom")
    createpatch_parser.add_argument("hacked_rom")
    createpatch_parser.add_argument("output_path")
    createpatch_parser.add_argument("author", nargs='?')
    createpatch_parser.add_argument("description", nargs='?')
    createpatch_parser.add_argument("title", nargs='?')
    createpatch_parser.set_defaults(func=_createpatch)

    expand_parser = subparsers.add_parser("expand", help="Expand a ROM's size to 32 MBits (4MB) or 48 MBits (6MB). exhi is false for 4MB, and true for 6MB.")

    expand_parser.add_argument("rom")
    expand_parser.add_argument("exhi")
    expand_parser.set_defaults(func=_expand)

    addheader_parser = subparsers.add_parser("addheader", help="Add a header to a ROM.")

    addheader_parser.add_argument("rom")
    addheader_parser.set_defaults(func=_addheader)

    stripheader_parser = subparsers.add_parser("stripheader", help="Remove a header from a ROM.")

    stripheader_parser.add_argument("rom")
    stripheader_parser.set_defaults(func=_stripheader)

    version_parser = subparsers.add_parser("version", help="display version information")
    version_parser.set_defaults(func=_version)

    args = parser.parse_args()

    setup_logging(quiet=args.quiet, verbose=args.verbose)

    args.func(args)


def _compile(args):
    compile_project(project_path=args.project_directory,
                    base_rom_filename=args.base_rom,
                    output_rom_filename=args.output_rom,
                    ccscript_offset=args.ccscript_offset)

def _decompile(args):
    decompile_rom(rom_filename=args.rom,
                  project_path=args.project_directory)


def _upgrade(args):
    upgrade_project(base_rom_filename=args.base_rom,
                    project_path=args.project_directory)

def _scriptdump(args):
    decompile_script(rom_filename=args.rom_filename,
                     project_path=args.project_directory)

def _patchrom(args):
    if args.headered == "true":
        header = True
    else:
        header = False
    patch_rom(clean_rom_filename=args.clean_rom,
              patched_rom_filename=args.output_rom,
              patch_filename=args.patch,
              headered=header)

def _createpatch(args):
    if args.author == None:
        args.author = 'author'
    if args.description == None:
        args.description = 'description'
    if args.title == None:
        args.title = 'title'
    create_patch(clean_rom=args.clean_rom,
              hacked_rom=args.hacked_rom,
              patch_path=args.output_path,
              author=args.author,
              description=args.description,
              title=args.title)

def _expand(args):
    if args.exhi == "true":
        exval = True
    else:
        exval = False
    returntest = expand(romfile=args.rom,
                         ex=exval)
    if returntest and exval:
        print("Expansion Successful: Your ROM was expanded. (48Mbits/6MB)")
    if returntest and (not exval):
        print("Expansion Successful: Your ROM was expanded. (32Mbits/4MB)")
    if not returntest:
        print("Error: This ROM is already expanded.")

def _addheader(args):
    returntest = add_header(romfile=args.rom)
    if returntest:
        print("Header Addition Successful: Your ROM was given a header.")
    else:
        print("Error: Invalid ROM.")

def _stripheader(args):
    returntest = strip_header(romfile=args.rom)
    if returntest:
        print("Header Removal Successful: Your ROM's header was removed.")
    else:
        print("Error: Invalid ROM.")


def _version(args):
    print(coilsnake_about())
