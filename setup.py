#!/usr/bin/python

######################################################################
# header

import os
import sys
from subprocess import call

def main():
    # setting up python interpreter history
    yorn = raw_input("Do you want a persistent Python interpreter history? [y]/n: ")
    if yorn == "" or yorn == "y":
        # check and download .pystartup
        if not os.path.isfile(os.path.expanduser("~") + "/.pystartup"):
            print "Cloning '~/.pystartup' from git ..."
            os.system("wget -q -P ~/ https://gist.githubusercontent.com/radziej/28185647752b647e1f4e/raw/216e66f27971dbe91686a6db71fb35e48a0c141d/.pystartup")
            print "Done."
            print "Exporting file to 'PYTHONSTARTUP' in the '~/.bashrc' ..."
        else:
            print "'~/.pystartup' already exists. Skipping."

        # export .pystartup to PYTHONSTARTUP
        with open(os.path.expanduser("~") + "/.bashrc", "a") as f:
             f.write("\n")
             f.write("# python presistent history\n")
             f.write("export PYTHONSTARTUP=${HOME}/.pystartup")

        print "Done."
    else:
        print "Not installing the persistent Python interpreter history"


    # setting up alias
    print " "
    yorn = raw_input("Do you want an alias to start brot with? [y]/n: ")
    if yorn == "" or yorn == "y":
        print "Setting up alias in '~/.bashrc' ..."

        with open(os.path.expanduser("~") + "/.bashrc", "a") as f:
             f.write("\n")
             f.write("# bROT alias\n")
             f.write("alias brot=\"python -i brot.py\"")

        print "Done."
        command = "brot"
    else:
        print "Not setting up the alias."
        command = "python -i brot.py"

    os.system("source ~/.bashrc")
    print "Installation complete. You can now 'cd' into the 'brot' subdirectory and start using this tool by calling '" + command + "'."

if __name__ == "__main__":
    sys.exit(main())
