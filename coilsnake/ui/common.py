import logging
import os
from shutil import copyfile
import time
from subprocess import Popen, PIPE, STDOUT

from coilsnake.Project import Project, FORMAT_VERSION, PROJECT_FILENAME, get_version_name
from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.model.common.blocks import Rom
from coilsnake.ui.formatter import CoilSnakeFormatter
from coilsnake.util.common.assets import open_asset, ccc_file_name


log = logging.getLogger(__name__)


def setup_logging(quiet=False, verbose=False):
    handler = logging.StreamHandler()
    handler.setFormatter(CoilSnakeFormatter())
    if quiet:
        logging.root.disabled = True
    elif verbose:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)


def upgrade_project(project_path, base_rom_filename):
    modules = load_modules()

    # Open project
    project_filename = os.path.join(project_path, PROJECT_FILENAME)

    project = Project()
    project.load(project_filename)
    check_if_project_too_new(project)

    if project.version== FORMAT_VERSION:
        log.info("Project is already up to date.")
        return

    log.info("Upgrading Project {} from {} to {}".format(project_path, get_version_name(project.version),
                                                         get_version_name(FORMAT_VERSION)))

    rom = Rom()
    rom.from_file(base_rom_filename)
    check_if_types_match(project=project, rom=rom)

    compatible_modules = [x for x in modules if x[1].is_compatible_with_romtype(rom.type)]
    for module_name, module_class in compatible_modules:
        log.debug("Starting upgrade of {}", module_class.NAME)
        start_time = time.time()
        with module_class() as module:
            module.upgrade_project(project.version, FORMAT_VERSION, rom,
                                   lambda x, y: project.get_resource(module_name, x, y, 'rb'),
                                   lambda x, y: project.get_resource(module_name, x, y, 'wb'),
                                   lambda x: project.delete_resource(module_name, x))
        log.info("Upgraded {} in {:.2f}s", module_class.NAME, time.time() - start_time)

    log.debug("Saving Project")
    project.version = FORMAT_VERSION
    project.write(project_filename)


def compile_project(project_path, base_rom_filename, output_rom_filename):
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
        log.info("Calling CCScript compiler")
        process = Popen(
            [ccc_file_name(), "-n", "-o", output_rom_filename, "-s", "F10000",
             "--summary", os.path.join(project_path, "ccscript", "summary.txt")] +
            script_filenames, stdout=PIPE, stderr=STDOUT)
        process.wait()
        if process.returncode == 0:
            log.info("CCScript compiler finished successfully")
        else:
            log.error("CCScript compiler failed with the following message:")
            log.error(process.stdout.read())
            raise CoilSnakeError("CCScript compilation failed")

    rom = Rom()
    rom.from_file(output_rom_filename)
    check_if_types_match(project=project, rom=rom)

    log.info("Compiling Project {}".format(project_path))
    compile_start_time = time.time()

    for module_name, module_class in modules:
        if module_class.is_compatible_with_romtype(rom.type):
            for free_range in module_class.FREE_RANGES:
                rom.deallocate(free_range)
        else:
            continue

        start_time = time.time()
        with module_class() as module:
            log.debug("Reading {}".format(module_class.NAME))
            module.read_from_project(lambda x, y: project.get_resource(module_name, x, y, 'rb'))
            log.debug("Writing {}".format(module_class.NAME))
            module.write_to_rom(rom)
        log.info("Compiled {} in {:.2f}s".format(module_class.NAME, time.time() - start_time))

    log.debug("Saving ROM")
    rom.to_file(output_rom_filename)

    log.info("Compiled to {} in {:.2f}s".format(output_rom_filename, time.time() - compile_start_time))


def decompile_rom(rom_filename, project_path):
    modules = load_modules()

    rom = Rom()
    rom.from_file(rom_filename)

    project = Project()
    project.load(os.path.join(project_path, PROJECT_FILENAME), rom.type)

    log.info("Decompiling ROM {}".format(rom_filename))
    decompile_start_time = time.time()

    for module_name, module_class in modules:
        if not module_class.is_compatible_with_romtype(rom.type):
            continue

        start_time = time.time()
        with module_class() as module:
            log.debug("Reading {}".format(module_class.NAME))
            module.read_from_rom(rom)
            log.debug("Writing {}".format(module_class.NAME))
            module.write_to_project(lambda x, y: project.get_resource(module_name, x, y, 'wb'))
        log.info("Decompiled {} in {:.2f}s".format(module_class.NAME, time.time() - start_time))

    log.debug("Saving Project")
    project.write(os.path.join(project_path, PROJECT_FILENAME))

    log.info("Decompiled to {} in {:.2f}s".format(project_path, time.time() - decompile_start_time))


def load_modules():
    all_modules = []
    with open_asset("modulelist.txt") as f:
        for line in f:
            line = line.rstrip('\n')
            if line[0] == '#':
                continue
            components = line.split('.')
            mod = __import__("coilsnake.modules." + line, globals(), locals(), [components[-1]])
            all_modules.append((line, mod.__dict__[components[-1]] ))
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