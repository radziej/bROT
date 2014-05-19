#!/user/bin/python

# execute startup file to load history
import os

startup_file = os.environ.get("PYTHONSTARTUP")
if startup_file and os.path.isfile(startup_file):
    # note that the startup file may delete imports
    execfile(startup_file)


print "Loading bROT ..."
execfile("main.py")
setup("plot.cfg")
selection("pytest")

