#! /usr/bin/env python
import os
from subprocess import Popen
from os.path import dirname, isdir, join
import yaml
from threading import Thread
from time import time
from traceback import print_exc
from platform import python_version
from Tkinter import *
import tkFileDialog
import tkMessageBox
from ttk import Progressbar

from coilsnake.model.common.blocks import Rom
from coilsnake.ui import cli, information
from coilsnake.ui.Fun import getTitle
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

    def getPrefsValue(self, key):
        try:
            return self._prefs[key]
        except KeyError:
            return ""

    def savePrefs(self):
        with open(self.PREFS_FNAME, "w") as f:
            yaml.dump(self._prefs, f, Dumper=yaml.CSafeDumper)

    def toggleTitles(self):
        self._prefs["title"] = (~(self._prefs["title"])) | 1
        self.savePrefs()

    def aboutMenu(self):
        am = Toplevel(self._root)
        # Label(am, text="CoilSnake " + CoilSnake._VERSION,
        #        font=("Helvetica", 16)).pack(fill=X)
        photo = PhotoImage(file=os.path.join(ASSET_PATH, "images", "logo.gif"))
        photoLabel = Label(am, image=photo)
        photoLabel.photo = photo
        photoLabel.pack(fill='both', expand=1)

        Label(am,
              text=
              (("CoilSnake %s\n"
                + "Released on %s\n\n"
                + "Created by MrTenda\n"
                + "Logo art by Reg\n\n"
                + "With help from\n"
                + "  Penguin, Reg, H.S, Michael1,\n"
                + "  Mr. Accident, AnyoneEB, Goplat, Captain Bozo,\n"
                + "  and the rest of the PK Hack community.\n"
                + "\n"
                + "Running on Python %s") % (
                   information.VERSION,
                   information.RELEASE_DATE, python_version())),
              anchor="w", justify="left", bg="white", borderwidth=5,
              relief=GROOVE).pack(
            fill='both', expand=1)
        Button(am, text="Toggle Alternate Titles",
               command=self.toggleTitles).pack(fill=X)
        Button(am, text="Close", command=am.destroy).pack(fill=X)
        am.resizable(False, False)
        am.title("About CoilSnake %s" % information.VERSION)

    def setText(self, entry, str):
        entry.delete(0, END)
        entry.insert(0, str)
        entry.xview(END)

    def setEmulatorExe(self):
        self._prefs["Emulator"] = tkFileDialog.askopenfilename(
            parent=self._root,
            title="Select an Emulator Executable",
            initialfile=self.getPrefsValue("Emulator"))
        self.savePrefs()

    def setCccExe(self):
        self._prefs["CCC"] = tkFileDialog.askopenfilename(
            parent=self._root,
            title="Select the CCC Executable",
            initialfile=self.getPrefsValue("CCC"))
        self.savePrefs()

    def toggleErrorDetails(self):
        if self.getPrefsValue("ErrorDetails") == "1":
            self._prefs["ErrorDetails"] = "0"
        else:
            self._prefs["ErrorDetails"] = "1"

    def browseForRom(self, entry, save=False):
        if save:
            fname = tkFileDialog.asksaveasfilename(
                parent=self._root, title="Select an output ROM",
                filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        else:
            fname = tkFileDialog.askopenfilename(
                parent=self._root, title="Select a ROM",
                filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if len(fname) > 0:
            self.setText(entry, fname)

    def browseForProject(self, entry, save=False):
        fname = tkFileDialog.askdirectory(
            parent=self._root, title="Select a Project Directory",
            mustexist=(not save))
        self.setText(entry, fname)

    def runRom(self, entry):
        romFname = entry.get()
        if self.getPrefsValue("Emulator") == "":
            tkMessageBox.showerror(parent=self._root,
                                   title="Error",
                                   message="""Emulator executable not specified.
Please specify it in the Preferences menu.""")
        elif romFname != "":
            Popen([self.getPrefsValue("Emulator"), romFname])

    def resetConsole(self):
        self._console.delete(1.0, END)
        self._console.see(END)

    def doExport(self, romEntry, projEntry):
        if (romEntry.get() != "") and (projEntry.get() != ""):
            # Update the GUI
            self.resetConsole()
            self._exportB["state"] = DISABLED
            self._importB["state"] = DISABLED
            self._upgradeB["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["export_rom"] = romEntry.get()
            self._prefs["export_proj"] = projEntry.get()
            self.savePrefs()

            self._progBar["value"] = 0
            print "Initializing CoilSnake\n"
            self._cs = cli.CoilSnake()
            self._progBar.step(10)
            thread = Thread(target=self._doExportHelp,
                            args=(romEntry.get(), projEntry.get(),
                                  time(), ))
            thread.start()

    def _doExportHelp(self, rom, proj, startTime):
        try:
            if self._cs.romToProj(rom, proj):
                print "Done! (Took %0.2fs)" % (time() - startTime)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.getPrefsValue("ErrorDetails") == "1":
                print_exc()
        self._progBar["value"] = 0
        self._exportB["state"] = NORMAL
        self._importB["state"] = NORMAL
        self._upgradeB["state"] = NORMAL
        del self._cs

    def doImport(self, projEntry, cleanRomEntry, romEntry):
        if self.getPrefsValue("CCC") == "":
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
            self._upgradeB["state"] = DISABLED
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

            self._console.delete(1.0, END)
            # Run CoilSnake as usual
            print "Initializing CoilSnake\n"
            self._cs = cli.CoilSnake()
            self._progBar.step(10)
            thread = Thread(target=self._doImportHelp,
                            args=(projDir, oldRom, newRom, time()))
            thread.start()

    def _doImportHelp(self, proj, oldRom, newRom, startTime):
        try:
            if self._cs.projToRom(proj, oldRom, newRom,
                                  self.getPrefsValue("CCC")):
                print "Done! (Took %0.2fs)" % (time() - startTime)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.getPrefsValue("ErrorDetails") == "1":
                print_exc()
        self._progBar["value"] = 0
        self._exportB["state"] = NORMAL
        self._importB["state"] = NORMAL
        self._upgradeB["state"] = NORMAL
        self._importRunB["state"] = NORMAL
        del self._cs

    def doUpgrade(self, romEntry, projEntry):
        if (romEntry.get() != "") and (projEntry.get() != ""):
            # Update the GUI
            self.resetConsole()
            self._exportB["state"] = DISABLED
            self._importB["state"] = DISABLED
            self._upgradeB["state"] = DISABLED
            # Save the fields to preferences
            self._prefs["upgrade_rom"] = romEntry.get()
            self._prefs["upgrade_proj"] = projEntry.get()
            self.savePrefs()

            self._progBar["value"] = 0
            print "Initializing CoilSnake\n"
            self._cs = cli.CoilSnake()
            self._progBar.step(10)
            thread = Thread(target=self._doUpgradeHelp,
                            args=(romEntry.get(), projEntry.get(),
                                  time(), ))
            thread.start()

    def _doUpgradeHelp(self, rom, proj, startTime):
        try:
            if self._cs.upgradeProject(rom, proj):
                print "Done! (Took %0.2fs)" % (time() - startTime)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.getPrefsValue("ErrorDetails") == "1":
                print_exc()
        self._progBar["value"] = 0
        self._exportB["state"] = NORMAL
        self._importB["state"] = NORMAL
        self._upgradeB["state"] = NORMAL
        del self._cs

    def expandRom(self, ex=False):
        r = Rom.Rom()
        fname = tkFileDialog.askopenfilename(
            parent=self._root, title="Select a ROM to expand",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if len(fname) > 0:
            r.load(fname)
            if (not ex and len(r) >= 0x400000) or (ex and (len(r) >= 0x600000)):
                tkMessageBox.showerror(
                    parent=self._root,
                    title="Error",
                    message="This ROM is already expanded.")
            else:
                if ex:
                    r.expand(0x600000)
                else:
                    r.expand(0x400000)
                r.save(fname)
                del r
                tkMessageBox.showinfo(
                    parent=self._root,
                    title="Expansion Successful",
                    message="Your ROM was expanded.")

    def expandRomEx(self):
        self.expandRom(ex=True)

    def addHeaderRom(self):
        fname = tkFileDialog.askopenfilename(
            parent=self._root, title="Select a ROM to which to add a header",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if len(fname) > 0:
            with Rom() as rom:
                rom.from_file(fname)
                rom.add_header()
                rom.to_file(fname)
            tkMessageBox.showinfo(
                parent=self._root,
                title="Header Addition Successful",
                message="Your ROM was given a header.")

    def stripHeaderRom(self):
        fname = tkFileDialog.askopenfilename(
            parent=self._root, title="Select a ROM from which to remove a header",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if len(fname) > 0:
            with Rom() as rom:
                rom.from_file(fname)
                rom.to_file(fname)
            tkMessageBox.showinfo(
                parent=self._root,
                title="Header Remove Successful",
                message="Your ROM's header was removed.")

    def extractEarthBoundDialogue(self):
        if not CCScriptWriter:
            tkMessageBox.showerror(
                "CCScriptWriter Not Installed",
                "You need to place CCScriptWriter.py in the tools/CCScriptWriter folder.",
                parent=self._root)
            return
        romName = tkFileDialog.askopenfilename(
            parent=self._root, title="Select an EarthBound ROM from which to extract the dialogue text",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
        if not romName:
            return
        r = Rom()
        r.from_file(romName)
        if r.type() != "Earthbound":
            tkMessageBox.showerror(
                "Invalid EarthBound ROM",
                "You have specified an invalid EarthBound ROM.",
                parent=self._root)
            return
        del r
        projectName = tkFileDialog.askopenfilename(
            parent=self._root, title="Select a CoilSnake project to modify",
            filetypes=[('CoilSnake Project', 'Project.snake')])
        if not projectName:
            return
        projectDir = join(dirname(projectName), "ccscript")
        thread = Thread(
            target=self._runCCScriptWriter,
            args=(
                projectDir,
                romName))
        thread.start()

    def _runCCScriptWriter(self, projectDir, romName):
        print("CCScriptWriter v1.1")
        start = time()
        romFile = open(romName, "rb")
        try:
            ccsw = CCScriptWriter(romFile, projectDir, False)
            ccsw.loadDialogue(True)
            ccsw.processDialogue()
            ccsw.outputDialogue(True)
        except Exception as inst:
            print "\nError:", str(inst)
            if self.getPrefsValue("ErrorDetails") == "1":
                print_exc()
        else:
            print "Complete. Time: {:.2f}s".format(float(time() - start))
            tkMessageBox.showinfo(
                title="Dialogue Extraction Successful",
                message="Successfully extracted EarthBound dialogue.",
                parent=self._root)
        finally:
            romFile.close()

    def main(self):
        self._root = Tk()
        if self.getPrefsValue("title") == 1:
            self._root.wm_title(getTitle() + " " + information.VERSION)
        else:
            self._root.wm_title("CoilSnake" + " " + information.VERSION)
            if self.getPrefsValue("title") == 0:
                self._prefs["title"] = 1
                self.savePrefs()

        menuBar = Menu(self._root)
        # Preferences pulldown menu
        prefMenu = Menu(menuBar, tearoff=0)
        prefMenu.add_command(label="CCScript Compiler Executable",
                             command=self.setCccExe)
        prefMenu.add_command(label="Emulator Executable",
                             command=self.setEmulatorExe)
        prefMenu.add_command(label="Toggle Error Details",
                             command=self.toggleErrorDetails)
        menuBar.add_cascade(label="Preferences", menu=prefMenu)
        # Tools pulldown menu
        toolsMenu = Menu(menuBar, tearoff=0)
        toolsMenu.add_command(label="Expand ROM to 32 MBit",
                              command=self.expandRom)
        toolsMenu.add_command(label="Expand ROM to 48 MBit",
                              command=self.expandRomEx)
        toolsMenu.add_command(label="Add Header to ROM",
                              command=self.addHeaderRom)
        toolsMenu.add_command(label="Remove Header from ROM",
                              command=self.stripHeaderRom)
        toolsMenu.add_command(label="Extract EarthBound Dialogue to Project",
                              command=self.extractEarthBoundDialogue)
        menuBar.add_cascade(label="Tools", menu=toolsMenu)
        # Help menu
        helpMenu = Menu(menuBar, tearoff=0)
        helpMenu.add_command(label="About", command=self.aboutMenu)
        menuBar.add_cascade(label="Help", menu=helpMenu)

        self._root.config(menu=menuBar)

        # Left side: Export
        a = Label(self._root, text="ROM -> New Project", justify=CENTER).grid(
            row=0, column=1, columnspan=1)
        # ROM file selector
        Label(self._root, text="Input ROM:").grid(
            row=1, column=0, sticky=E)
        inRom = Entry(self._root)
        inRom.grid(row=1, column=1)
        self.setText(inRom, self.getPrefsValue("export_rom"))

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
        self.setText(outProj, self.getPrefsValue("export_proj"))

        def browseTmp():
            self.browseForProject(outProj, save=True)

        Button(self._root, text="Browse...",
               command=browseTmp).grid(row=2, column=2, sticky=W)
        # Export Button

        def exportTmp():
            self.doExport(inRom, outProj)

        self._exportB = Button(self._root, text="Decompile", command=exportTmp)
        self._exportB.grid(row=3, column=1, columnspan=1, sticky=W + E)

        # Right side: Import
        Label(self._root, text="Project -> New ROM").grid(
            row=0, column=5, columnspan=1)
        # Base ROM file selector
        Label(self._root, text="Base Expanded ROM:").grid(
            row=1, column=4, sticky=E)
        baseRom = Entry(self._root)
        baseRom.grid(row=1, column=5)
        self.setText(baseRom, self.getPrefsValue("import_baserom"))

        def browseTmp():
            self.browseForRom(baseRom)

        def runTmp():
            self.runRom(baseRom)

        Button(self._root, text="Browse...",
               command=browseTmp).grid(row=1, column=6)
        Button(self._root, text="Run",
               command=runTmp).grid(row=1, column=7, sticky=E + W)
        # Project dir selector
        Label(self._root, text="Project Directory:").grid(
            row=2, column=4, sticky=E)
        inProj = Entry(self._root, text=self.getPrefsValue("import_proj"))
        inProj.grid(row=2, column=5)
        self.setText(inProj, self.getPrefsValue("import_proj"))

        def browseTmp():
            self.browseForProject(inProj, save=False)

        Button(self._root, text="Browse...",
               command=browseTmp).grid(row=2, column=6)
        # ROM file selector
        Label(self._root, text="Output ROM:").grid(
            row=3, column=4, sticky=E)
        outRom = Entry(self._root, text=self.getPrefsValue("import_rom"))
        outRom.grid(row=3, column=5)
        self.setText(outRom, self.getPrefsValue("import_rom"))

        def browseTmp():
            self.browseForRom(outRom, save=True)

        def runTmp():
            self.runRom(outRom)

        Button(self._root, text="Browse...",
               command=browseTmp).grid(row=3, column=6)
        self._importRunB = Button(self._root, text="Run",
                                  command=runTmp)
        self._importRunB.grid(row=3, column=7, sticky=E + W)
        # Import Button

        def importTmp():
            self.doImport(inProj, baseRom, outRom)

        self._importB = Button(self._root, text="Compile", command=importTmp)
        self._importB.grid(row=4, column=5, columnspan=1, sticky=W + E)

        # Upgrade
        a = Label(self._root, text="Upgrade Project", justify=CENTER).grid(
            row=5, column=1, columnspan=1)
        # ROM file selector
        Label(self._root, text="Base ROM:").grid(
            row=6, column=0, sticky=E)
        upgradeRom = Entry(self._root)
        upgradeRom.grid(row=6, column=1)
        self.setText(upgradeRom, self.getPrefsValue("upgrade_rom"))

        def browseTmp():
            self.browseForRom(upgradeRom)

        def runTmp():
            self.runRom(upgradeRom)

        Button(self._root, text="Browse...",
               command=browseTmp).grid(row=6, column=2, sticky=W)
        Button(self._root, text="Run",
               command=runTmp).grid(row=6, column=3, sticky=W)
        # Project dir selector
        Label(self._root, text="Project Directory:").grid(
            row=7, column=0, sticky=E)
        upgradeProj = Entry(self._root)
        upgradeProj.grid(row=7, column=1)
        self.setText(upgradeProj, self.getPrefsValue("upgrade_proj"))

        def browseTmp():
            self.browseForProject(upgradeProj, save=True)

        Button(self._root, text="Browse...",
               command=browseTmp).grid(row=7, column=2, sticky=W)
        # Upgrade Button

        def upgradeTmp():
            self.doUpgrade(upgradeRom, upgradeProj)

        self._upgradeB = Button(self._root, text="Upgrade", command=upgradeTmp)
        self._upgradeB.grid(row=8, column=1, columnspan=1, sticky=W + E)

        # Progress bar
        self._progBar = Progressbar(self._root,
                                    orient=HORIZONTAL, mode='determinate')
        self._progBar.grid(row=9, column=0, columnspan=8, sticky=W + E)

        # Console
        consoleFrame = Frame(self._root)
        consoleFrame.grid(row=10, column=0, columnspan=8, sticky=W + E)
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

            def write(self, str):
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


def main():
    csf = CoilSnakeFrontend()
    sys.exit(csf.main())


if __name__ == '__main__':
    main()