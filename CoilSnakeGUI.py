#! /usr/bin/env python

from subprocess import Popen
import os
import yaml
import shutil

from Tkinter import *
import tkFileDialog, tkMessageBox

from CoilSnake import CoilSnake

_version = "0.1"

class CoilSnakeFrontend:
    PREFS_FNAME = "prefs.yml"
    def __init__(self):
        self._cs = CoilSnake()
        try:
            with open(self.PREFS_FNAME, 'r') as f:
                self._prefs = yaml.load(f)
        except IOError:
            self._prefs = {
                    'Emulator': None,
                    'CCC': None
                    }
    def setEmulatorExe(self):
        self._prefs["Emulator"] = tkFileDialog.askopenfilename(
                parent=self._root,
                title="Select an Emulator Executable",
                initialfile=self._prefs["Emulator"])
        with open(self.PREFS_FNAME, "w") as f:
            yaml.dump(self._prefs, f)
    def setCccExe(self):
        self._prefs["CCC"] = tkFileDialog.askopenfilename(
                parent=self._root,
                title="Select the CCC Executable",
                initialfile=self._prefs["CCC"])
        with open(self.PREFS_FNAME, "w") as f:
            yaml.dump(self._prefs, f)
    def browseForRom(self, entry, save=False):
        if save:
            fname = tkFileDialog.asksaveasfilename(
                    parent=self._root, title="Select an output ROM",
                    filetypes=[('SNES ROMs','*.smc'), ('All files','*.*')])
        else:
            fname = tkFileDialog.askopenfilename(
                    parent=self._root, title="Select a ROM",
                    filetypes=[('SNES ROMs','*.smc'), ('All files','*.*')])
        entry.delete(0, END)
        entry.insert(0, fname)
        entry.xview(END)
    def browseForProject(self, entry, save=False):
        fname = tkFileDialog.askdirectory(
                parent=self._root, title="Select a Project Directory",
                mustexist=(not save))
        entry.delete(0, END)
        entry.insert(0, fname)
        entry.xview(END)
    def runRom(self, entry):
        romFname = entry.get()
        if self._prefs["Emulator"] == None:
            tkMessageBox.showerror(parent=self._root,
                    title="Error",
                    message="""Emulator executable not specified.
Please specify it in the Preferences menu.""")
        elif romFname != "":
            Popen([self._prefs["Emulator"], romFname])
    def doImport(self, romEntry, projEntry):
        if (romEntry.get() != "") and (projEntry.get() != ""):
            self._cs.romToProj(romEntry.get(), projEntry.get() +
                    "/Project.csproj")
    def doExport(self, projEntry, cleanRomEntry, romEntry):
        if self._prefs["CCC"] == None:
            tkMessageBox.showerror(parent=self._root,
                    title="Error",
                    message="""CCScript Compiler executable not specified.
Please specify it in the Preferences menu.""")
        elif ((projEntry.get() != "") and (cleanRomEntry.get() != "")
                and (romEntry.get() != "")):
            oldRom = cleanRomEntry.get()
            newRom = romEntry.get()
            projDir = projEntry.get()
            # Copy the clean rom to the output rom
            shutil.copyfile(oldRom, newRom)
            # Get a list of the script filenames in projDir/ccscript
            scriptFnames = [ projDir + "/ccscript/" + x 
                    for x in os.listdir(projDir + "/ccscript")
                    if x.endswith('.ccs') ]
            # Compile scripts using the CCC, and put the data at $F00000
            process = Popen(
                    [self._prefs["CCC"], "-n", "-o", newRom, "-s", "F00000",
                        "--summary", projDir + "/ccscript/summary.txt"] +
                    scriptFnames)
            process.wait()
            # Run CoilSnake as usual
            self._cs.projToRom(projDir + "/Project.csproj",
                    newRom, newRom)
    def main(self):
        self._root = Tk()
        self._root.wm_title("CoilSnake")

        menuBar = Menu(self._root)
        # Preferences pulldown menu
        prefMenu = Menu(menuBar, tearoff=0)
        prefMenu.add_command(label="CCScript Compiler Executable",
                command=self.setCccExe)
        prefMenu.add_command(label="Emulator Executable",
                command=self.setEmulatorExe)
        menuBar.add_cascade(label="Preferences", menu=prefMenu)
        self._root.config(menu=menuBar)

        # Left side: Import
        a=Label(self._root, text="ROM -> New Project",justify=CENTER).grid(
                row=0, column=1, columnspan=1)
        # ROM file selector
        Label(self._root, text="Input ROM:").grid(
                row=1, column=0, sticky=E)
        inRom = Entry(self._root)
        inRom.grid(row=1, column=1)
        def browseTmp():
            self.browseForRom(inRom)
        def runTmp():
            self.runRom(inRom)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=1, column=2, sticky=W)
        Button(self._root, text="Run",
                command=runTmp).grid(row=1, column=3, sticky=W)
        # Project dir selector
        Label(self._root, text="Output Directory:").grid(
                row=2, column=0, sticky=E)
        outProj = Entry(self._root)
        outProj.grid(row=2, column=1)
        def browseTmp():
            self.browseForProject(outProj, save=True)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=2, column=2)
        # Import Button
        def importTmp():
            self.doImport(inRom, outProj)
        Button(self._root, text="Import", command=importTmp).grid(
                row=4, column=1, columnspan=1, sticky=W+E)

        # Right side: Export
        Label(self._root, text="Project -> New ROM").grid(
                row=0, column=5, columnspan=1)
        # Base ROM file selector
        Label(self._root, text="Base ROM:").grid(
                row=1, column=4, sticky=E)
        baseRom = Entry(self._root)
        baseRom.grid(row=1, column=5)
        def browseTmp():
            self.browseForRom(baseRom)
        def runTmp():
            self.runRom(baseRom)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=1, column=6)
        Button(self._root, text="Run",
                command=runTmp).grid(row=1, column=7, sticky=W)
        # Project dir selector
        Label(self._root, text="Project Directory:").grid(
                row=2, column=4, sticky=E)
        inProj = Entry(self._root)
        inProj.grid(row=2, column=5)
        def browseTmp():
            self.browseForProject(inProj, save=False)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=2, column=6)
        # ROM file selector
        Label(self._root, text="Output ROM:").grid(
                row=3, column=4, sticky=E)
        outRom = Entry(self._root)
        outRom.grid(row=3, column=5)
        def browseTmp():
            self.browseForRom(outRom, save=True)
        def runTmp():
            self.runRom(outRom)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=3, column=6)
        Button(self._root, text="Run",
                command=runTmp).grid(row=3, column=7, sticky=W)
        # Export Button
        def exportTmp():
            self.doExport(inProj, baseRom, outRom)
        Button(self._root, text="Export", command=exportTmp).grid(
                row=4, column=5, columnspan=1, sticky=W+E)

        self._root.mainloop()

if (__name__ == '__main__'):
    csf = CoilSnakeFrontend()
    sys.exit(csf.main())
