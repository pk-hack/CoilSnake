#! /usr/bin/env python
from typing import Callable

import sys
import tkinter as tk
import tkinter
from functools import partial
import logging
from subprocess import Popen
from threading import Thread
import tkinter.filedialog
import tkinter.messagebox
import tkinter.simpledialog
from traceback import format_exc
import tkinter.ttk
import webbrowser
from tkinter import *
from tkinter.ttk import *
import platform

import os
from PIL import ImageTk

from coilsnake.model.common.blocks import Rom, ROM_TYPE_GROUP_EBM2
from coilsnake.ui import information, gui_util
from coilsnake.ui.common import decompile_rom, compile_project, upgrade_project, setup_logging, decompile_script, \
    patch_rom, create_patch
from coilsnake.ui.gui_preferences import CoilSnakePreferences
from coilsnake.ui.gui_util import browse_for_patch, browse_for_rom, browse_for_project, open_folder, set_entry_text, \
    find_system_java_exe
from coilsnake.ui.information import coilsnake_about
from coilsnake.ui.widgets import ThreadSafeConsole, CoilSnakeGuiProgressBar
from coilsnake.util.common.project import PROJECT_FILENAME
from coilsnake.util.common.assets import asset_path

from coilsnake.ui.language import TranslationStringManager, LANGUAGES, global_strings

# Set up logging
log = logging.getLogger(__name__)

# Constants for button and label widths
BUTTON_WIDTH = 15
LABEL_WIDTH = 20

class GuiTranslationHelper:
    def __init__(self, strings: TranslationStringManager):
        self.strings = strings

    def change_language(self, language=None, language_name=None):
        return self.strings.change_language(language, language_name)

    def get(self, string_name: str) -> str:
        return self.strings.get(string_name)

    def register_callback(self, cb, invoke=True):
        self.strings.register_callback(cb, invoke)

    def register_widget(self, elem: Widget, string_name: str, invoke=True):
        cb = lambda: elem.configure(text=self.get(string_name))
        self.strings.register_callback(cb, invoke=invoke)

    def register_notebook_frame(self, notebook, frame, string_name, invoke=True):
        cb = lambda: notebook.tab(frame, text=self.get(string_name))
        self.strings.register_callback(cb, invoke=invoke)

