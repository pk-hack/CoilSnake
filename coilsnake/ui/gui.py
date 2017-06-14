#! /usr/bin/env python
import Tkinter
from functools import partial
import logging
from subprocess import Popen
from threading import Thread
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
from traceback import format_exc
import ttk
import webbrowser
from Tkinter import *
from ttk import *

import os
from PIL import ImageTk

from coilsnake.model.common.blocks import Rom
from coilsnake.ui import information, gui_util
from coilsnake.ui.common import decompile_rom, compile_project, upgrade_project, setup_logging, decompile_script, \
    patch_rom
from coilsnake.ui.gui_preferences import CoilSnakePreferences
from coilsnake.ui.gui_util import browse_for_patch, browse_for_rom, browse_for_project, open_folder, set_entry_text, \
    find_system_java_exe
from coilsnake.ui.information import coilsnake_about
from coilsnake.ui.widgets import ThreadSafeConsole, CoilSnakeGuiProgressBar
from coilsnake.util.common.project import PROJECT_FILENAME
from coilsnake.util.common.assets import asset_path


log = logging.getLogger(__name__)


class CoilSnakeGui(object):
    def __init__(self):
        self.preferences = CoilSnakePreferences()
        self.preferences.load()
        self.components = []
        self.progress_bar = None

    # Preferences functions

    def refresh_debug_logging(self):
        if self.preferences["debug mode"]:
            logging.root.setLevel(logging.DEBUG)
        else:
            logging.root.setLevel(logging.INFO)

    def set_debug_mode(self):
        confirm = tkMessageBox.askquestion(
            "Enable Debug Mode?",
            "Would you like to enable Debug mode? Debug mode will provide you with more detailed output while "
            + "CoilSnake is running.\n\n"
            + "This is generally only needed by advanced users.",
            icon="question"
        )

        self.preferences["debug mode"] = (confirm == "yes")
        self.preferences.save()

        self.refresh_debug_logging()

    def set_emulator_exe(self):
        tkMessageBox.showinfo(
            "Select the Emulator Executable",
            "Select an emulator executable for CoilSnake to use.\n\n"
            "Hint: It is probably named either zsnesw.exe, snes9x.exe, or higan-accuracy.exe"
        )

        emulator_exe = tkFileDialog.askopenfilename(
            parent=self.root,
            initialdir=os.path.expanduser("~"),
            title="Select an Emulator Executable")
        if emulator_exe:
            self.preferences["emulator"] = emulator_exe
            self.preferences.save()

    def set_ccscript_offset(self):
        ccscript_offset_str = tkSimpleDialog.askstring(
            title="Input CCScript Offset",
            prompt=("Specify the hexidecimal offset to which CCScript should compile text.\n"
                    + "(The default value is F10000)\n\n"
                    + "You should leave this setting alone unless if you really know what you are doing."),
            initialvalue="{:x}".format(self.preferences.get_ccscript_offset()).upper())

        if ccscript_offset_str:
            try:
                ccscript_offset = int(ccscript_offset_str, 16)
            except:
                tkMessageBox.showerror(parent=self.root,
                                       title="Error",
                                       message="{} is not a valid hexidecimal number.".format(ccscript_offset_str))
                return

            self.preferences.set_ccscript_offset(ccscript_offset)
            self.preferences.save()

    def get_java_exe(self):
        return self.preferences["java"] or find_system_java_exe()

    def set_java_exe(self):
        system_java_exe = find_system_java_exe()

        if system_java_exe:
            confirm = tkMessageBox.askquestion(
                "Configure Java",
                "CoilSnake has detected Java at the following location:\n\n"
                + system_java_exe + "\n\n"
                + "To use this installation of Java, select \"Yes\".\n\n"
                + "To override and instead use a different version of Java, select \"No\".",
                icon="question"
            )
            if confirm == "yes":
                self.preferences["java"] = None
                self.preferences.save()
                return

        tkMessageBox.showinfo(
            "Select the Java Executable",
            "Select a Java executable for CoilSnake to use.\n\n"
            "On Windows, it might be called \"javaw.exe\" or \"java.exe\"."
        )

        java_exe = tkFileDialog.askopenfilename(
            parent=self.root,
            title="Select the Java Executable",
            initialfile=(self.preferences["java"] or system_java_exe))
        if java_exe:
            self.preferences["java"] = java_exe
            self.preferences.save()

    def save_default_tab(self):
        tab_number = self.notebook.index(self.notebook.select())
        self.preferences.set_default_tab(tab_number)
        self.preferences.save()

    # GUI update functions
    def disable_all_components(self):
        for component in self.components:
            component["state"] = DISABLED

    def enable_all_components(self):
        for component in self.components:
            component["state"] = NORMAL

    # GUI popup functions

    def run_rom(self, entry):
        rom_filename = entry.get()
        if not self.preferences["emulator"]:
            tkMessageBox.showerror(parent=self.root,
                                   title="Error",
                                   message="""CoilSnake could not find an emulator.
Please configure your emulator in the Settings menu.""")
        elif rom_filename:
            Popen([self.preferences["emulator"], rom_filename])
    
    def open_ebprojedit(self, entry=None):
        if entry:
            project_path = entry.get()
        else:
            project_path = None

        java_exe = self.get_java_exe()
        if not java_exe:
            tkMessageBox.showerror(parent=self.root,
                                   title="Error",
                                   message="""CoilSnake could not find Java.
Please configure Java in the Settings menu.""")
            return

        command = [java_exe, "-jar", asset_path(["bin", "EbProjEdit.jar"])]
        if project_path:
            command.append(os.path.join(project_path, PROJECT_FILENAME))

        Popen(command)

    # Actions

    def do_decompile(self, rom_entry, project_entry):
        rom = rom_entry.get()
        project = project_entry.get()

        if rom and project:
            if os.path.isdir(project):
                confirm = tkMessageBox.askquestion("Are You Sure?",
                                                   "Are you sure you would like to permanently overwrite the "
                                                   + "contents of the selected output directory?",
                                                   icon='warning')
                if confirm != "yes":
                    return

            self.save_default_tab()

            # Update the GUI
            self.console.clear()
            self.disable_all_components()

            self.progress_bar.clear()
            thread = Thread(target=self._do_decompile_help, args=(rom, project))
            thread.start()

    def _do_decompile_help(self, rom, project):
        try:
            decompile_rom(rom_filename=rom, project_path=project, progress_bar=self.progress_bar)
        except Exception as inst:
            log.debug(format_exc())
            log.error(inst)

        self.progress_bar.clear()
        self.enable_all_components()

    def do_compile(self, project_entry, base_rom_entry, rom_entry):
        base_rom = base_rom_entry.get()
        rom = rom_entry.get()
        project = project_entry.get()

        if base_rom and rom and project:
            self.save_default_tab()

            base_rom_rom = Rom()
            base_rom_rom.from_file(base_rom)
            if base_rom_rom.type == "Earthbound" and len(base_rom_rom) == 0x300000:
                confirm = tkMessageBox.askquestion("Expand Your Base ROM?",
                                                   "You are attempting to compile using a base ROM which is "
                                                   "unexpanded. It is likely that this will not succeed, as CoilSnake "
                                                   "needs the extra space in an expanded ROM to store additional data."
                                                   "\n\n"
                                                   "Would you like to expand this base ROM before proceeding? This "
                                                   "will permanently overwrite your base ROM.",
                                                   icon='warning')
                if confirm == "yes":
                    base_rom_rom.expand(0x400000)
                    base_rom_rom.to_file(base_rom)
            del base_rom_rom

            # Update the GUI
            self.console.clear()
            self.disable_all_components()

            self.progress_bar.clear()

            log.info("Starting compilation...")

            thread = Thread(target=self._do_compile_help, args=(project, base_rom, rom))
            thread.start()

    def _do_compile_help(self, project, base_rom, rom):
        try:
            compile_project(project, base_rom, rom,
                            ccscript_offset=self.preferences.get_ccscript_offset(),
                            progress_bar=self.progress_bar)
        except Exception as inst:
            log.debug(format_exc())
            log.error(inst)

        self.progress_bar.clear()
        self.enable_all_components()

    def do_upgrade(self, rom_entry, project_entry):
        rom = rom_entry.get()
        project = project_entry.get()

        if rom and project:
            confirm = tkMessageBox.askquestion("Are You Sure?",
                                               "Are you sure you would like to upgrade this project? This operation "
                                               + "cannot be undone.\n\n"
                                               + "It is recommended that you backup your project before proceeding.",
                                               icon='warning')
            if confirm != "yes":
                return

            self.save_default_tab()

            # Update the GUI
            self.console.clear()
            self.disable_all_components()

            self.progress_bar.clear()
            thread = Thread(target=self._do_upgrade_help, args=(rom, project))
            thread.start()

    def _do_upgrade_help(self, rom, project):
        try:
            upgrade_project(project_path=project, base_rom_filename=rom, progress_bar=self.progress_bar)
        except Exception as inst:
            log.debug(format_exc())
            log.error(inst)

        self.progress_bar.clear()
        self.enable_all_components()

    def do_decompile_script(self, rom_entry, project_entry):
        rom = rom_entry.get()
        project = project_entry.get()

        if rom and project:
            confirm = tkMessageBox.askquestion("Are You Sure?",
                                               "Are you sure you would like to decompile the script into this "
                                               "project? This operation cannot be undone.\n\n"
                                               + "It is recommended that you backup your project before proceeding.",
                                               icon='warning')
            if confirm != "yes":
                return

            self.save_default_tab()

            # Update the GUI
            self.console.clear()
            self.disable_all_components()
            self.progress_bar.cycle_animation_start()

            thread = Thread(target=self._do_decompile_script_help, args=(rom, project))
            thread.start()

    def _do_decompile_script_help(self, rom, project):
        try:
            decompile_script(rom_filename=rom, project_path=project, progress_bar=self.progress_bar)
        except Exception as inst:
            log.debug(format_exc())
            log.error(inst)

        self.progress_bar.cycle_animation_stop()
        self.enable_all_components()

    def do_patch_rom(self, clean_rom_entry, patched_rom_entry, patch_entry, headered_var):
        clean_rom = clean_rom_entry.get()
        patched_rom = patched_rom_entry.get()
        patch = patch_entry.get()
        headered = headered_var.get()

        if clean_rom and patched_rom and patch:
            self.save_default_tab()

            # Update the GUI
            self.console.clear()
            self.disable_all_components()
            self.progress_bar.cycle_animation_start()

            thread = Thread(target=self._do_patch_rom_help, args=(clean_rom, patched_rom, patch, headered))
            thread.start()

    def _do_patch_rom_help(self, clean_rom, patched_rom, patch, headered):
        try:
            patch_rom(clean_rom, patched_rom, patch, headered, progress_bar=self.progress_bar)
        except Exception as inst:
            log.debug(format_exc())
            log.error(inst)

        self.progress_bar.cycle_animation_stop()
        self.enable_all_components()

    def main(self):
        self.create_gui()
        self.root.mainloop()

    def create_gui(self):
        self.root = Tk()
        self.root.wm_title("CoilSnake " + information.VERSION)

        self.icon = ImageTk.PhotoImage(file=asset_path(["images", "icon.png"]))
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)

        self.create_menubar()

        self.notebook = ttk.Notebook(self.root)

        decompile_frame = self.create_decompile_frame(self.notebook)
        self.notebook.add(decompile_frame, text="Decompile")

        compile_frame = self.create_compile_frame(self.notebook)
        self.notebook.add(compile_frame, text="Compile")

        upgrade_frame = self.create_upgrade_frame(self.notebook)
        self.notebook.add(upgrade_frame, text="Upgrade")

        decompile_script_frame = self.create_decompile_script_frame(self.notebook)
        self.notebook.add(decompile_script_frame, text="Decompile Script")

        patcher_patch_frame = self.create_apply_patch_frame(self.notebook)
        self.notebook.add(patcher_patch_frame, text="Apply Patch")

        #patcher_create_frame = self.create_create_patch_frame(self.notebook)
        #self.notebook.add(patcher_create_frame, text="Create Patch")

        self.notebook.pack(fill=BOTH, expand=1)
        self.notebook.select(self.preferences.get_default_tab())

        self.progress_bar = CoilSnakeGuiProgressBar(self.root, orient=HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=BOTH, expand=1)

        console_frame = Frame(self.root)

        scrollbar = Scrollbar(console_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.console = ThreadSafeConsole(console_frame, width=80, height=8)
        self.console.pack(fill=X)
        scrollbar.config(command=self.console.yview)
        self.console.config(yscrollcommand=scrollbar.set)
        console_frame.pack(fill=X, expand=1)

        def selectall_text(event):
            event.widget.tag_add("sel", "1.0", "end")
        self.root.bind_class("Text", "<Control-a>", selectall_text)

        def selectall_entry(event):
            event.widget.selection_range(0, END)
        self.root.bind_class("Entry", "<Control-a>", selectall_entry)

        def tab_changed(event):
            # Do this so some random element in the tab isn't selected upon tab change
            self.notebook.focus()
        self.notebook.bind("<<NotebookTabChanged>>", tab_changed)

        self.console_stream = self.console

        setup_logging(quiet=False, verbose=False, stream=self.console_stream)
        self.refresh_debug_logging()

    def create_about_window(self):
        self.about_menu = Toplevel(self.root, takefocus=True)
        self.about_menu.tk.call('wm', 'iconphoto', self.about_menu._w, self.icon)

        photo = ImageTk.PhotoImage(file=asset_path(["images", "logo.png"]))
        about_label = Label(self.about_menu, image=photo)
        about_label.photo = photo
        about_label.pack(side=LEFT, expand=1)

        about_right_frame = ttk.Frame(self.about_menu)
        Label(about_right_frame,
              text=coilsnake_about(),
              font=("Courier", 11),
              anchor="w",
              justify="left",
              borderwidth=5,
              relief=GROOVE).pack(fill=BOTH, expand=1, side=TOP)

        about_right_frame.pack(side=LEFT, fill=BOTH, expand=1)

        self.about_menu.resizable(False, False)
        self.about_menu.title("About CoilSnake {}".format(information.VERSION))
        self.about_menu.withdraw()
        self.about_menu.transient(self.root)

        self.about_menu.protocol('WM_DELETE_WINDOW', self.about_menu.withdraw)

    def create_menubar(self):
        menubar = Menu(self.root)

        # Tools pulldown menu
        tools_menu = Menu(menubar, tearoff=0)
        tools_menu.add_command(label="EB Project Editor",
                               command=self.open_ebprojedit)
        tools_menu.add_separator()
        tools_menu.add_command(label="Expand ROM to 32 MBit",
                               command=partial(gui_util.expand_rom, self.root))
        tools_menu.add_command(label="Expand ROM to 48 MBit",
                               command=partial(gui_util.expand_rom_ex, self.root))
        tools_menu.add_separator()
        tools_menu.add_command(label="Add Header to ROM",
                               command=partial(gui_util.add_header_to_rom, self.root))
        tools_menu.add_command(label="Remove Header from ROM",
                               command=partial(gui_util.strip_header_from_rom, self.root))
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Preferences pulldown menu
        pref_menu = Menu(menubar, tearoff=0)
        pref_menu.add_command(label="Configure Emulator",
                              command=self.set_emulator_exe)
        pref_menu.add_command(label="Configure Java",
                              command=self.set_java_exe)
        pref_menu.add_separator()
        pref_menu.add_command(label="Configure CCScript",
                              command=self.set_ccscript_offset)
        pref_menu.add_separator()
        pref_menu.add_command(label="Debug Mode",
                              command=self.set_debug_mode)
        menubar.add_cascade(label="Settings", menu=pref_menu)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)

        self.create_about_window()

        def show_about_window():
            self.about_menu.deiconify()
            self.about_menu.lift()

        def open_coilsnake_website():
            webbrowser.open(information.WEBSITE, 2)

        help_menu.add_command(label="About CoilSnake", command=show_about_window)
        help_menu.add_command(label="CoilSnake Website", command=open_coilsnake_website)

        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def create_decompile_frame(self, notebook):
        self.decompile_fields = dict()

        decompile_frame = ttk.Frame(notebook)
        self.add_title_label_to_frame(text="Decompile a ROM to create a new project.", frame=decompile_frame)

        profile_selector_init = self.add_profile_selector_to_frame(frame=decompile_frame,
                                                                   tab="decompile",
                                                                   fields=self.decompile_fields)

        input_rom_entry = self.add_rom_fields_to_frame(name="ROM", frame=decompile_frame)
        self.decompile_fields["rom"] = input_rom_entry
        project_entry = self.add_project_fields_to_frame(name="Output Directory", frame=decompile_frame)
        self.decompile_fields["output_directory"] = project_entry

        profile_selector_init()

        def decompile_tmp():
            self.do_decompile(input_rom_entry, project_entry)

        decompile_button = Button(decompile_frame, text="Decompile", command=decompile_tmp)
        decompile_button.pack(fill=BOTH, expand=1)
        self.components.append(decompile_button)

        return decompile_frame

    def create_compile_frame(self, notebook):
        self.compile_fields = dict()

        compile_frame = ttk.Frame(notebook)
        self.add_title_label_to_frame(text="Compile a project to create a new ROM.", frame=compile_frame)

        profile_selector_init = self.add_profile_selector_to_frame(frame=compile_frame,
                                                                   tab="compile",
                                                                   fields=self.compile_fields)

        base_rom_entry = self.add_rom_fields_to_frame(name="Base ROM", frame=compile_frame)
        self.compile_fields["base_rom"] = base_rom_entry
        project_entry = self.add_project_fields_to_frame(name="Project", frame=compile_frame)
        self.compile_fields["project"] = project_entry
        output_rom_entry = self.add_rom_fields_to_frame(name="Output ROM", frame=compile_frame, save=True)
        self.compile_fields["output_rom"] = output_rom_entry

        profile_selector_init()

        def compile_tmp():
            self.do_compile(project_entry, base_rom_entry, output_rom_entry)

        compile_button = Button(compile_frame, text="Compile", command=compile_tmp)
        compile_button.pack(fill=BOTH, expand=1)
        self.components.append(compile_button)

        return compile_frame

    def create_upgrade_frame(self, notebook):
        upgrade_frame = ttk.Frame(notebook)
        self.add_title_label_to_frame(text="Upgrade a project created using an older version of CoilSnake.",
                                      frame=upgrade_frame)

        rom_entry = self.add_rom_fields_to_frame(name="Clean ROM", frame=upgrade_frame)
        project_entry = self.add_project_fields_to_frame(name="Project", frame=upgrade_frame)

        def upgrade_tmp():
            self.preferences["default upgrade rom"] = rom_entry.get()
            self.preferences.save()
            self.do_upgrade(rom_entry, project_entry)

        self.upgrade_button = Button(upgrade_frame, text="Upgrade", command=upgrade_tmp)
        self.upgrade_button.pack(fill=BOTH, expand=1)
        self.components.append(self.upgrade_button)

        if self.preferences["default upgrade rom"]:
            set_entry_text(entry=rom_entry,
                           text=self.preferences["default upgrade rom"])

        return upgrade_frame

    def create_decompile_script_frame(self, notebook):
        decompile_script_frame = ttk.Frame(notebook)
        self.add_title_label_to_frame(text="Decompile a ROM's script to an already existing project.",
                                      frame=decompile_script_frame)

        input_rom_entry = self.add_rom_fields_to_frame(name="ROM", frame=decompile_script_frame)
        project_entry = self.add_project_fields_to_frame(name="Project", frame=decompile_script_frame)

        def decompile_script_tmp():
            self.preferences["default decompile script rom"] = input_rom_entry.get()
            self.preferences.save()
            self.do_decompile_script(input_rom_entry, project_entry)

        button = Button(decompile_script_frame, text="Decompile Script", command=decompile_script_tmp)
        button.pack(fill=BOTH, expand=1)
        self.components.append(button)

        if self.preferences["default decompile script rom"]:
            set_entry_text(entry=input_rom_entry,
                           text=self.preferences["default decompile script rom"])

        return decompile_script_frame

    def create_apply_patch_frame(self, notebook):
        patcher_patch_frame = ttk.Frame(notebook)
        self.add_title_label_to_frame("Apply an EBP or IPS patch to a ROM", patcher_patch_frame)

        clean_rom_entry = self.add_rom_fields_to_frame(name="Clean ROM", frame=patcher_patch_frame, padding_buttons=0)
        patched_rom_entry = self.add_rom_fields_to_frame(name="Patched ROM", frame=patcher_patch_frame, save=True,
                                                         padding_buttons=0)
        patch_entry = self.add_patch_fields_to_frame(name="Patch", frame=patcher_patch_frame)
        headered_var = self.add_headered_field_to_frame(name="ROM Header (IPS only)", frame=patcher_patch_frame)

        def patch_rom_tmp():
            self.preferences["default clean rom"] = clean_rom_entry.get()
            self.preferences["default patched rom"] = patched_rom_entry.get()
            self.preferences["default patch"] = patch_entry.get()
            self.preferences.save()
            self.do_patch_rom(clean_rom_entry, patched_rom_entry, patch_entry, headered_var)

        button = Button(patcher_patch_frame, text="Patch ROM", command=patch_rom_tmp)
        button.pack(fill=BOTH, expand=1)
        self.components.append(button)

        if self.preferences["default clean rom"]:
            set_entry_text(entry=clean_rom_entry,
                           text=self.preferences["default clean rom"])
        if self.preferences["default patched rom"]:
            set_entry_text(entry=patched_rom_entry,
                           text=self.preferences["default patched rom"])
        if self.preferences["default patch"]:
            set_entry_text(entry=patch_entry,
                           text=self.preferences["default patch"])

        return patcher_patch_frame

    def create_create_patch_frame(self, notebook):
        patcher_create_frame = ttk.Frame(notebook)
        self.add_title_label_to_frame("Create EBP patch from a ROM", patcher_create_frame)

        clean_rom_entry = self.add_rom_fields_to_frame(name="Clean ROM", frame=patcher_create_frame, padding_buttons=0)
        modified_rom_entry = self.add_rom_fields_to_frame(name="Modified ROM", frame=patcher_create_frame,
                                                          padding_buttons=0)
        patch_entry = self.add_patch_fields_to_frame(name="Patch", frame=patcher_create_frame, save=True)

        def create_patch_tmp():
            self.preferences["default clean rom"] = clean_rom_entry.get()
            self.preferences["default modified rom"] = modified_rom_entry.get()
            self.preferences.save()
            self.do_create_patch(clean_rom_entry, modified_rom_entry, patch_entry)

        button = Button(patcher_create_frame, text="Create Patch", command=create_patch_tmp)
        button.pack(fill=BOTH, expand=1)
        self.components.append(button)

        if self.preferences["default clean rom"]:
            set_entry_text(entry=clean_rom_entry,
                           text=self.preferences["default clean rom"])
        if self.preferences["default modified rom"]:
            set_entry_text(entry=modified_rom_entry,
                           text=self.preferences["default patched rom"])

        return patcher_create_frame

    def add_title_label_to_frame(self, text, frame):
        Label(frame, text=text, justify=CENTER).pack(fill=BOTH, expand=1)

    def add_profile_selector_to_frame(self, frame, tab, fields):
        profile_frame = ttk.Frame(frame)

        Label(profile_frame, text="Profile:", width=13).pack(side=LEFT, fill=BOTH, expand=1)

        def tmp_select(profile_name):
            for field_id in fields:
                set_entry_text(entry=fields[field_id],
                               text=self.preferences.get_profile_value(tab, profile_name, field_id))
            self.preferences.set_default_profile(tab, profile_name)
            self.preferences.save()

        profile_var = StringVar(profile_frame)

        profile = OptionMenu(profile_frame, profile_var, "", command=tmp_select)
        profile["width"] = 25
        profile.pack(side=LEFT, fill=BOTH, expand=1, ipadx=1)
        
        self.components.append(profile)

        def tmp_reload_options(selected_profile_name=None):
            profile["menu"].delete(0, END)
            for profile_name in sorted(self.preferences.get_profiles(tab)):
                if not selected_profile_name:
                    selected_profile_name = profile_name
                profile["menu"].add_command(label=profile_name,
                                            command=Tkinter._setit(profile_var, profile_name, tmp_select))
            profile_var.set(selected_profile_name)
            tmp_select(selected_profile_name)

        def tmp_new():
            profile_name = tkSimpleDialog.askstring("New Profile Name", "Specify the name of the new profile.")
            if profile_name:
                profile_name = profile_name.strip()
                if self.preferences.has_profile(tab, profile_name):
                    tkMessageBox.showerror(parent=self.root,
                                           title="Error",
                                           message="A profile with that name already exists.")
                    return

                self.preferences.add_profile(tab, profile_name)
                tmp_reload_options(profile_name)
                self.preferences.save()

        def tmp_save():
            profile_name = profile_var.get()
            for field_id in fields:
                self.preferences.set_profile_value(tab, profile_name, field_id, fields[field_id].get())
            self.preferences.save()

        def tmp_delete():
            if self.preferences.count_profiles(tab) <= 1:
                tkMessageBox.showerror(parent=self.root,
                                       title="Error",
                                       message="Cannot delete the only profile.")
            else:
                self.preferences.delete_profile(tab, profile_var.get())
                tmp_reload_options()
                self.preferences.save()

        button = Button(profile_frame, text="Save", width=6, command=tmp_save)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        button = Button(profile_frame, text="Delete", width=5, command=tmp_delete)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        button = Button(profile_frame, text="New", width=5, command=tmp_new)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        profile_frame.pack(fill=BOTH, expand=1)

        def tmp_reload_options_and_select_default():
            tmp_reload_options(selected_profile_name=self.preferences.get_default_profile(tab))

        return tmp_reload_options_and_select_default

    def add_rom_fields_to_frame(self, name, frame, save=False, padding_buttons=1):
        rom_frame = ttk.Frame(frame)

        Label(rom_frame, text="{}:".format(name), width=13, justify=RIGHT).pack(side=LEFT, fill=BOTH, expand=1)
        rom_entry = Entry(rom_frame, width=30)
        rom_entry.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(rom_entry)

        def browse_tmp():
            browse_for_rom(self.root, rom_entry, save)

        def run_tmp():
            self.run_rom(rom_entry)

        button = Button(rom_frame, text="Browse...", command=browse_tmp, width=6)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        button = Button(rom_frame, text="Run", command=run_tmp, width=5)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        for i in range(padding_buttons):
            button = Button(rom_frame, text="", width=5, state=DISABLED, takefocus=False)
            button.pack(side=LEFT, fill=BOTH, expand=1)
            button.lower()

        rom_frame.pack(fill=BOTH, expand=1)

        return rom_entry

    def add_project_fields_to_frame(self, name, frame):
        project_frame = ttk.Frame(frame)

        Label(project_frame, text="{}:".format(name), width=13, justify=RIGHT).pack(side=LEFT, fill=BOTH, expand=1)
        project_entry = Entry(project_frame, width=30)
        project_entry.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(project_entry)

        def browse_tmp():
            browse_for_project(self.root, project_entry, save=True)

        def open_tmp():
            open_folder(project_entry)

        def edit_tmp():
            self.open_ebprojedit(project_entry)

        button = Button(project_frame, text="Browse...", command=browse_tmp, width=6)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        button = Button(project_frame, text="Open", command=open_tmp, width=5)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        button = Button(project_frame, text="Edit", command=edit_tmp, width=5)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        project_frame.pack(fill=BOTH, expand=1)

        return project_entry

    def add_patch_fields_to_frame(self, name, frame, save=False):
        patch_frame = ttk.Frame(frame)

        Label(
            patch_frame, text="{}:".format(name), width=13, justify=RIGHT
        ).pack(side=LEFT, fill=BOTH, expand=1)
        patch_entry = Entry(patch_frame, width=30)
        patch_entry.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(patch_entry)

        def browse_tmp():
            browse_for_patch(self.root, patch_entry, save)

        button = Button(patch_frame, text="Browse...", command=browse_tmp, width=6)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        self.components.append(button)

        button = Button(patch_frame, text="", width=5, state=DISABLED, takefocus=False)
        button.pack(side=LEFT, fill=BOTH, expand=1)
        button.lower()

        patch_frame.pack(fill=BOTH, expand=1)

        return patch_entry

    def add_headered_field_to_frame(self, name, frame):
        patch_frame = ttk.Frame(frame)

        headered_var = BooleanVar()
        headered_check = Checkbutton(patch_frame, text=name, variable=headered_var)
        headered_check.pack(
            side=LEFT, fill=BOTH, expand=1
        )
        self.components.append(headered_check)
        patch_frame.pack(fill=BOTH, expand=1)

        return headered_var


def main():
    gui = CoilSnakeGui()
    sys.exit(gui.main())