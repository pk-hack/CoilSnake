from datetime import datetime
import logging
import os
import json
from shutil import copyfile
import time
import sys
from ccscript import ccc

from CCScriptWriter.CCScriptWriter import CCScriptWriter

from coilsnake.model.common.ips import IpsPatch
from coilsnake.model.eb.blocks import EbRom
from coilsnake.model.eb.ebp import EbpPatch
from coilsnake.util.common.project import FORMAT_VERSION, PROJECT_FILENAME, get_version_name
from coilsnake.exceptions.common.exceptions import CoilSnakeError, CCScriptCompilationError
from coilsnake.model.common.blocks import Rom, ROM_TYPE_NAME_UNKNOWN, ROM_TYPE_NAME_EARTHBOUND
from coilsnake.ui.formatter import CoilSnakeFormatter
from coilsnake.util.common.project import Project
from coilsnake.util.common.assets import open_asset, ccscript_library_path


log = logging.getLogger(__name__)


def setup_logging(quiet=False, verbose=False, stream=None):
    # Disable the weird "STREAM" logging messages in Pillow 3.0.0
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL)

    if not stream:
        stream = sys.stdout
    handler = logging.StreamHandler(stream=stream)
    handler.setFormatter(CoilSnakeFormatter())
    if quiet:
        logging.root.disabled = True
    elif verbose:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)


def upgrade_project(project_path, base_rom_filename, progress_bar=None):
    if not os.path.isdir(project_path):
        raise RuntimeError("Project directory \"" + project_path + "\" is not a directory.")
    if not os.path.isfile(base_rom_filename):
        raise RuntimeError("Base Rom \"" + base_rom_filename + "\" is not a file.")

    modules = load_modules()

    # Open project
    project_filename = os.path.join(project_path, PROJECT_FILENAME)

    project = Project()
    project.load(project_filename)
    check_if_project_too_new(project)

    if project.version == FORMAT_VERSION:
        log.info("Project is already up to date.")
        return

    log.info("Upgrading project from version {} to {}".format(
        get_version_name(project.version),
        get_version_name(FORMAT_VERSION)))
    upgrade_start_time = time.time()

    rom = Rom()
    rom.from_file(base_rom_filename)
    check_if_types_match(project=project, rom=rom)

    compatible_modules = [(name, clazz) for name, clazz in modules if clazz.is_compatible_with_romtype(rom.type)]
    tick_amount = 1.0/len(compatible_modules)

    for module_name, module_class in compatible_modules:
        log.info("Upgrading {}...".format(module_class.NAME))
        start_time = time.time()
        with module_class() as module:
            module.upgrade_project(project.version, FORMAT_VERSION, rom,
                                   lambda x, y, astext=False : project.get_resource(module_name, x, y, 'rt' if astext else 'rb', 'utf-8' if astext else None),
                                   lambda x, y, astext=False: 
                                        project.get_resource(module_name, x, y, 
                                            'wt' if astext else 'wb', 
                                            'utf-8' if astext else None,
                                            '\n' if astext else None),
                                   lambda x: project.delete_resource(module_name, x))
            if progress_bar:
                progress_bar.tick(tick_amount)
        log.info("Finished upgrading {} in {:.2f}s".format(module_class.NAME, time.time() - start_time))

    project.version = FORMAT_VERSION
    project.write(project_filename)

    log.info("Upgraded {} in {:.2f}s".format(project_path, time.time() - upgrade_start_time))


def compile_project(project_path, base_rom_filename, output_rom_filename, ccscript_offset, progress_bar=None):
    if not os.path.isdir(project_path):
        raise RuntimeError("Project directory \"" + project_path + "\" is not a directory.")
    if not os.path.isfile(base_rom_filename):
        raise RuntimeError("Base Rom \"" + base_rom_filename + "\" is not a file.")

    modules = load_modules()

    project_filename = os.path.join(project_path, PROJECT_FILENAME)
    project = Project()
    project.load(project_filename)
    check_if_project_too_old(project)
    check_if_project_too_new(project)

    if base_rom_filename != output_rom_filename:
        copyfile(base_rom_filename, output_rom_filename)

    # Compile scripts using CCScript
    script_filenames = [os.path.join(project_path, "ccscript", x)
                        for x in os.listdir(os.path.join(project_path, "ccscript"))
                        if x.lower().endswith('.ccs')]

    if script_filenames:
        log.info("Compiling CCScript")
        if not ccscript_offset:
            ccscript_offset = "F10000"
        elif type(ccscript_offset) == int:
            ccscript_offset = "{:x}".format(ccscript_offset)

        ccc_args = ["-n",
                    "--libs", ccscript_library_path(),
                    "--summary", os.path.join(project_path, "ccscript", "summary.txt"),
                    "-s", ccscript_offset,
                    "-o", output_rom_filename] + script_filenames
        ccc_returncode, ccc_log = ccc(ccc_args)

        if ccc_returncode == 0:
            log.info("Finished compiling CCScript")
        else:
            raise CCScriptCompilationError("CCScript compilation failed with output:\n" + ccc_log)

    rom = Rom()
    rom.from_file(output_rom_filename)
    check_if_types_match(project=project, rom=rom)

    compatible_modules = [(name, clazz) for name, clazz in modules if clazz.is_compatible_with_romtype(rom.type)]
    tick_amount = 1.0/(2*len(compatible_modules))

    log.info("Compiling Project {}".format(project_path))
    compile_start_time = time.time()

    for module_name, module_class in modules:
        if module_class.is_compatible_with_romtype(rom.type):
            for free_range in module_class.FREE_RANGES:
                rom.deallocate(free_range)

    for module_name, module_class in modules:
        if not module_class.is_compatible_with_romtype(rom.type):
            continue

        log.info("Compiling {}...".format(module_class.NAME))
        start_time = time.time()
        with module_class() as module:
            module.read_from_project(lambda x, y, astext=False : project.get_resource(module_name, x, y, 'rt' if astext else 'rb', 'utf-8' if astext else None))
            if progress_bar:
                progress_bar.tick(tick_amount)
            module.write_to_rom(rom)
            if progress_bar:
                progress_bar.tick(tick_amount)
        log.info("Finished compiling {} in {:.2f}s".format(module_class.NAME, time.time() - start_time))

    log.debug("Saving ROM")
    rom.to_file(output_rom_filename)

    log.info("Compiled to {} in {:.2f}s, finished at {}".format(
        output_rom_filename, time.time() - compile_start_time, datetime.now().strftime('%I:%M:%S %p')))