class CoilSnakeGui(object):
    def __init__(self):
        self.preferences = CoilSnakePreferences()
        self.preferences.load()
        self.components = []
        self.progress_bar = None
        self.guistrings = GuiTranslationHelper(global_strings)

    # Function to open the language selection window
    def open_language_window(self):
        # Create a new top-level window for language selection
        language_window = tk.Toplevel(self.root)
        language_window.title("Select Language")
        language_window.geometry("250x200")

        # StringVar to store the selected language
        selected_language = tk.StringVar(value="en")  # Default to English

        # Frame for language selection
        language_frame = tk.LabelFrame(language_window, text="Select Language")
        language_frame.pack(pady=10, padx=10, fill="both")

        for language in LANGUAGES:
            tk.Radiobutton(
                language_frame,
                text=language.full_name,
                variable=selected_language,
                value=language.iso639_1_name
            ).pack(anchor="w")

        # Function to apply the selected language
        def apply_language():
            language = selected_language.get()
            self.guistrings.change_language(language_name=language)
            language_window.destroy()


        # OK Button to confirm selection
        ok_button = tk.Button(language_window, text="OK", command=apply_language)
        ok_button.pack(pady=10)

        # Cancel Button to close without applying changes
        cancel_button = tk.Button(language_window, text="Cancel", command=language_window.destroy)
        cancel_button.pack(pady=5)

    def refresh_debug_logging(self):
        if self.preferences["debug mode"]:
            logging.root.setLevel(logging.DEBUG)
        else:
            logging.root.setLevel(logging.INFO)

    def refresh_debug_mode_command_label(self):
        # The "Debug Mode" command is the 5th in the Preferences menu (starting counting at 0, including separators)
        self.pref_menu.entryconfig(5, label=self.get_debug_mode_command_label())

    def get_debug_mode_command_label(self):
        return self.guistrings.get("disable_debug_mode") if self.preferences["debug mode"] else self.guistrings.get("enable_debug_mode")

    def set_debug_mode(self):
        if self.preferences["debug mode"]:
            confirm = tkinter.messagebox.askquestion(
                self.guistrings.get("ask_disable_debug"),
                self.guistrings.get("ask_disable_debug_prompt"),
                icon="question"
            )

            if confirm == "yes":
                self.preferences["debug mode"] = False
        else:
            confirm = tkinter.messagebox.askquestion(
                self.guistrings.get("ask_enable_debug"),
                self.guistrings.get("ask_enable_debug_prompt")
                + self.guistrings.get("coilsnake_is_running")
                + self.guistrings.get("advanced_users"),
                icon="question"
            )

            if confirm == "yes":
                self.preferences["debug mode"] = True

        self.preferences.save()

        self.refresh_debug_logging()
        self.refresh_debug_mode_command_label()

    def set_emulator_exe(self):
        tkinter.messagebox.showinfo(
            self.guistrings.get("select_emu_exe"),
            self.guistrings.get("coilsnake_use_emu"),
            self.guistrings.get("emu_hint")
        )

        emulator_exe = tkinter.filedialog.askopenfilename(
            parent=self.root,
            initialdir=os.path.expanduser("~"),
            title=self.guistrings.get("select_an_emu"))
        if emulator_exe:
            self.preferences["emulator"] = emulator_exe
            self.preferences.save()

    def set_ccscript_offset(self):
        ccscript_offset_str = tkinter.simpledialog.askstring(
            title=self.guistrings.get("ccscript_offset"),
            prompt=(self.guistrings.get("which_ccscript_compile")
                    + self.guistrings.get("default_F10000")
                    + self.guistrings.get("know_what_youre_doing")),
            initialvalue="{:x}".format(self.preferences.get_ccscript_offset()).upper())

        if ccscript_offset_str:
            try:
                ccscript_offset = int(ccscript_offset_str, 16)
            except:
                tkinter.messagebox.showerror(parent=self.root,
                                       title=self.guistrings.get("error"),
                                       message=self.guistrings.get("not_a_valid_hex").format(ccscript_offset_str))
                return

            self.preferences.set_ccscript_offset(ccscript_offset)
            self.preferences.save()

    def get_java_exe(self):
        return self.preferences["java"] or find_system_java_exe()

    def set_java_exe(self):
        system_java_exe = find_system_java_exe()

        if system_java_exe:
            confirm = tkinter.messagebox.askquestion(
                self.guistrings.get("config_java"),
                self.guistrings.get("java_following_loc")
                + system_java_exe + "\n\n"
                + self.guistrings.get("select_yes")
                + self.guistrings.get("select_yes"),
                icon="question"
            )
            if confirm == "yes":
                self.preferences["java"] = None
                self.preferences.save()
                return

        tkinter.messagebox.showinfo(
            self.guistrings.get("select_the_java_exe"),
            self.guistrings.get("java_for_coilsnake"),
            self.guistrings.get("on_windows_info")
        )

        java_exe = tkinter.filedialog.askopenfilename(
            parent=self.root,
            title=self.guistrings.get("select_the_java_exe"),
            initialfile=(self.preferences["java"] or system_java_exe))
        if java_exe:
            self.preferences["java"] = java_exe
            self.preferences.save()

    def save_default_tab(self):
        tab_number = self.notebook.index(self.notebook.select())
        self.preferences.set_default_tab(tab_number)
        self.preferences.save()

    def save_geometry_and_close(self, e=None):
        self.preferences['width']  = self.root.winfo_width()
        self.preferences['height'] = self.root.winfo_height()
        self.preferences['xpos']   = self.root.winfo_x()
        self.preferences['ypos']   = self.root.winfo_y()
        self.preferences.save()
        self.root.destroy()

    def load_geometry(self):
        self.root.update_idletasks()
        width  = self.preferences['width']  or self.root.winfo_width()
        height = self.preferences['height'] or self.root.winfo_height()
        xpos   = self.preferences['xpos']   or self.root.winfo_x()
        ypos   = self.preferences['ypos']   or self.root.winfo_y()

        if platform.system() != "Windows" and platform.system() != "Darwin":
            # Workaround - On X11, the window coordinates refer to the window border rather than the content
            # Since there may be a menubar at the top of the screen, move the window to 100, 100 and
            # then measure the position, to know how much we need to compensate our position by.
            # This seems to exactly restore the window location on my machine.
            self.root.geometry('{}x{}+100+100'.format(width, height))
            self.root.update_idletasks()
            xpos -= (self.root.winfo_x() - 100)
            ypos -= (self.root.winfo_y() - 100)

        self.root.geometry('{}x{}+{}+{}'.format(width, height, xpos, ypos))
        self.root.update_idletasks()

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
            tkinter.messagebox.showerror(parent=self.root,
                                   title=self.guistrings.get("error"),
                                   message=self.guistrings.get("cant_find_emu"))
        elif rom_filename:
            Popen([self.preferences["emulator"], rom_filename])

    def open_ebprojedit(self, entry=None):
        if entry:
            project_path = entry.get()
        else:
            project_path = None

        java_exe = self.get_java_exe()
        if not java_exe:
            tkinter.messagebox.showerror(parent=self.root,
                                   title=self.guistrings.get("error"),
                                   message=self.guistrings.get("cant_find_java"))
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
                confirm = tkinter.messagebox.askquestion(self.guistrings.get("are_you_sure"),
                                                   self.guistrings.get("ask_perm_overwrite")
                                                   + self.guistrings.get("ask_perm_overwrite_2"),
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
            if base_rom_rom.type in ROM_TYPE_GROUP_EBM2 and len(base_rom_rom) == 0x300000:
                confirm = tkinter.messagebox.askquestion(self.guistrings.get("ask_expand_rom"),
                                                   self.guistrings.get("attempt_compile"),
                                                   self.guistrings.get("attempt_compile_2"),
                                                   self.guistrings.get("attempt_compile_3"),
                                                   "\n\n",
                                                   self.guistrings.get("ask_expand_base"),
                                                   self.guistrings.get("ask_expand_base_2"),
                                                   icon='warning')
                if confirm == "yes":
                    base_rom_rom.expand(0x400000)
                    base_rom_rom.to_file(base_rom)
            del base_rom_rom

            # Update the GUI
            self.console.clear()
            self.disable_all_components()

            self.progress_bar.clear()

            log.info(self.guistrings.get("start_comp"))

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
            confirm = tkinter.messagebox.askquestion(self.guistrings.get("are_you_sure"),
                                               self.guistrings.get("ask_upgrade")
                                               + self.guistrings.get("ask_upgrade_2")
                                               + self.guistrings.get("backup_info"),
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
            confirm = tkinter.messagebox.askquestion(self.guistrings.get("are_you_sure"),
                                               self.guistrings.get("decomp_script_prompt"),
                                               self.guistrings.get("decomp_script_prompt_2"),
                                               + self.guistrings.get("backup_info"),
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

    def do_create_patch(self, clean_rom_entry, hacked_rom_entry, patch_path_entry, author, description, title):
        clean_rom = clean_rom_entry.get()
        hacked_rom = hacked_rom_entry.get()
        patch_path = patch_path_entry.get()

        if clean_rom and hacked_rom and patch_path:
            self.save_default_tab()

            # Update the GUI
            self.console.clear()
            self.disable_all_components()
            self.progress_bar.cycle_animation_start()

            thread = Thread(target=self._do_create_patch_help, args=(clean_rom, hacked_rom, patch_path, author, description, title))
            thread.start()

    def _do_create_patch_help(self, clean_rom, hacked_rom, patch_path, author, description, title):
        try:
            if patch_path.endswith(".ebp"):
                create_patch(clean_rom, hacked_rom, patch_path, author, description, title, progress_bar=self.progress_bar)
            elif patch_path.endswith(".ips"):
                create_patch(clean_rom, hacked_rom, patch_path, "", "", "", progress_bar=self.progress_bar)
            else:
                log.info(self.guistrings.get("cant_patch_rom"))
                return
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
        self.guistrings.change_language(language_name="en") #replace this with [whatever is in Preferences when we put default language in the preferences stuff]
        self.guistrings.register_callback(lambda: self.root.wm_title(self.guistrings.get("coilsnake_name") + information.VERSION))

        if platform.system() == "Windows":
            self.root.tk.call("wm", "iconbitmap", self.root._w, asset_path(["images", "CoilSnake.ico"]))
        elif platform.system() == "Darwin":
            # Workaround - Raise the window
            from Cocoa import NSRunningApplication, NSApplicationActivateIgnoringOtherApps

            app = NSRunningApplication.runningApplicationWithProcessIdentifier_(os.getpid())
            app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        else:
            self.iconphoto_params = (True,
                ImageTk.PhotoImage(file=asset_path(["images", "16.png"])),
                ImageTk.PhotoImage(file=asset_path(["images", "22.png"])),
                ImageTk.PhotoImage(file=asset_path(["images", "24.png"])),
                ImageTk.PhotoImage(file=asset_path(["images", "32.png"])),
                ImageTk.PhotoImage(file=asset_path(["images", "48.png"])),
                ImageTk.PhotoImage(file=asset_path(["images", "64.png"])),
                ImageTk.PhotoImage(file=asset_path(["images", "128.png"])),
                ImageTk.PhotoImage(file=asset_path(["images", "256.png"]))
            )
            self.root.wm_iconphoto(*self.iconphoto_params)

        self.create_menubar()

        self.notebook = tkinter.ttk.Notebook(self.root)

        decompile_frame = self.create_decompile_frame(self.notebook)
        self.notebook.add(decompile_frame)
        self.guistrings.register_notebook_frame(self.notebook, decompile_frame, "decompile_text")

        compile_frame = self.create_compile_frame(self.notebook)
        self.notebook.add(compile_frame)
        self.guistrings.register_notebook_frame(self.notebook, compile_frame, "compile_text")

        upgrade_frame = self.create_upgrade_frame(self.notebook)
        self.notebook.add(upgrade_frame)
        self.guistrings.register_notebook_frame(self.notebook, upgrade_frame, "upgrade")

        decompile_script_frame = self.create_decompile_script_frame(self.notebook)
        self.notebook.add(decompile_script_frame)
        self.guistrings.register_notebook_frame(self.notebook, decompile_script_frame, "decomp_script")

        patcher_patch_frame = self.create_apply_patch_frame(self.notebook)
        self.notebook.add(patcher_patch_frame)
        self.guistrings.register_notebook_frame(self.notebook, patcher_patch_frame, "apply_patch")

        patcher_create_frame = self.create_create_patch_frame(self.notebook)
        self.notebook.add(patcher_create_frame)
        self.guistrings.register_notebook_frame(self.notebook, patcher_create_frame, "create_patch")

        self.notebook.pack(fill=X)
        self.notebook.select(self.preferences.get_default_tab())

        self.progress_bar = CoilSnakeGuiProgressBar(self.root, orient=HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=X)

        console_frame = Frame(self.root)

        scrollbar = Scrollbar(console_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.console = ThreadSafeConsole(console_frame, width=80, height=8)
        self.console.pack(fill=BOTH, expand=1)
        scrollbar.config(command=self.console.yview)
        self.console.config(yscrollcommand=scrollbar.set)
        console_frame.pack(fill=BOTH, expand=1)

        def selectall_text(event):
            event.widget.tag_add("sel", "1.0", "end")
        self.root.bind_class("Text", "<Control-a>", selectall_text)

        def selectall_entry(event):
            event.widget.selection_range(0, END)
        self.root.bind_class("Entry", "<Control-a>", selectall_entry)

        def tab_changed(event):
            # Do this so some random element in the tab isn't selected upon tab change
            self.notebook.focus()

            ## Recalculate the height of the notebook depending on the contents of the new tab

            # Ensure the dimensions of the widgets are up to date
            self.notebook.update_idletasks()

            # Get the width and height of the window, so we can reset it later
            width  = self.root.winfo_width()
            height = self.root.winfo_height()

            # Set the notebook height to the selected tab's requested height
            tab_window_name = self.notebook.select()
            tab = self.notebook.nametowidget(tab_window_name)
            tab_height = tab.winfo_reqheight()
            self.notebook.configure(height=tab_height)

            # Keeps the window from changing size
            self.root.geometry("{}x{}".format(width, height))

        self.notebook.bind("<<NotebookTabChanged>>", tab_changed)

        self.console_stream = self.console

        setup_logging(quiet=False, verbose=False, stream=self.console_stream)
        self.refresh_debug_logging()
        self.load_geometry()
        self.root.protocol("WM_DELETE_WINDOW", self.save_geometry_and_close)

    def create_about_window(self):
        self.about_menu = Toplevel(self.root, takefocus=True)

        if platform.system() == "Windows":
            self.about_menu.tk.call("wm", "iconbitmap", self.about_menu._w, asset_path(["images", "CoilSnake.ico"]))
        elif platform.system() != "Darwin":
            self.about_menu.wm_iconphoto(*self.iconphoto_params)

        photo_header = ImageTk.PhotoImage(file=asset_path(["images", "CS4_logo.png"]))
        about_header = Label(self.about_menu, image=photo_header, anchor=CENTER)
        about_header.photo = photo_header
        about_header.pack(side=TOP, fill=BOTH, expand=1)

        photo = ImageTk.PhotoImage(file=asset_path(["images", "logo.png"]))
        about_label = Label(self.about_menu, image=photo, justify=RIGHT)
        about_label.photo = photo
        about_label.pack(side=LEFT, fill=BOTH, expand=1)

        about_right_frame = tkinter.ttk.Frame(self.about_menu)
        Label(about_right_frame,
              text=coilsnake_about(),
              font=("Courier", 10),
              anchor=CENTER,
              justify=LEFT).pack(fill=BOTH, expand=1, side=TOP)

        about_right_frame.pack(side=LEFT, fill=BOTH, expand=1)

        self.about_menu.resizable(False, False)
        self.about_menu.title("About CoilSnake {}".format(information.VERSION))
        self.about_menu.withdraw()
        self.about_menu.transient(self.root)

        self.about_menu.protocol('WM_DELETE_WINDOW', self.about_menu.withdraw)

    last_used_temporary_menu_index = 1
    def add_menu_item_and_get_index(self, menu: Menu, command=None, submenu=None) -> int:
        templabel = f"MyTemp{self.last_used_temporary_menu_index}"
        self.last_used_temporary_menu_index += 1
        if command:
            menu.add_command(label=templabel, command=command)
        elif submenu:
            menu.add_cascade(label=templabel, menu=submenu)
        item_index = menu.index(templabel)
        return item_index

    def _add_translated_menu_item(self, menu: Menu, label_string_name: str, command=None, submenu=None):
        index = self.add_menu_item_and_get_index(menu, command=command, submenu=submenu)
        def translation_callback():
            menu.entryconfigure(index, label=self.guistrings.get(label_string_name))
        self.guistrings.register_callback(translation_callback)

    def add_translated_menu_command(self, menu: Menu, label_string_name: str, command: Callable[[], None]):
        self._add_translated_menu_item(menu, label_string_name, command=command)

    def add_translated_menu_cascade(self, menu: Menu, label_string_name: str, submenu: Menu):
        self._add_translated_menu_item(menu, label_string_name, submenu=submenu)

    def create_menubar(self):
        menubar = Menu(self.root)

        # Add 'About CoilSnake' to the app menu on macOS
        self.create_about_window()

        def show_about_window():
            self.about_menu.deiconify()
            self.about_menu.lift()

        if platform.system() == "Darwin":
            app_menu = Menu(menubar, name='apple')
            menubar.add_cascade(menu=app_menu)
            self.add_translated_menu_command(app_menu, "about_coilsnake", show_about_window)

        # Tools pulldown menu
        tools_menu = Menu(menubar, tearoff=0)
        self.add_translated_menu_command(tools_menu, "eb_proj_edit", self.open_ebprojedit)
        tools_menu.add_separator()
        self.add_translated_menu_command(tools_menu, "expand_to_32", partial(gui_util.expand_rom, self.root))
        self.add_translated_menu_command(tools_menu, "expand_to_48", partial(gui_util.expand_rom_ex, self.root))
        tools_menu.add_separator()
        self.add_translated_menu_command(tools_menu, "add_header", partial(gui_util.add_header_to_rom, self.root))
        self.add_translated_menu_command(tools_menu, "remove_header", partial(gui_util.strip_header_from_rom, self.root))
        self.add_translated_menu_cascade(menubar, "tools", tools_menu)

        # Preferences pulldown menu
        self.pref_menu = Menu(menubar, tearoff=0)
        self.add_translated_menu_command(self.pref_menu, "config_emu", self.set_emulator_exe)
        self.add_translated_menu_command(self.pref_menu, "config_java", self.set_java_exe)
        self.pref_menu.add_separator()
        self.add_translated_menu_command(self.pref_menu, "config_ccscript", self.set_ccscript_offset)
        self.pref_menu.add_separator()
        debug_mode_index = self.add_menu_item_and_get_index(self.pref_menu, command=self.set_debug_mode)
        self.guistrings.register_callback(lambda: self.pref_menu.entryconfigure(debug_mode_index, label=self.get_debug_mode_command_label()))
        self.pref_menu.add_separator()
        self.add_translated_menu_command(self.pref_menu, "language_setting", self.open_language_window)

        self.add_translated_menu_cascade(menubar, "settings", self.pref_menu)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)

        def open_coilsnake_website():
            webbrowser.open(information.WEBSITE, 2)

        if platform.system() != "Darwin":
            self.add_translated_menu_command(help_menu, "about_coilsnake", show_about_window)

        self.add_translated_menu_command(help_menu, "coilsnake_site", open_coilsnake_website)

        self.add_translated_menu_cascade(menubar, "help_text", help_menu)

        self.root.config(menu=menubar)

    def create_decompile_frame(self, notebook):
        self.decompile_fields = dict()

        decompile_frame = tkinter.ttk.Frame(notebook)
        self.add_title_label_to_frame("decomp_rom_new_proj", frame=decompile_frame)

        profile_selector_init = self.add_profile_selector_to_frame(frame=decompile_frame,
                                                                   tab="decompile",
                                                                   fields=self.decompile_fields)

        input_rom_entry = self.add_rom_fields_to_frame("rom", frame=decompile_frame)
        self.decompile_fields["rom"] = input_rom_entry
        project_entry = self.add_project_fields_to_frame("output_dir", frame=decompile_frame)
        self.decompile_fields["output_directory"] = project_entry

        profile_selector_init()

        def decompile_tmp():
            self.do_decompile(input_rom_entry, project_entry)

        decompile_button = Button(decompile_frame, command=decompile_tmp)
        decompile_button.pack(fill=X, expand=1)
        self.guistrings.register_widget(decompile_button, "decompile_text")

        self.components.append(decompile_button)

        return decompile_frame

    def create_compile_frame(self, notebook):
        self.compile_fields = dict()

        compile_frame = tkinter.ttk.Frame(notebook)
        self.add_title_label_to_frame("comp_rom_new_proj", frame=compile_frame)

        profile_selector_init = self.add_profile_selector_to_frame(frame=compile_frame,
                                                                   tab="compile",
                                                                   fields=self.compile_fields)

        base_rom_entry = self.add_rom_fields_to_frame("base_rom", frame=compile_frame)
        self.compile_fields["base_rom"] = base_rom_entry
        project_entry = self.add_project_fields_to_frame("project", frame=compile_frame)
        self.compile_fields["project"] = project_entry
        output_rom_entry = self.add_rom_fields_to_frame("output_rom", frame=compile_frame, save=True)
        self.compile_fields["output_rom"] = output_rom_entry

        profile_selector_init()

        def compile_tmp():
            self.do_compile(project_entry, base_rom_entry, output_rom_entry)

        compile_button = Button(compile_frame, command=compile_tmp)
        compile_button.pack(fill=X, expand=1)
        self.guistrings.register_widget(compile_button, "compile_text")
        self.components.append(compile_button)

        return compile_frame

    def create_upgrade_frame(self, notebook):
        upgrade_frame = tkinter.ttk.Frame(notebook)
        self.add_title_label_to_frame("upgrade_info", frame=upgrade_frame)

        rom_entry = self.add_rom_fields_to_frame("clean_rom", frame=upgrade_frame)
        project_entry = self.add_project_fields_to_frame("project", frame=upgrade_frame)

        def upgrade_tmp():
            self.preferences["default upgrade rom"] = rom_entry.get()
            self.preferences["default upgrade project"] = project_entry.get()
            self.preferences.save()
            self.do_upgrade(rom_entry, project_entry)

        self.upgrade_button = Button(upgrade_frame, command=upgrade_tmp)
        self.upgrade_button.pack(fill=X, expand=1)
        self.guistrings.register_widget(self.upgrade_button, "upgrade")
        self.components.append(self.upgrade_button)

        if self.preferences["default upgrade rom"]:
            set_entry_text(entry=rom_entry,
                           text=self.preferences["default upgrade rom"])

        if self.preferences["default upgrade project"]:
            set_entry_text(entry=project_entry,
                           text=self.preferences["default upgrade project"])

        return upgrade_frame

    def create_decompile_script_frame(self, notebook):
        decompile_script_frame = tkinter.ttk.Frame(notebook)
        self.add_title_label_to_frame("decomp_rom_script", frame=decompile_script_frame)

        input_rom_entry = self.add_rom_fields_to_frame("rom", frame=decompile_script_frame)
        project_entry = self.add_project_fields_to_frame("project", frame=decompile_script_frame)

        def decompile_script_tmp():
            self.preferences["default decompile script rom"] = input_rom_entry.get()
            self.preferences["default decompile script project"] = project_entry.get()
            self.preferences.save()
            self.do_decompile_script(input_rom_entry, project_entry)

        button = Button(decompile_script_frame, command=decompile_script_tmp)
        button.pack(fill=X, expand=1)
        self.guistrings.register_widget(button, "decomp_script")
        self.components.append(button)

        if self.preferences["default decompile script rom"]:
            set_entry_text(entry=input_rom_entry,
                           text=self.preferences["default decompile script rom"])

        if self.preferences["default decompile script project"]:
            set_entry_text(entry=project_entry,
                           text=self.preferences["default decompile script project"])

        return decompile_script_frame

    def create_apply_patch_frame(self, notebook):
        patcher_patch_frame = tkinter.ttk.Frame(notebook)
        self.add_title_label_to_frame("apply_patch_info", frame=patcher_patch_frame)

        clean_rom_entry = self.add_rom_fields_to_frame("clean_rom", frame=patcher_patch_frame, padding_buttons=0)
        patched_rom_entry = self.add_rom_fields_to_frame("patched_rom", frame=patcher_patch_frame, save=True,
                                                         padding_buttons=0)
        patch_entry = self.add_patch_fields_to_frame("patch", frame=patcher_patch_frame)
        headered_var = self.add_headered_field_to_frame("header_ips_only", frame=patcher_patch_frame)

        def patch_rom_tmp():
            self.preferences["default clean rom"] = clean_rom_entry.get()
            self.preferences["default patched rom"] = patched_rom_entry.get()
            self.preferences["default patch"] = patch_entry.get()
            self.preferences.save()
            self.do_patch_rom(clean_rom_entry, patched_rom_entry, patch_entry, headered_var)

        button = Button(patcher_patch_frame, command=patch_rom_tmp)
        button.pack(fill=X, expand=1)
        self.guistrings.register_widget(button, "patch_rom")
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
        patcher_create_frame = tkinter.ttk.Frame(notebook)
        self.add_title_label_to_frame("create_patch", patcher_create_frame)

        clean_rom_entry = self.add_rom_fields_to_frame("clean_rom", frame=patcher_create_frame, padding_buttons=0)
        hacked_rom_entry = self.add_rom_fields_to_frame("modded_rom", frame=patcher_create_frame, padding_buttons=0)
        patch_entry = self.add_patch_fields_to_frame("patch", frame=patcher_create_frame, save=True)

        def create_patch_tmp(author, description, title):
            self.preferences["default clean rom"] = clean_rom_entry.get()
            self.preferences["default hacked rom"] = hacked_rom_entry.get()
            self.preferences["default created patch"] = patch_entry.get()
            self.preferences.save()
            self.do_create_patch(clean_rom_entry, hacked_rom_entry, patch_entry, author, description, title)

        def create_patch_do_first():
            if patch_entry.get().endswith(".ebp"):
                popup_ebp_patch_info(self, notebook)
            elif patch_entry.get().endswith(".ips"):
                create_patch_tmp("", "", "")
            else:
                exc = Exception(self.guistrings.get("invalid_format"))
                log.error(exc)

        def popup_ebp_patch_info(self, notebook):

            if self.preferences["default author"] is None:
                self.preferences["default author"] = self.gui_string_manager.get("author")

            author = self.preferences["default author"]

            if self.preferences["default description"] is None:
                self.preferences["default description"] = self.gui_string_manager.get("desc")

            description = self.preferences["default description"]

            if self.preferences["default title"] is None:
                self.preferences["default title"] = self.gui_string_manager.get("title")

            title = self.preferences["default title"]

            top = self.top = Toplevel(notebook)
            top.wm_title(self.gui_string_manager.get("ebp_patch"))
            l = Label(top,text=self.gui_string_manager.get("input_ebp"))
            l.pack()
            auth = Entry(top)
            auth.delete(0,)
            auth.insert(0,author)
            auth.pack()
            desc = Entry(top)
            desc.delete(0,)
            desc.insert(0,description)
            desc.pack()
            titl = Entry(top)
            titl.delete(0,)
            titl.insert(0,title)
            titl.pack()

            def cleanup():
                author = auth.get()
                self.preferences["default author"] = author
                description = desc.get()
                self.preferences["default description"] = description
                title = titl.get()
                self.preferences["default title"] = title
                self.top.destroy()
                create_patch_tmp(author, description, title)

            self.b=Button(top,text=self.gui_string_manager.get("ok"),command=cleanup)
            self.b.pack()

        button = Button(patcher_create_frame, command=create_patch_do_first)
        button.pack(fill=X, expand=1)
        self.guistrings.register_widget(button, "create_patch")
        self.components.append(button)

        if self.preferences["default clean rom"]:
            set_entry_text(entry=clean_rom_entry,
                           text=self.preferences["default clean rom"])
        if self.preferences["default hacked rom"]:
            set_entry_text(entry=hacked_rom_entry,
                           text=self.preferences["default hacked rom"])
        if self.preferences["default created patch"]:
            set_entry_text(entry=patch_entry,
                           text=self.preferences["default created patch"])

        return patcher_create_frame


    def add_title_label_to_frame(self, text_string_name, frame):
        label = Label(frame, justify=CENTER)
        label.pack(fill=BOTH, expand=1)
        self.guistrings.register_widget(label, text_string_name)

    def add_profile_selector_to_frame(self, frame, tab, fields):
        profile_frame = tkinter.ttk.Frame(frame)

        label = Label(profile_frame, width=LABEL_WIDTH)
        label.pack(side=LEFT)
        self.guistrings.register_widget(label, "profile")

        def tmp_select(profile_name):
            for field_id in fields:
                set_entry_text(entry=fields[field_id],
                               text=self.preferences.get_profile_value(tab, profile_name, field_id))
            self.preferences.set_default_profile(tab, profile_name)
            self.preferences.save()

        profile_var = StringVar(profile_frame)

        profile = OptionMenu(profile_frame, profile_var, "", command=tmp_select)
        profile.pack(side=LEFT, fill=BOTH, expand=1, ipadx=1)

        self.components.append(profile)

        def tmp_reload_options(selected_profile_name=None):
            profile["menu"].delete(0, END)
            for profile_name in sorted(self.preferences.get_profiles(tab)):
                if not selected_profile_name:
                    selected_profile_name = profile_name
                profile["menu"].add_command(label=profile_name,
                                            command=tkinter._setit(profile_var, profile_name, tmp_select))
            profile_var.set(selected_profile_name)
            tmp_select(selected_profile_name)

        def tmp_new():
            profile_name = tkinter.simpledialog.askstring(self.guistrings.get("new_prof_name"), self.guistrings.get("specify_name"))
            if profile_name:
                profile_name = profile_name.strip()
                if self.preferences.has_profile(tab, profile_name):
                    tkinter.messagebox.showerror(parent=self.root,
                                           title=self.guistrings.get("error"),
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
                tkinter.messagebox.showerror(parent=self.root,
                                       title=self.guistrings.get("error"),
                                       message=self.guistrings.get("cant_delete_prof"))
            else:
                self.preferences.delete_profile(tab, profile_var.get())
                tmp_reload_options()
                self.preferences.save()

        button = Button(profile_frame, width=BUTTON_WIDTH, command=tmp_save)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "save")
        self.components.append(button)

        button = Button(profile_frame, width=BUTTON_WIDTH, command=tmp_delete)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "delete")
        self.components.append(button)

        button = Button(profile_frame, width=BUTTON_WIDTH, command=tmp_new)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "new")
        self.components.append(button)

        profile_frame.pack(fill=X, expand=1)

        def tmp_reload_options_and_select_default():
            tmp_reload_options(selected_profile_name=self.preferences.get_default_profile(tab))

        return tmp_reload_options_and_select_default

    def add_rom_fields_to_frame(self, text_string_name, frame, save=False, padding_buttons=1):
        rom_frame = tkinter.ttk.Frame(frame)

        label = Label(rom_frame, width=LABEL_WIDTH, justify=RIGHT)
        label.pack(side=LEFT)
        self.guistrings.register_callback(lambda: label.configure(text="{}:".format(self.guistrings.get(text_string_name))))
        rom_entry = Entry(rom_frame)
        rom_entry.pack(side=LEFT, fill=BOTH, expand=1, padx=1)
        self.components.append(rom_entry)

        def browse_tmp():
            browse_for_rom(self.root, rom_entry, save)

        def run_tmp():
            self.run_rom(rom_entry)

        button = Button(rom_frame, command=browse_tmp, width=BUTTON_WIDTH)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "browse")
        self.components.append(button)

        button = Button(rom_frame, command=run_tmp, width=BUTTON_WIDTH)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "run")
        self.components.append(button)

        for _ in range(padding_buttons):
            button = Button(rom_frame, text="", width=BUTTON_WIDTH, state=DISABLED, takefocus=False)
            button.pack(side=LEFT)
            button.lower()

        rom_frame.pack(fill=X)

        return rom_entry

    def add_project_fields_to_frame(self, text_string_name, frame):
        project_frame = tkinter.ttk.Frame(frame)

        label = Label(project_frame, width=LABEL_WIDTH, justify=RIGHT)
        label.pack(side=LEFT)
        self.guistrings.register_callback(lambda: label.configure(text="{}:".format(self.guistrings.get(text_string_name))))
        project_entry = Entry(project_frame)
        project_entry.pack(side=LEFT, fill=BOTH, expand=1, padx=1)
        self.components.append(project_entry)

        def browse_tmp():
            browse_for_project(self.root, project_entry, save=True)

        def open_tmp():
            open_folder(project_entry)

        def edit_tmp():
            self.open_ebprojedit(project_entry)

        button = Button(project_frame, command=browse_tmp, width=BUTTON_WIDTH)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "browse")
        self.components.append(button)

        button = Button(project_frame, command=open_tmp, width=BUTTON_WIDTH)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "open_text")
        self.components.append(button)

        button = Button(project_frame, command=edit_tmp, width=BUTTON_WIDTH)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "edit")
        self.components.append(button)

        project_frame.pack(fill=X, expand=1)

        return project_entry

    def add_patch_fields_to_frame(self, text_string_name, frame, save=False):
        patch_frame = tkinter.ttk.Frame(frame)

        label = Label(patch_frame, width=LABEL_WIDTH, justify=RIGHT)
        label.pack(side=LEFT)
        self.guistrings.register_callback(lambda: label.configure(text="{}:".format(self.guistrings.get(text_string_name))))
        patch_entry = Entry(patch_frame)
        patch_entry.pack(side=LEFT, fill=BOTH, expand=1, padx=1)
        self.components.append(patch_entry)

        def browse_tmp():
            browse_for_patch(self.root, patch_entry, save)

        button = Button(patch_frame, command=browse_tmp, width=BUTTON_WIDTH)
        button.pack(side=LEFT)
        self.guistrings.register_widget(button, "browse")
        self.components.append(button)

        button = Button(patch_frame, text="", width=BUTTON_WIDTH, state=DISABLED, takefocus=False)
        button.pack(side=LEFT)
        button.lower()

        patch_frame.pack(fill=BOTH, expand=1)

        return patch_entry

    def add_headered_field_to_frame(self, text_string_name, frame):
        patch_frame = tkinter.ttk.Frame(frame)

        headered_var = BooleanVar()
        headered_check = Checkbutton(patch_frame, variable=headered_var)
        headered_check.pack(
            side=LEFT, fill=BOTH, expand=1
        )
        self.guistrings.register_widget(headered_check, text_string_name)
        self.components.append(headered_check)
        patch_frame.pack(fill=BOTH, expand=1)

        return headered_var


def main():
    gui = CoilSnakeGui()
    sys.exit(gui.main())