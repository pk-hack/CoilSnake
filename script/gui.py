#!/usr/bin/env python

import os
import subprocess
import sys
sys.path.append(".")

from coilsnake.ui.gui import main
from coilsnake.ui.cli import main as cli_main

def perform_windows_noconsole_workaround(argv):
    return os.name == 'nt' and len(argv) == 1 and argv[0].endswith('.exe')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--gui':
        main()
    elif perform_windows_noconsole_workaround(sys.argv):
        # We're on Windows. Start ourselves but with no console window, and then exit.
        subprocess.Popen([sys.argv[0], '--gui'], creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)
    elif len(sys.argv) > 1:
        sys.exit(cli_main())
    else:
        main()