def decompile_rom(rom_filename, project_path, progress_bar=None):
    if not os.path.isfile(rom_filename):
        raise RuntimeError("Rom \"" + rom_filename + "\" is not a file.")

    modules = load_modules()

    rom = Rom()
    rom.from_file(rom_filename)

    project = Project()
    project.load(os.path.join(project_path, PROJECT_FILENAME), rom.type)

    compatible_modules = [(name, clazz) for name, clazz in modules if clazz.is_compatible_with_romtype(rom.type)]
    tick_amount = 1.0/(2*len(compatible_modules))

    log.info("Decompiling ROM {}".format(rom_filename))
    decompile_start_time = time.time()

    for module_name, module_class in compatible_modules:
        if not module_class.is_compatible_with_romtype(rom.type):
            continue

        log.info("Decompiling {}...".format(module_class.NAME))
        start_time = time.time()
        with module_class() as module:
            module.read_from_rom(rom)
            if progress_bar:
                progress_bar.tick(tick_amount)
            module.write_to_project(
                lambda x, y, astext=False: 
                    project.get_resource(module_name, x, y, 
                        'wt' if astext else 'wb', 
                        'utf-8' if astext else None, 
                        '\n' if astext else None))
            if progress_bar:
                progress_bar.tick(tick_amount)
        log.info("Finished decompiling {} in {:.2f}s".format(module_class.NAME, time.time() - start_time))

    log.debug("Saving Project")
    project.write(os.path.join(project_path, PROJECT_FILENAME))

    log.info("Decompiled to {} in {:.2f}s".format(project_path, time.time() - decompile_start_time))


def decompile_script(rom_filename, project_path, progress_bar=None):
    if not os.path.isdir(project_path):
        raise RuntimeError("Project directory \"" + project_path + "\" is not a directory.")
    if not os.path.isfile(rom_filename):
        raise RuntimeError("Rom \"" + rom_filename + "\" is not a file.")

    used_path = project_path
    project_snake_file = os.path.join(project_path, PROJECT_FILENAME)
    project_ccscript_path = os.path.join(project_path, "ccscript")

    if not os.path.isfile(project_snake_file):
        used_path = os.path.abspath(os.path.join(project_path, os.pardir))
        project_snake_file = os.path.join(used_path, PROJECT_FILENAME)
        project_ccscript_path = os.path.join(used_path, "ccscript")
        if not os.path.isfile(project_snake_file):
            raise RuntimeError("Project directory \"" + project_path + "\" or its parent directory is not a valid project folder.")

    rom = Rom()
    rom.from_file(rom_filename)
    if rom.type != ROM_TYPE_NAME_EARTHBOUND:
        raise CoilSnakeError("Cannot decompile script of a non-Earthbound rom. A {} rom was supplied.".format(
            rom.type))
    del rom

    start_time = time.time()

    rom_file = open(rom_filename, "rb")
    try:
        ccsw = CCScriptWriter(rom_file, project_ccscript_path, False)
        ccsw.loadDialogue(True)
        ccsw.processDialogue()
        ccsw.outputDialogue(True)
    except Exception as inst:
        log.exception("Error")
    else:
        log.info("Decompiled script to {} in {:.2f}s".format(used_path, time.time() - start_time))
    finally:
        rom_file.close()


