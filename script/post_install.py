#!/usr/bin/env python

import os
import sys
import stat


def setup_ccscript():
    # Remove the current directory from the front of sys.path
    old_sys_path = sys.path
    sys.path.pop(0)

    # Mark the installed "ccc" executable as executable by everyone
    from coilsnake.util.common.assets import ccc_file_name
    ccc_fname = ccc_file_name()
    print "Making {} executable".format(ccc_fname)
    os.chmod(ccc_fname, stat.S_IXOTH)

    # Restore the old sys.path
    sys.path = old_sys_path

if __name__ == "__main__":
    setup_ccscript()
