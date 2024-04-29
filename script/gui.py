#!/usr/bin/env python

import sys
sys.path.append(".")

from coilsnake.ui.gui import main
from coilsnake.ui.cli import main as cli_main

if __name__ == '__main__':
    # if we recieve arguments, run the cli instead
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    else:
        main()