def patch_rom(clean_rom_filename, patched_rom_filename, patch_filename, headered, progress_bar=None):
    if not os.path.isfile(clean_rom_filename):
        raise RuntimeError("Clean Rom \"" + clean_rom_filename + "\" is not a file.")
    if not os.path.isfile(patch_filename):
        raise RuntimeError("Patch \"" + patch_filename + "\" is not a file.")

    if clean_rom_filename != patched_rom_filename:
        copyfile(clean_rom_filename, patched_rom_filename)

    log.info("Patching ROM {} with patch {}".format(patched_rom_filename, patch_filename))
    patching_start_time = time.time()

    if patch_filename.endswith(".ips"):
        output_rom = Rom()
        output_rom.from_file(clean_rom_filename)
        patch = IpsPatch()
    elif patch_filename.endswith(".ebp"):
        output_rom = EbRom()
        output_rom.from_file(clean_rom_filename)
        patch = EbpPatch()
    else:
        raise CoilSnakeError("Unknown patch format.")

    # Load the patch and expand the ROM as needed
    add_header = headered and not isinstance(patch, EbpPatch)
    extra = int(add_header)*0x200  # 0x200 if a header will be added, 0 otherwise
    patch.load(patch_filename)
    if isinstance(patch, EbpPatch):
        log.info("Patch: {title} by {author}".format(**patch.metadata))
    if patch.last_offset_used > len(output_rom) + extra:
        if patch.last_offset_used < 0x400000 + extra:
            output_rom.expand(0x400000)
        elif patch.last_offset_used < 0x600000 + extra:
            output_rom.expand(0x600000)
        else:
            output_rom.expand(patch.last_offset_used)

    # If the user specified the patch was made for a headered ROM, add a header
    # to the ROM
    if add_header:
        output_rom.add_header()

    # Apply the patch and write out the patched ROM
    patch.apply(output_rom)
    if add_header:
        # Remove the header that was added, so that we're always dealing with
        # unheadered ROMs in the end
        output_rom.data = output_rom.data[0x200:]
        output_rom.size -= 0x200
    output_rom.to_file(patched_rom_filename)

    log.info("Patched to {} in {:.2f}s".format(patched_rom_filename, time.time() - patching_start_time))
    
def create_patch(clean_rom, hacked_rom, patch_path, author, description, title, progress_bar=None):
    """Starts creating the patch in its own thread."""

    creating_patch_start_time = time.time()
    # Prepare the metadata.
    metadata = json.dumps({"patcher": "EBPatcher", "author": author,
                           "title": title, "description": description})
    
    
    # Try to create the patch; if it fails, display an error message.
    try:
        if patch_path.endswith(".ebp"):
            log.info("Creating EBP patch by " + author + " with description \"" + description + "\" called " + title + "...")
            patch = EbpPatch()
            patch.create(clean_rom, hacked_rom, patch_path, metadata)
        elif patch_path.endswith(".ips"):
            log.info("Creating IPS patch...")
            patch = IpsPatch()
            patch.create(clean_rom, hacked_rom, patch_path)
        else:
            raise CoilSnakeError("Unknown patch format.")
    except OSError as e:
        log.info("There was an error creating the patch: " + e)
        return

    # Display a success message.
    patch_name = ""
    if patch_path.rfind("/") != -1:
        patch_name = patch_path[patch_path.rfind("/") + 1:len(patch_path)]
    else:
        patch_name = patch_path[patch_path.rfind("\\") + 1:len(patch_path)]
    log.info("The patch {} was successfully created in {:.2f}s.".format(patch_name, time.time() - creating_patch_start_time))

def expand(romfile, ex=False):
    rom = Rom()
    rom.from_file(romfile)
    if (not ex and len(rom) >= 0x400000) or (ex and (len(rom) >= 0x600000)):
        return False
    else:
        if ex:
            rom.expand(0x600000)
        else:
            rom.expand(0x400000)
        rom.to_file(romfile)
        del rom
        return True

def add_header(romfile):
    if romfile:
        with Rom() as rom:
            rom.from_file(romfile)
            rom.add_header()
            rom.to_file(romfile)
        return True
    else:
        return False

def strip_header(romfile):
    if romfile:
        with Rom() as rom:
            rom.from_file(romfile)
            rom.to_file(romfile)
        return True
    else:
        return False


def load_modules():
    all_modules = []
    with open_asset("modulelist.txt") as f:
        for line in f:
            line = line.rstrip('\n')
            if line[0] == '#':
                continue
            components = line.split('.')
            mod = __import__("coilsnake.modules." + line, globals(), locals(), [components[-1]])
            all_modules.append((line, mod.__dict__[components[-1]]))
    return all_modules


def check_if_project_too_new(project):
    if project.version > FORMAT_VERSION:
        raise CoilSnakeError("This project is not compatible with this version of CoilSnake. Please use this project"
                             + " with a newer version of CoilSnake.")


def check_if_project_too_old(project):
    if project.version < FORMAT_VERSION:
        raise CoilSnakeError("This project must be upgraded before performing this operation.")


def check_if_types_match(project, rom):
    if rom.type != project.romtype:
        raise CoilSnakeError("Rom type {} does not match Project type {}".format(rom.type, project.romtype))
