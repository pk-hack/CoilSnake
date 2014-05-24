from datetime import datetime
import logging
import os
from shutil import copyfile
import time
import sys
from ccscript import ccc

from CCScriptWriter.CCScriptWriter import CCScriptWriter
from coilsnake.util.common.project import FORMAT_VERSION, PROJECT_FILENAME, get_version_name
from coilsnake.exceptions.common.exceptions import CoilSnakeError, CCScriptCompilationError
from coilsnake.model.common.blocks import Rom
from coilsnake.ui.formatter import CoilSnakeFormatter
from coilsnake.util.common.project import Project
from coilsnake.util.common.assets import open_asset, ccscript_library_path, asset_exists


log = logging.getLogger(__name__)


def setup_logging(quiet=False, verbose=False, stream=None):
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
                                   lambda x, y: project.get_resource(module_name, x, y, 'rb'),
                                   lambda x, y: project.get_resource(module_name, x, y, 'wb'),
                                   lambda x: project.delete_resource(module_name, x))
            if progress_bar:
                progress_bar.tick(tick_amount)
        log.info("Finished upgrading {} in {:.2f}s".format(module_class.NAME, time.time() - start_time))

    project.version = FORMAT_VERSION
    project.write(project_filename)

    log.info("Upgraded {} in {:.2f}s".format(project_path, time.time() - upgrade_start_time))


def compile_project(project_path, base_rom_filename, output_rom_filename, ccscript_offset=None, progress_bar=None):
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
            module.read_from_project(lambda x, y: project.get_resource(module_name, x, y, 'rb'))
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
            module.write_to_project(lambda x, y: project.get_resource(module_name, x, y, 'wb'))
            if progress_bar:
                progress_bar.tick(tick_amount)
        log.info("Finished decompiling {} in {:.2f}s".format(module_class.NAME, time.time() - start_time))

    log.debug("Saving Project")
    project.write(os.path.join(project_path, PROJECT_FILENAME))

    log.info("Decompiled to {} in {:.2f}s".format(project_path, time.time() - decompile_start_time))


def decompile_script(rom_filename, project_path, progress_bar=None):
    rom = Rom()
    rom.from_file(rom_filename)
    if rom.type != "Earthbound":
        raise CoilSnakeError("Cannot decompile script of a non-Earthbound rom. A {} rom was supplied.".format(
            rom.type))
    del rom

    project_ccscript_path = os.path.join(project_path, "ccscript")

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
        log.info("Decompiled script to {} in {:.2f}s".format(project_path, time.time() - start_time))
    finally:
        rom_file.close()


def load_modules():
    all_modules = []
    modulelist_filename = "modulelist.txt"
    if asset_exists("modulelist-override.txt"):
        modulelist_filename = "modulelist-override.txt"
    with open_asset(modulelist_filename) as f:
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