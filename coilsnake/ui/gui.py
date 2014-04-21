#! /usr/bin/env python
import os
from subprocess import Popen
from os.path import dirname, isdir, join
import yaml
from threading import Thread
from time import time
from traceback import print_exc
from Tkinter import *
import tkFileDialog
import tkMessageBox
import ttk

from coilsnake.model.common.blocks import Rom
from coilsnake.ui import information
from coilsnake.ui.common import decompile_rom, compile_project, upgrade_project, setup_logging
from coilsnake.ui.fun import get_fun_title
from coilsnake.ui.information import coilsnake_about
from coilsnake.util.common.assets import ASSET_PATH


# Import CCScriptWriter from the submodule, if possible.

if isdir(join("tools", "CCScriptWriter")):
    sys.path.append(join("tools", "CCScriptWriter"))
    from CCScriptWriter import CCScriptWriter
else:
    CCScriptWriter = None


class CoilSnakeFrontend:
    PREFS_FNAME = "prefs.yml"

    def __init__(self):
        try:
            with open(self.PREFS_FNAME, 'r') as f:
                self._prefs = yaml.load(f, Loader=yaml.CSafeLoader)
        except IOError:
            self._prefs = {'title': 0}

    def get_preference_value(self, key):
        try:
            return self._prefs[key]
        except KeyError:
            return ""

    def save_preferences(self):
        with open(self.PREFS_FNAME, "w") as f:
            yaml.dump(self._prefs, f, Dumper=yaml.CSafeDumper)

    def toggle_titles(self):
        self._prefs["title"] = (~(self._prefs["title"])) | 1
        self.save_preferences()

    def about_menu(self):
        am = Toplevel(self.root)
        photo = PhotoImage(file=os.path.join(ASSET_PATH, "images", "logo.gif"))
        photoLabel = Label(am, image=photo)
        photoLabel.photo = photo
        photoLabel.pack(fill='both', expand=1)

        Label(am,
              text=coilsnake_about(),
              anchor="w", justify="left", bg="white", borderwidth=5,
              relief=GROOVE).pack(
            fill='both', expand=1)
        Button(am, text="Toggle Alternate Titles",
               command=self.toggle_titles).pack(fill=X)
        Button(am, text="Close", command=am.destroy).pack(fill=X)
        am.resizable(False, False)
        am.title("About CoilSnake %s" % information.VERSION)

    def set_text(self, entry, str):
        entry.delete(0, END)
        entry.insert(0, str)
        entry.xview(END)

    def set_emulator_exe(self):
        self._prefs["Emulator"] = tkFileDialog.askopenfilename(
            parent=self.root,
            title="Select an Emulator Executable",
            initialfile=self.get_preference_value("Emulator"))
        self.save_preferences()

    def browse_for_rom(self, entry, save=False):
        if save:
            fname = tkFileDialog.asksaveasfilename(
                parent=self.root, title="Select an output ROM",
                filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        else:
            fname = tkFileDialog.askopenfilename(
                parent=self.root, title="Select a ROM",
                filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if len(fname) > 0:
            self.set_text(entry, fname)

    def browse_for_project(self, entry, save=False):
        fname = tkFileDialog.askdirectory(
            parent=self.root, title="Select a Project Directory",
            mustexist=(not save))
        self.set_text(entry, fname)

    def run_rom(self, entry):
        romFname = entry.get()
        if self.get_preference_value("Emulator") == "":
            tkMessageBox.showerror(parent=self.root,
                                   title="Error",
                                   message="""Emulator executable not specified.
Please specify it in the Preferences menu.""")
        elif romFname != "":
            Popen([self.get_preference_value("Emulator"), romFname])

    def reset_console(self):
        pass

    def do_decompile(self, rom_entry, project_entry):
        rom = rom_entry.get()
        project = project_entry.get()

        if rom and project:
            # Update the GUI
            self.reset_console()
            self.decompile_button["state"] = DISABLED
            self.compile_button["state"] = DISABLED
            self.upgrade_button["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["export_rom"] = rom
            self._prefs["export_proj"] = project
            self.save_preferences()

            self.progress_bar["value"] = 0
            thread = Thread(target=self._do_decompile_help,
                            args=(rom, project))
            thread.start()

    def _do_decompile_help(self, rom, project):
        try:
            decompile_rom(rom_filename=rom, project_path=project)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.get_preference_value("ErrorDetails") == "1":
                print_exc()

        self.progress_bar["value"] = 0
        self.decompile_button["state"] = NORMAL
        self.compile_button["state"] = NORMAL
        self.upgrade_button["state"] = NORMAL

    def do_compile(self, project_entry, base_rom_entry, rom_entry):
        base_rom = base_rom_entry.get()
        rom = rom_entry.get()
        project = project_entry.get()

        if base_rom and rom and project:
            # Update the GUI
            self.reset_console()
            self.decompile_button["state"] = DISABLED
            self.compile_button["state"] = DISABLED
            self.upgrade_button["state"] = DISABLED
            self._importRunB["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["import_proj"] = project
            self._prefs["import_baserom"] = base_rom
            self._prefs["import_rom"] = rom
            self.save_preferences()

            # Reset the progress bar
            self.progress_bar["value"] = 0

            thread = Thread(target=self._do_compile_help,
                            args=(project, base_rom, rom))
            thread.start()

    def _do_compile_help(self, project, base_rom, rom):
        try:
            compile_project(project, base_rom, rom)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.get_preference_value("ErrorDetails") == "1":
                print_exc()
        self.progress_bar["value"] = 0
        self.decompile_button["state"] = NORMAL
        self.compile_button["state"] = NORMAL
        self.upgrade_button["state"] = NORMAL
        self._importRunB["state"] = NORMAL

    def do_upgrade(self, rom_entry, project_entry):
        rom = rom_entry.get()
        project = project_entry.get()

        if rom and project:
            # Update the GUI
            self.reset_console()
            self.decompile_button["state"] = DISABLED
            self.compile_button["state"] = DISABLED
            self.upgrade_button["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["upgrade_rom"] = rom
            self._prefs["upgrade_proj"] = project
            self.save_preferences()

            self.progress_bar["value"] = 0
            self.progress_bar.step(10)
            thread = Thread(target=self._do_upgrade_help,
                            args=(rom_entry.get(), project_entry.get()))
            thread.start()

    def _do_upgrade_help(self, rom, project):
        try:
            upgrade_project(project_path=project, base_rom_filename=rom)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.get_preference_value("ErrorDetails") == "1":
                print_exc()
        self.progress_bar["value"] = 0
        self.decompile_button["state"] = NORMAL
        self.compile_button["state"] = NORMAL
        self.upgrade_button["state"] = NORMAL

    def expand_rom(self, ex=False):
        rom = Rom()
        filename = tkFileDialog.askopenfilename(
            parent=self.root, title="Select a ROM to expand",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if filename:
            rom.load(filename)
            if (not ex and len(rom) >= 0x400000) or (ex and (len(rom) >= 0x600000)):
                tkMessageBox.showerror(
                    parent=self.root,
                    title="Error",
                    message="This ROM is already expanded.")
            else:
                if ex:
                    rom.expand(0x600000)
                else:
                    rom.expand(0x400000)
                rom.save(filename)
                del rom
                tkMessageBox.showinfo(
                    parent=self.root,
                    title="Expansion Successful",
                    message="Your ROM was expanded.")

    def expand_rom_ex(self):
        self.expand_rom(ex=True)

    def add_header_to_rom(self):
        filename = tkFileDialog.askopenfilename(
            parent=self.root, title="Select a ROM to which to add a header",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if filename:
            with Rom() as rom:
                rom.from_file(filename)
                rom.add_header()
                rom.to_file(filename)
            tkMessageBox.showinfo(
                parent=self.root,
                title="Header Addition Successful",
                message="Your ROM was given a header.")

    def strip_header_from_rom(self):
        filename = tkFileDialog.askopenfilename(
            parent=self.root, title="Select a ROM from which to remove a header",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if filename:
            with Rom() as rom:
                rom.from_file(filename)
                rom.to_file(filename)
            tkMessageBox.showinfo(
                parent=self.root,
                title="Header Removal Successful",
                message="Your ROM's header was removed.")

    def extract_earthbound_dialogue(self):
        if not CCScriptWriter:
            tkMessageBox.showerror(
                "CCScriptWriter Not Installed",
                "You need to place CCScriptWriter.py in the tools/CCScriptWriter folder.",
                parent=self.root)
            return
        rom_filename = tkFileDialog.askopenfilename(
            parent=self.root, title="Select an EarthBound ROM from which to extract the dialogue text",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if not rom_filename:
            return
        rom = Rom()
        rom.from_file(rom_filename)
        if rom.type() != "Earthbound":
            tkMessageBox.showerror(
                "Invalid EarthBound ROM",
                "You have specified an invalid EarthBound ROM.",
                parent=self.root)
            return
        del rom
        project_filename = tkFileDialog.askopenfilename(
            parent=self.root, title="Select a CoilSnake project to modify",
            filetypes=[('CoilSnake Project', 'Project.snake')])
        if not project_filename:
            return
        project_ccscript_path = join(dirname(project_filename), "ccscript")
        thread = Thread(
            target=self._run_CCScriptWriter,
            args=(project_ccscript_path, rom_filename))
        thread.start()

    def _run_CCScriptWriter(self, project_dir, rom_name):
        start = time()
        rom_file = open(rom_name, "rb")
        try:
            ccsw = CCScriptWriter(rom_file, project_dir, False)
            ccsw.loadDialogue(True)
            ccsw.processDialogue()
            ccsw.outputDialogue(True)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.get_preference_value("ErrorDetails") == "1":
                print_exc()
        else:
            print "Complete. Time: {:.2f}s".format(float(time() - start))
            tkMessageBox.showinfo(
                title="Dialogue Extraction Successful",
                message="Successfully extracted EarthBound dialogue.",
                parent=self.root)
        finally:
            rom_file.close()

    def create_gui(self):
        self.root = Tk()
        if self.get_preference_value("title") == 1:
            self.root.wm_title(get_fun_title() + " " + information.VERSION)
        else:
            self.root.wm_title("CoilSnake" + " " + information.VERSION)
            if self.get_preference_value("title") == 0:
                self._prefs["title"] = 1
                self.save_preferences()

        self.create_menubar()

        notebook = ttk.Notebook(self.root)

        decompile_frame = self.create_decompile_frame(notebook)
        notebook.add(decompile_frame, text="Decompile")

        compile_frame = self.create_compile_frame(notebook)
        notebook.add(compile_frame, text="Compile")

        upgrade_frame = self.create_upgrade_frame(notebook)
        notebook.add(upgrade_frame, text="Upgrade")

        notebook.grid(row=0, column=0, sticky=E+W)

        self.progress_bar = ttk.Progressbar(self.root, orient=HORIZONTAL, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=E+W)

        console_frame = Frame(self.root)
        console_frame.grid(row=2, column=0, sticky=E+W)
        scrollbar = Scrollbar(console_frame)
        self.console = Text(console_frame, width=80, height=8)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.console.pack(fill=X)
        scrollbar.config(command=self.console.yview)
        self.console.config(yscrollcommand=scrollbar.set)

        class StdoutRedirector(object):
            def __init__(self, textarea):
                self.textarea = textarea

            def write(self, str):
                self.textarea.insert(END, str)
                self.textarea.see(END)

            def flush(self):
                pass

        self.console_stream = StdoutRedirector(self.console)
        sys.stdout = self.console_stream
        sys.stderr = self.console_stream

        setup_logging(quiet=False, verbose=False)

    def main(self):
        self.create_gui()
        self.root.mainloop()

    def create_menubar(self):
        menubar = Menu(self.root)

        # Preferences pulldown menu
        prefMenu = Menu(menubar, tearoff=0)
        prefMenu.add_command(label="Emulator Executable",
                             command=self.set_emulator_exe)
        menubar.add_cascade(label="Preferences", menu=prefMenu)

        # Tools pulldown menu
        toolsMenu = Menu(menubar, tearoff=0)
        toolsMenu.add_command(label="Expand ROM to 32 MBit",
                              command=self.expand_rom)
        toolsMenu.add_command(label="Expand ROM to 48 MBit",
                              command=self.expand_rom_ex)
        toolsMenu.add_command(label="Add Header to ROM",
                              command=self.add_header_to_rom)
        toolsMenu.add_command(label="Remove Header from ROM",
                              command=self.strip_header_from_rom)
        toolsMenu.add_command(label="Extract EarthBound Dialogue to Project",
                              command=self.extract_earthbound_dialogue)
        menubar.add_cascade(label="Tools", menu=toolsMenu)

        # Help menu
        helpMenu = Menu(menubar, tearoff=0)
        helpMenu.add_command(label="About", command=self.about_menu)
        menubar.add_cascade(label="Help", menu=helpMenu)

        self.root.config(menu=menubar)

    def add_title_fields_to_frame(self, text, frame, row, column):
        Label(frame, text=text, justify=CENTER).grid(row=0, column=0, columnspan=4, sticky=E+W)

    def add_rom_fields_to_frame(self, name, frame, row, column):
        Label(frame, text="{}:".format(name), width=13, justify=RIGHT).grid(row=row, column=column, sticky=E+W)
        rom_entry = Entry(frame)
        rom_entry.grid(row=row, column=column+1)

        def browse_tmp():
            self.browse_for_rom(rom_entry)

        def run_tmp():
            self.run_rom(rom_entry)

        Button(frame, text="Browse...", command=browse_tmp).grid(row=row, column=column+2, sticky=E+W)
        Button(frame, text="Run", command=run_tmp).grid(row=row, column=column+3, sticky=E+W)

        return rom_entry

    def add_project_fields_to_frame(self, name, frame, row, column):
        Label(frame, text="{}:".format(name), width=13, justify=RIGHT).grid(row=row, column=column, sticky=E+W)
        project_entry = Entry(frame)
        project_entry.grid(row=row, column=column+1)

        def browse_tmp():
            self.browse_for_project(project_entry, save=True)

        Button(frame, text="Browse...", command=browse_tmp).grid(row=row, column=column+2, sticky=E+W)

        return project_entry

    def create_decompile_frame(self, notebook):
        decompile_frame = ttk.Frame(notebook)
        self.add_title_fields_to_frame(text="ROM -> New Project", frame=decompile_frame, row=0, column=0)

        input_rom_entry = self.add_rom_fields_to_frame(
            name="ROM", frame=decompile_frame, row=1, column=0)
        project_entry = self.add_project_fields_to_frame(
            name="Output Directory", frame=decompile_frame, row=2, column=0)

        def decompile_tmp():
            self.do_decompile(input_rom_entry, project_entry)

        self.decompile_button = Button(decompile_frame, text="Decompile", command=decompile_tmp)
        self.decompile_button.grid(row=3, column=0, columnspan=4, sticky=E+W)

        return decompile_frame

    def create_compile_frame(self, notebook):
        compile_frame = ttk.Frame(notebook)
        self.add_title_fields_to_frame(text="Project -> New ROM", frame=compile_frame, row=0, column=0)

        base_rom_entry = self.add_rom_fields_to_frame(
            name="Base ROM", frame=compile_frame, row=1, column=0)
        project_entry = self.add_project_fields_to_frame(
            name="Project", frame=compile_frame, row=2, column=0)
        output_rom_entry = self.add_rom_fields_to_frame(
            name="Output ROM", frame=compile_frame, row=3, column=0)

        def compile_tmp():
            self.do_compile(project_entry, base_rom_entry, output_rom_entry)

        self.compile_button = Button(compile_frame, text="Compile", command=compile_tmp)
        self.compile_button.grid(row=4, column=0, columnspan=4, sticky=E+W)

        return compile_frame

    def create_upgrade_frame(self, notebook):
        upgrade_frame = ttk.Frame(notebook)
        self.add_title_fields_to_frame(text="Upgrade Project", frame=upgrade_frame, row=0, column=0)

        rom_entry = self.add_rom_fields_to_frame(
            name="Base ROM", frame=upgrade_frame, row=1, column=0)
        project_entry = self.add_project_fields_to_frame(
            name="Project", frame=upgrade_frame, row=2, column=0)

        def upgrade_tmp():
            self.do_upgrade(rom_entry, project_entry)

        self.upgrade_button = Button(upgrade_frame, text="Upgrade", command=upgrade_tmp)
        self.upgrade_button.grid(row=3, column=0, columnspan=4, sticky=E+W)

        return upgrade_frame


def main():
    csf = CoilSnakeFrontend()
    sys.exit(csf.main())