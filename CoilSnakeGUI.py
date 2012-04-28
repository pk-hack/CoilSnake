#! /usr/bin/env python

from subprocess import Popen
from os import listdir
import yaml
from shutil import copyfile
from threading import Thread
from time import time
from traceback import print_exc

from Tkinter import *
import tkFileDialog, tkMessageBox
from ttk import Progressbar

import CoilSnake
from modules import Rom, Progress
from modules.Fun import getTitle
from tools import EbRomExpander

_version = "0.1"
_releaseDate = "?/?/??"

class CoilSnakeFrontend:
    PREFS_FNAME = "prefs.yml"
    def __init__(self):
        try:
            with open(self.PREFS_FNAME, 'r') as f:
                self._prefs = yaml.load(f, Loader=yaml.CSafeLoader)
        except IOError:
            self._prefs = {
                    'Emulator': "",
                    'CCC': "",
                    'import_proj': "",
                    'import_baserom': "",
                    'import_rom': "",
                    'export_proj': "",
                    'export_rom': "",
                    'title': 0,
                    }
    def savePrefs(self):
        with open(self.PREFS_FNAME, "w") as f:
            yaml.dump(self._prefs, f, Dumper=yaml.CSafeDumper)
    def toggleTitles(self):
        self._prefs["title"] = (~(self._prefs["title"]))|1
        self.savePrefs()
    def aboutMenu(self):
        am = Toplevel(self._root)
        Label(am, text="CoilSnake " + _version,
                font=("Helvetica", 16)).pack(fill=X)
        Label(am,
                text=
                "Released on " + _releaseDate + ".\n\n"
                + "Created by MrTenda.\n\n"
                + "With help from\n"
                + "  Penguin, Mr. Accident, Goplat,\n"
                + "  AnyoneEB, Captain Bozo, JeffMan,\n"
                + "  and the rest of the PK Hack community.",
                anchor="w",justify="left",bg="white",borderwidth=5,
                relief=GROOVE).pack(
                        fill='both', expand=1)
        Button(am, text="Toggle Alternate Titles",
                command=self.toggleTitles).pack(fill=X)
        Button(am, text="Close", command=am.destroy).pack(fill=X)
        am.resizable(False, False)
        am.title("About")
    def setText(self, entry, str):
        entry.delete(0, END)
        entry.insert(0, str)
        entry.xview(END)
    def setEmulatorExe(self):
        self._prefs["Emulator"] = tkFileDialog.askopenfilename(
                parent=self._root,
                title="Select an Emulator Executable",
                initialfile=self._prefs["Emulator"])
        self.savePrefs()
    def setCccExe(self):
        self._prefs["CCC"] = tkFileDialog.askopenfilename(
                parent=self._root,
                title="Select the CCC Executable",
                initialfile=self._prefs["CCC"])
        self.savePrefs()
    def browseForRom(self, entry, save=False):
        if save:
            fname = tkFileDialog.asksaveasfilename(
                    parent=self._root, title="Select an output ROM",
                    filetypes=[('SNES ROMs','*.smc'), ('All files','*.*')])
        else:
            fname = tkFileDialog.askopenfilename(
                    parent=self._root, title="Select a ROM",
                    filetypes=[('SNES ROMs','*.smc'), ('All files','*.*')])
        self.setText(entry, fname)
    def browseForProject(self, entry, save=False):
        fname = tkFileDialog.askdirectory(
                parent=self._root, title="Select a Project Directory",
                mustexist=(not save))
        self.setText(entry, fname)
    def runRom(self, entry):
        romFname = entry.get()
        if self._prefs["Emulator"] == "":
            tkMessageBox.showerror(parent=self._root,
                    title="Error",
                    message="""Emulator executable not specified.
Please specify it in the Preferences menu.""")
        elif romFname != "":
            Popen([self._prefs["Emulator"], romFname])
    def resetConsole(self):
        self._console.delete(1.0, END)
        self._console.see(END)
    def doExport(self, romEntry, projEntry):
        if (romEntry.get() != "") and (projEntry.get() != ""):
            # Update the GUI
            self.resetConsole()
            self._exportB["state"] = DISABLED
            self._importB["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["export_rom"] = romEntry.get()
            self._prefs["export_proj"] = projEntry.get()
            self.savePrefs()

            self._progBar["value"] = 0
            print "Initializing CoilSnake\n"
            self._cs = CoilSnake.CoilSnake()
            self._progBar.step(10)
            thread = Thread(target=self._doExportHelp,
                    args=(romEntry.get(), projEntry.get()+"/Project.snake",
                        time(), ))
            thread.start()
    def _doExportHelp(self, rom, proj, startTime):
        try:
            self._cs.romToProj(rom, proj)
            print "Done! (Took %0.2fs)" % (time()-startTime)
        except Exception as inst:
            print "\nError! Something went wrong:"
            print_exc()
        self._progBar["value"] = 0
        self._exportB["state"] = NORMAL
        self._importB["state"] = NORMAL
        del(self._cs)
    def doImport(self, projEntry, cleanRomEntry, romEntry):
        if self._prefs["CCC"] == "":
            tkMessageBox.showerror(parent=self._root,
                    title="Error",
                    message="""CCScript Compiler executable not specified.
Please specify it in the Preferences menu.""")
        elif ((projEntry.get() != "") and (cleanRomEntry.get() != "")
                and (romEntry.get() != "")):
            # Update the GUI
            self.resetConsole()
            self._exportB["state"] = DISABLED
            self._importB["state"] = DISABLED
            self._importRunB["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["import_proj"] = projEntry.get()
            self._prefs["import_baserom"] = cleanRomEntry.get()
            self._prefs["import_rom"] = romEntry.get()
            self.savePrefs()

            oldRom = cleanRomEntry.get()
            newRom = romEntry.get()
            projDir = projEntry.get()
            # Reset the progress bar
            self._progBar["value"] = 0
            # Copy the clean rom to the output rom
            self._console.delete(1.0, END)
            print "Copying ROM"
            copyfile(oldRom, newRom)
            self._progBar.step(2)
            # Get a list of the script filenames in projDir/ccscript
            scriptFnames = [ projDir + "/ccscript/" + x 
                    for x in listdir(projDir + "/ccscript")
                    if x.endswith('.ccs') ]
            # Compile scripts using the CCC, and put the data at $F00000
            print "Calling external CCScript Compiler"
            process = Popen(
                    [self._prefs["CCC"], "-n", "-o", newRom, "-s", "F00000",
                        "--summary", projDir + "/ccscript/summary.txt"] +
                    scriptFnames)
            process.wait()
            self._progBar.step(4)
            # Run CoilSnake as usual
            print "Initializing CoilSnake\n"
            self._cs = CoilSnake.CoilSnake()
            self._progBar.step(4)
            thread = Thread(target=self._doImportHelp,
                    args=(projDir+"/Project.snake", newRom, time()))
            thread.start()
    def _doImportHelp(self, proj, rom, startTime):
        try:
            self._cs.projToRom(proj, rom, rom)
            print "Done! (Took %0.2fs)" % (time()-startTime)
        except Exception as inst:
            print "\nError! Something went wrong:"
            print_exc()
        self._progBar["value"] = 0
        self._exportB["state"] = NORMAL
        self._importB["state"] = NORMAL
        self._importRunB["state"] = NORMAL
        del(self._cs)
    def expandRom(self, ex=False):
        r = Rom.Rom('romtypes.yaml')
        fname = tkFileDialog.askopenfilename(
                    parent=self._root, title="Select a ROM to expand",
                    filetypes=[('SNES ROMs','*.smc'), ('All files','*.*')])
        r.load(fname)
        EbRomExpander.expandRom(r, ex)
        r.save(fname)
        del(r)
        tkMessageBox.showinfo("Expansion Successful",
                "Your ROM was expanded.")
    def expandRomEx(self):
        self.expandRom(ex=True)
    def main(self):
        self._root = Tk()
        if self._prefs["title"] == 1:
            self._root.wm_title(getTitle() + " " + _version)
        else:
            self._root.wm_title("CoilSnake" + " " + _version)
            if self._prefs["title"] == 0:
                self._prefs["title"] = 1
                self.savePrefs()

        menuBar = Menu(self._root)
        # Preferences pulldown menu
        prefMenu = Menu(menuBar, tearoff=0)
        prefMenu.add_command(label="CCScript Compiler Executable",
                command=self.setCccExe)
        prefMenu.add_command(label="Emulator Executable",
                command=self.setEmulatorExe)
        menuBar.add_cascade(label="Preferences", menu=prefMenu)
        # Tools pulldown menu
        toolsMenu = Menu(menuBar, tearoff=0)
        toolsMenu.add_command(label="Expand ROM to 32 MBit",
                command=self.expandRom)
        toolsMenu.add_command(label="Expand ROM to 48 MBit",
                command=self.expandRomEx)
        menuBar.add_cascade(label="Tools", menu=toolsMenu)
        # Help menu
        helpMenu = Menu(menuBar, tearoff=0)
        helpMenu.add_command(label="About", command=self.aboutMenu)
        menuBar.add_cascade(label="Help", menu=helpMenu)

        self._root.config(menu=menuBar)


        # Left side: Export
        a=Label(self._root, text="ROM -> New Project",justify=CENTER).grid(
                row=0, column=1, columnspan=1)
        # ROM file selector
        Label(self._root, text="Input ROM:").grid(
                row=1, column=0, sticky=E)
        inRom = Entry(self._root)
        inRom.grid(row=1, column=1)
        self.setText(inRom, self._prefs["export_rom"])
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
        self.setText(outProj, self._prefs["export_proj"])
        def browseTmp():
            self.browseForProject(outProj, save=True)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=2, column=2, sticky=W)
        # Export Button
        def exportTmp():
            self.doExport(inRom, outProj)
        self._exportB = Button(self._root, text="Export", command=exportTmp)
        self._exportB.grid(row=4, column=1, columnspan=1, sticky=W+E)

        # Right side: Import
        Label(self._root, text="Project -> New ROM").grid(
                row=0, column=5, columnspan=1)
        # Base ROM file selector
        Label(self._root, text="Base Expanded ROM:").grid(
                row=1, column=4, sticky=E)
        baseRom = Entry(self._root)
        baseRom.grid(row=1, column=5)
        self.setText(baseRom, self._prefs["import_baserom"])
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
        inProj = Entry(self._root, text=self._prefs["import_proj"])
        inProj.grid(row=2, column=5)
        self.setText(inProj, self._prefs["import_proj"])
        def browseTmp():
            self.browseForProject(inProj, save=False)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=2, column=6)
        # ROM file selector
        Label(self._root, text="Output ROM:").grid(
                row=3, column=4, sticky=E)
        outRom = Entry(self._root, text=self._prefs["import_rom"])
        outRom.grid(row=3, column=5)
        self.setText(outRom, self._prefs["import_rom"])
        def browseTmp():
            self.browseForRom(outRom, save=True)
        def runTmp():
            self.runRom(outRom)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=3, column=6)
        self._importRunB = Button(self._root, text="Run",
                command=runTmp)
        self._importRunB.grid(row=3, column=7, sticky=W)
        # Import Button
        def importTmp():
            self.doImport(inProj, baseRom, outRom)
        self._importB = Button(self._root, text="Import", command=importTmp)
        self._importB.grid(row=4, column=5, columnspan=1, sticky=W+E)

        # Progress bar
        self._progBar = Progressbar(self._root,
                orient=HORIZONTAL, mode='determinate')
        self._progBar.grid(row=5, column=0, columnspan=8, sticky=W+E)
        def updProg(dp):
            Progress.__updateProgress__(dp)
            # Note: The number of modules is hardcoded here as "16"
            self._progBar.step((90.0/16) * (dp/100.0))
        Progress.updateProgress = updProg

        # Console
        consoleFrame = Frame(self._root)
        consoleFrame.grid(row=6, column=0, columnspan=8, sticky=W+E)
        s = Scrollbar(consoleFrame)
        self._console = Text(consoleFrame, width=80, height=6)
        s.pack(side=RIGHT, fill=Y)
        self._console.pack(fill=X)
        s.config(command=self._console.yview)
        self._console.config(yscrollcommand=s.set)

        # Stdout Redirector
        class StdoutRedirector:
            def __init__(self, textArea):
                self._tA = textArea
            def write(self,str):
                if str.startswith("\b\b\b\b\b\b\b\b"):
                    self._tA.delete("end-9c", "end")
                    self._tA.insert(END, str[8:])
                else:
                    self._tA.insert(END, str)
                self._tA.see(END)
            def flush(self):
                pass
        self._consoleStdout = StdoutRedirector(self._console)
        sys.stdout = self._consoleStdout
        sys.stderr = self._consoleStdout

        self._root.mainloop()

if (__name__ == '__main__'):
    csf = CoilSnakeFrontend()
    sys.exit(csf.main())
