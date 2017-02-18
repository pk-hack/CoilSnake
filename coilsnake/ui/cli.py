#! /usr/bin/env python
import argparse
import logging

from coilsnake.ui.common import compile_project, decompile_rom, upgrade_project, decompile_script, patch_rom, setup_logging
from coilsnake.model.common.blocks import Rom
from coilsnake.ui.information import coilsnake_about


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("--quiet", help="silence all output", action="store_true")
    subparsers = parser.add_subparsers()

    compile_parser = subparsers.add_parser("compile", help="compile from project to rom")
    compile_parser.add_argument("project_directory")
    compile_parser.add_argument("base_rom")
    compile_parser.add_argument("output_rom")
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
    
    expand32_parser = subparsers.add_parser("expand32", help="Expand a ROM's size to 32 MBits (4MB)")
    
    expand32_parser.add_argument("rom")
    expand32_parser.set_defaults(func=_expand32)
    
    expand48_parser = subparsers.add_parser("expand48", help="Expand a ROM's size to 48 MBits (6MB)")
    
    expand48_parser.add_argument("rom")
    expand48_parser.set_defaults(func=_expand48)
    
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
                    output_rom_filename=args.output_rom)


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
	patch_rom(clean_rom_filename=args.clean_rom,
			  patched_rom_filename=args.output_rom,
			  patch_filename=args.patch,
			  headered=args.headered)

def _expand32(args):
	_expand(romfile=args.rom,
			ex=False)

def _expand48(args):
	_expand(romfile=args.rom,
			ex=True)

def _addheader(args):
	_add_header(romfile=args.rom)

def _stripheader(args):
	_strip_header(romfile=args.rom)


def _expand(romfile, ex):
	rom = Rom()
	rom.from_file(romfile)
	if (not ex and len(rom) >= 0x400000) or (ex and (len(rom) >= 0x600000)):
		print "Error: This ROM is already expanded."
	else:
		if ex:
			rom.expand(0x600000)
		else:
			rom.expand(0x400000)
		rom.to_file(romfile)
		del rom
		outputstring = "Expansion Successful: Your ROM was expanded."
		if ex:
			outputstring += " (48MBits/6MB)"
		else:
			outputstring += " (32MBits/4MB)"
		print outputstring

def _add_header(romfile):
    if romfile:
        with Rom() as rom:
            rom.from_file(romfile)
            rom.add_header()
            rom.to_file(romfile)
        print "Header Addition Successful: Your ROM was given a header."

def _strip_header(romfile):
    if romfile:
        with Rom() as rom:
            rom.from_file(romfile)
            rom.to_file(romfile)
        print "Header Removal Successful: Your ROM's header was removed."


def _version(args):
    print coilsnake_about()
