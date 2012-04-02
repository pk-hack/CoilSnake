#! /usr/bin/env python

from subprocess import Popen
import os
import yaml
import shutil
import threading
import time

from Tkinter import *
import tkFileDialog, tkMessageBox
from ttk import Progressbar

from CoilSnake import CoilSnake

_version = "0.1"

class CoilSnakeFrontend:
    PREFS_FNAME = "prefs.yml"
    def __init__(self):
        try:
            with open(self.PREFS_FNAME, 'r') as f:
                self._prefs = yaml.load(f)
        except IOError:
            self._prefs = {
                    'Emulator': "",
                    'CCC': "",
                    'export_proj': "",
                    'export_baserom': "",
                    'export_rom': "",
                    'import_proj': "",
                    'import_rom': ""
                    }
    def savePrefs(self):
        with open(self.PREFS_FNAME, "w") as f:
            yaml.dump(self._prefs, f)
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
    def doImport(self, romEntry, projEntry):
        if (romEntry.get() != "") and (projEntry.get() != ""):
            # Update the GUI
            self._importB["state"] = DISABLED
            self._exportB["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["import_rom"] = romEntry.get()
            self._prefs["import_proj"] = projEntry.get()
            self.savePrefs()

            self._progBar["value"] = 0
            print "Initializing CoilSnake\n"
            self._cs = CoilSnake()
            self._progBar.step(10)
            thread = threading.Thread(target=self._doImportHelp,
                    args=(romEntry.get(), projEntry.get()+"/Project.csproj",
                        time.time(), ))
            thread.start()
    def _doImportHelp(self, rom, proj, startTime):
        self._cs.romToProj(rom, proj, self._progBar, 90.0)
        self._importB["state"] = NORMAL
        self._exportB["state"] = NORMAL
        print "Done! (Took %0.2fs)" % (time.time()-startTime)
        del(self._cs)
    def doExport(self, projEntry, cleanRomEntry, romEntry):
        if self._prefs["CCC"] == "":
            tkMessageBox.showerror(parent=self._root,
                    title="Error",
                    message="""CCScript Compiler executable not specified.
Please specify it in the Preferences menu.""")
        elif ((projEntry.get() != "") and (cleanRomEntry.get() != "")
                and (romEntry.get() != "")):
            # Update the GUI
            self._importB["state"] = DISABLED
            self._exportB["state"] = DISABLED
            self._exportRunB["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["export_proj"] = projEntry.get()
            self._prefs["export_baserom"] = cleanRomEntry.get()
            self._prefs["export_rom"] = romEntry.get()
            self.savePrefs()

            oldRom = cleanRomEntry.get()
            newRom = romEntry.get()
            projDir = projEntry.get()
            # Reset the progress bar
            self._progBar["value"] = 0
            # Copy the clean rom to the output rom
            self._console.delete(1.0, END)
            print "Copying ROM"
            shutil.copyfile(oldRom, newRom)
            self._progBar.step(10)
            # Get a list of the script filenames in projDir/ccscript
            scriptFnames = [ projDir + "/ccscript/" + x 
                    for x in os.listdir(projDir + "/ccscript")
                    if x.endswith('.ccs') ]
            # Compile scripts using the CCC, and put the data at $F00000
            print "Calling external CCScript Compiler"
            process = Popen(
                    [self._prefs["CCC"], "-n", "-o", newRom, "-s", "F00000",
                        "--summary", projDir + "/ccscript/summary.txt"] +
                    scriptFnames)
            process.wait()
            self._progBar.step(10)
            # Run CoilSnake as usual
            #self._cs.projToRom(projDir + "/Project.csproj",
            #        newRom, newRom)
            print "Initializing CoilSnake\n"
            self._cs = CoilSnake()
            self._progBar.step(10)
            thread = threading.Thread(target=self._doExportHelp,
                    args=(projDir+"/Project.csproj", newRom, time.time()))
            thread.start()
    def _doExportHelp(self, proj, rom, startTime):
        self._cs.projToRom(proj, rom, rom, self._progBar, 70.0)
        self._importB["state"] = NORMAL
        self._exportB["state"] = NORMAL
        self._exportRunB["state"] = NORMAL
        print "Done! (Took %0.2fs)" % (time.time()-startTime)
        del(self._cs)
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
        self.setText(inRom, self._prefs["import_rom"])
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
        self.setText(outProj, self._prefs["import_proj"])
        def browseTmp():
            self.browseForProject(outProj, save=True)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=2, column=2)
        # Import Button
        def importTmp():
            self.doImport(inRom, outProj)
        self._importB = Button(self._root, text="Import", command=importTmp)
        self._importB.grid(row=4, column=1, columnspan=1, sticky=W+E)

        # Right side: Export
        Label(self._root, text="Project -> New ROM").grid(
                row=0, column=5, columnspan=1)
        # Base ROM file selector
        Label(self._root, text="Base Expanded ROM:").grid(
                row=1, column=4, sticky=E)
        baseRom = Entry(self._root)
        baseRom.grid(row=1, column=5)
        self.setText(baseRom, self._prefs["export_baserom"])
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
        inProj = Entry(self._root, text=self._prefs["export_proj"])
        inProj.grid(row=2, column=5)
        self.setText(inProj, self._prefs["export_proj"])
        def browseTmp():
            self.browseForProject(inProj, save=False)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=2, column=6)
        # ROM file selector
        Label(self._root, text="Output ROM:").grid(
                row=3, column=4, sticky=E)
        outRom = Entry(self._root, text=self._prefs["export_rom"])
        outRom.grid(row=3, column=5)
        self.setText(outRom, self._prefs["export_rom"])
        def browseTmp():
            self.browseForRom(outRom, save=True)
        def runTmp():
            self.runRom(outRom)
        Button(self._root, text="Browse...",
                command=browseTmp).grid(row=3, column=6)
        self._exportRunB = Button(self._root, text="Run",
                command=runTmp)
        self._exportRunB.grid(row=3, column=7, sticky=W)
        # Export Button
        def exportTmp():
            self.doExport(inProj, baseRom, outRom)
        self._exportB = Button(self._root, text="Export", command=exportTmp)
        self._exportB.grid(row=4, column=5, columnspan=1, sticky=W+E)

        # Progress bar
        self._progBar = Progressbar(self._root,
                orient=HORIZONTAL, mode='determinate')
        self._progBar.grid(row=5, column=0, columnspan=8, sticky=W+E)

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
                self._tA.insert(END, str)
                self._tA.see(END)
            def flush(self):
                pass
        self._consoleStdout = StdoutRedirector(self._console)
        sys.stdout = self._consoleStdout

        self._root.mainloop()

if (__name__ == '__main__'):
    csf = CoilSnakeFrontend()
    sys.exit(csf.main())
