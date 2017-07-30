from tkinter.constants import END
import os
import subprocess
import tkinter.filedialog
import tkinter.messagebox
import sys
import shutil

from coilsnake.model.common.blocks import Rom
from coilsnake.ui.common import expand, add_header, strip_header


PATCH_FILETYPES = [('IPS patches', '*.ips'), ('EBP patches', '*.ebp'), ('All files', '*.*')]
ROM_FILETYPES = [('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')]


def expand_rom(root):
    filename = tkinter.filedialog.askopenfilename(
        parent=root,
        initialdir=os.path.expanduser("~"),
        title="Select a ROM to expand",
        filetypes=ROM_FILETYPES)
    if filename:
        returntest = expand(filename)
        if not returntest:
            tkinter.messagebox.showerror(
                parent=root,
                title="Error",
                message="This ROM is already expanded.")
        else:
            tkinter.messagebox.showinfo(
                parent=root,
                title="Expansion Successful",
                message="Your ROM was expanded. (32MBits/4MB)")


def expand_rom_ex(root):
    filename = tkinter.filedialog.askopenfilename(
        parent=root,
        initialdir=os.path.expanduser("~"),
        title="Select a ROM to expand",
        filetypes=ROM_FILETYPES)
    if filename:
        returntest = expand(filename, ex=True)
        if not returntest:
            tkinter.messagebox.showerror(
                parent=root,
                title="Error",
                message="This ROM is already expanded.")
        else:
            tkinter.messagebox.showinfo(
                parent=root,
                title="Expansion Successful",
                message="Your ROM was expanded. (48MBits/6MB)")


def add_header_to_rom(root):
    filename = tkinter.filedialog.askopenfilename(
        parent=root,
        initialdir=os.path.expanduser("~"),
        title="Select a ROM to which to add a header",
        filetypes=ROM_FILETYPES)
    if filename:
        returntest = add_header(filename)
        if returntest:
            tkinter.messagebox.showinfo(
                parent=root,
                title="Header Addition Successful",
                message="Your ROM was given a header.")
        else:
            tkinter.messagebox.showinfo(
                parent=root,
                title="Header Addition Failed",
                message="Invalid ROM.")

def strip_header_from_rom(root):
    filename = tkinter.filedialog.askopenfilename(
        parent=root,
        initialdir=os.path.expanduser("~"),
        title="Select a ROM from which to remove a header",
        filetypes=ROM_FILETYPES)
    if filename:
        returntest = strip_header(filename)
        if returntest:
            tkinter.messagebox.showinfo(
                parent=root,
                title="Header Removal Successful",
                message="Your ROM's header was removed.")
        else:
            tkinter.messagebox.showinfo(
                parent=root,
                title="Header Removal Failed",
                message="Invalid ROM.")


def set_entry_text(entry, text):
    entry.delete(0, END)
    entry.insert(0, text)
    entry.xview(len(text)-1)


def browse_for_patch(root, entry, save=False):
    if save:
        filename = tkinter.filedialog.asksaveasfilename(
            parent=root,
            initialdir=os.path.dirname(entry.get()) or os.path.expanduser("~"),
            title="Select an output patch",
            filetypes=PATCH_FILETYPES)
    else:
        filename = tkinter.filedialog.askopenfilename(
            parent=root,
            initialdir=os.path.dirname(entry.get()) or os.path.expanduser("~"),
            title="Select a patch",
            filetypes=PATCH_FILETYPES)
    if filename:
        set_entry_text(entry, filename)
        entry.xview(END)


def browse_for_rom(root, entry, save=False):
    if save:
        filename = tkinter.filedialog.asksaveasfilename(
            parent=root,
            initialdir=os.path.dirname(entry.get()) or os.path.expanduser("~"),
            title="Select an output ROM",
            filetypes=ROM_FILETYPES)
    else:
        filename = tkinter.filedialog.askopenfilename(
            parent=root,
            initialdir=os.path.dirname(entry.get()) or os.path.expanduser("~"),
            title="Select a ROM",
            filetypes=ROM_FILETYPES)
    if filename:
        set_entry_text(entry, filename)
        entry.xview(len(filename)-1)


def browse_for_project(root, entry, save=False):
    filename = tkinter.filedialog.askdirectory(
        parent=root,
        initialdir=os.path.dirname(entry.get()) or os.path.expanduser("~"),
        title="Select a Project Directory",
        mustexist=(not save))
    if filename:
        set_entry_text(entry, filename)
        entry.xview(len(filename)-1)


def open_folder(entry):
    path = entry.get()
    if not path:
        return
    path = os.path.normpath(path)

    if sys.platform == 'darwin':
        subprocess.check_call(['open', path])
    elif sys.platform == 'linux2':
        subprocess.check_call(['gnome-open', path])
    elif sys.platform == 'win32':
        subprocess.call(['explorer', path])


def find_system_java_exe():
    if "JAVA_HOME" in os.environ:
        java_exe = os.path.join(os.environ["JAVA_HOME"], "bin", "javaw.exe")
        if os.path.isfile(java_exe):
            return java_exe

        java_exe = os.path.join(os.environ["JAVA_HOME"], "bin", "java.exe")
        if os.path.isfile(java_exe):
            return java_exe

        java_exe = os.path.join(os.environ["JAVA_HOME"], "bin", "java")
        if os.path.isfile(java_exe):
            return java_exe

    java_exe = shutil.which("javaw")
    if java_exe:
        return java_exe

    java_exe = shutil.which("java")
    if java_exe:
        return java_exe

    return None