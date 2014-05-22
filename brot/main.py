#!/usr/bin/python

######################################################################
# header

# python imports
import os
import sys
import math
import readline
from collections import namedtuple

# importing root functionality
from ROOT import *

# importing local libraries
import tdrstyle
from lib.configobj import ConfigObj
from lib.validate import Validator

#import functions defined in 'export.py'
from export import *



######################################################################
# defining classes to have global variables

class Objects():
    cfg         = None # config file
    xs_cfg      = None # xs config parser
    validator   = Validator()

objects = Objects()


class Settings():
    # basic settings
    base_dir    = "" # base directory for analyses
    ana_dir     = "" # analysis files subdirectory in base_dir
    file_dir    = "" # ROOT files subdirectory in the ana_dir
    tree_name   = "" # name of tree in root files
    luminosity  = 0 # luminosity
    hist_prefix = "" # prefix of histograms, sth like "h1_0_..."

    # switches
    draw_data           = True # do or dont draw the data
    draw_background     = True
    draw_signal         = True
    stack_signal        = False # do or dont stack signal on background

settings = Settings()

class Process():
    path        = ""
    label       = ""
    hist        = None
    xs          = 0.
    nev         = 0
    weight      = 0.

class Pad():
    data                = None # process: data
    background          = []   # processes: background
    signal              = []   # processes: signal
    background_stack    = None # thstack : backgrounds
    signal_stack        = None # thstack : signal

pads = [] # list of pads proportional to number of pads

class Plotting():
    canvas              = None # global canvas
    pad_nr              = 0 # current pad number
    max_pad_nr          = 0 # overall number of pads

plotting = Plotting()



######################################################################
# functions

def setup(config_file):
    """Reading the config file and doing a rudementary setup based upon it."""

    print "Reading config file", config_file

    # reading the plotting config file
    objects.cfg = ConfigObj("../cfg/" + config_file, configspec = "../cfg/plot_spec.cfg")
    # enter default values and check for errors
    if not objects.cfg.validate(objects.validator):
        print "Failed config file validation."
        
    # reading the cross section config file
    objects.xs_cfg = ConfigObj("../cfg/" + objects.cfg["general"]["xs_file"])

    # reading base directory
    settings.base_dir = objects.cfg["general"]["base_dir"]
    # reading ROOT files sub-directory
    settings.file_dir = objects.cfg["general"]["file_dir"]
    # reading tree name
    settings.tree_name = objects.cfg["general"]["tree_name"]
    # reading histogram prefix
    settings.hist_prefix = objects.cfg["general"]["hist_prefix"]

    # reading luminosity value
    settings.luminosity = objects.cfg["data"].as_float("luminosity")

    # reading switches
    settings.draw_data = objects.cfg["switches"].as_bool("draw_data")
    settings.stack_signal = objects.cfg["switches"].as_bool("stack_signal")

    # enable quadratic uncertainty handling
    TH1.SetDefaultSumw2(True)
    TH2.SetDefaultSumw2(True)
    TH3.SetDefaultSumw2(True)

    SetMemoryPolicy(kMemoryHeuristics)



def selection(analysis_directory):
    """Selecting the sub-directory in which the analysis files are located in"""

    print "Working in sub-directory", analysis_directory
    settings.ana_dir = analysis_directory



def brot_init():
    """Initialize default settings for the bROT package."""
    
    tdrstyle.set_tdr_style() # using TDR style for plotting
    setup("plot.cfg") # setup using the default plot.cfg
    selection("pytest")



def clear_and_prepare_pads(max_pad_number):
    """Delete the data, background and signal processes, as well as the stacks.
    Then create lists with lengths proportional to the number of pads."""

    # delete all pads
    while pads:
        pads.pop(0)
    
    # create process lists proportional to number of pads
    for i in range(max_pad_number):
        pads.append(Pad())


def create_canvas(divide_x = 1, divide_y = 1):
    """Create a canvas and divide it according to divide_x and divide_y. Default values are 1, 1."""

    # check for number of sub-canvases
    if (divide_x > 3 or divide_y > 2):
        print "Maximal amount of sub-canvases: 3x2"
        return

    # destroy previous canvas
    if plotting.canvas is not None:
        plotting.canvas.IsA().Destructor(plotting.canvas)
    
    # create canvas (used globally)
    x_size = int(round(600 * math.sqrt(2))) * divide_x
    y_size = 600 * divide_y
    plotting.canvas = TCanvas("gCanvas", "Analysis", 0, 0, x_size, y_size)

    plotting.canvas.Divide(divide_x, divide_y)
    plotting.canvas.cd(1)
    plotting.pad_nr = 0 # cd - 1 to start lists at [0]
    plotting.max_pad_nr = divide_x * divide_y

    # delete old processes and create new lists for them
    clear_and_prepare_pads(plotting.max_pad_nr)



def read_histogram(file_name, histogram_name):
    """Read a single histogram with the name histogram_name from the analysis.
    Function is called by read_histograms()."""
    
    file_path = settings.base_dir + settings.ana_dir + "/" + settings.file_dir + file_name

    if os.path.exists(file_path):
        t_file = TFile(file_path)
        histo = t_file.Get("h1_0_" + histogram_name)
        if histo:
            histo.SetDirectory(0) # detach histogram from file, otherwise gc will collect
            return histo
        else:
            print "File", file_name, "\n does not contain histogram", histogram_name
            return None

    else:
        print "Could not find file", file_path
        return None



def read_processes(histogram_name):
    """Read the histograms called histogram_name from the analysis files."""

    if objects.cfg is None:
        print "No config file loaded! Use setup('plot.cfg')"
        return

    if settings.ana_dir is "":
        print "No selection done yet. Use selection('fullrun75')"
        return

    dir_path = settings.base_dir + settings.ana_dir + "/"
    if not os.path.exists(dir_path):
        print "Path", dir_path, " does not exist!"
        return

    # load data histogram
    hist = read_histogram(objects.cfg["data"]["file"] + ".root", histogram_name)
    if hist:
        hist.SetFillStyle  (objects.cfg["data"].as_int("fstyle"))
        hist.SetFillColor  (objects.cfg["data"].as_int("fcolor"))
        hist.SetLineStyle  (objects.cfg["data"].as_int("lstyle"))
        hist.SetLineColor  (objects.cfg["data"].as_int("lcolor"))        
        hist.SetMarkerStyle(objects.cfg["data"]["mstyle"])
        hist.SetMarkerColor(objects.cfg["data"]["mcolor"])
        hist.SetMarkerSize (objects.cfg["data"]["msize"])
        
        proc        = Process()
        proc.hist   = hist
        proc.fname  = objects.cfg["data"]["file"]
        proc.label  = objects.cfg["data"]["label"]

        pads[plotting.pad_nr].data = proc

    # loop over backgrounds and load histograms
    for background in objects.cfg["background"]:
        hist = read_histogram(background + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["background"][background].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["background"][background].as_int("fcolor"))
            hist.SetLineStyle  (objects.cfg["background"][background].as_int("lstyle"))
            hist.SetLineColor  (objects.cfg["background"][background].as_int("fcolor"))
            hist.SetMarkerStyle(objects.cfg["background"][background].as_int("mstyle"))
            hist.SetMarkerColor(objects.cfg["background"][background].as_int("mcolor"))
            hist.SetMarkerSize (objects.cfg["background"][background].as_int("msize"))

            proc        = Process()
            proc.hist   = hist
            proc.fname  = background
            proc.label  = objects.cfg["background"][background]["label"]
            proc.xs     = objects.xs_cfg[background].as_float("xs")
            proc.weight = objects.xs_cfg[background].as_float("weight")
            proc.nev    = objects.xs_cfg[background].as_int("Nev")
            proc.hist.Scale(proc.weight * proc.xs * settings.luminosity / proc.nev)

            pads[plotting.pad_nr].background.append(proc)

    # loop over signals and load histograms
    for signal in objects.cfg["signal"]:
        hist = read_histogram(signal + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["signal"][signal].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["signal"][signal].as_int("fcolor"))
            hist.SetLineStyle  (objects.cfg["signal"][signal].as_int("lstyle"))
            hist.SetLineColor  (objects.cfg["signal"][signal].as_int("lcolor"))
            hist.SetMarkerStyle(objects.cfg["signal"][signal].as_int("mstyle"))
            hist.SetMarkerColor(objects.cfg["signal"][signal].as_int("mcolor"))
            hist.SetMarkerSize (objects.cfg["signal"][signal].as_int("msize"))

            proc        = Process()
            proc.hist   = hist
            proc.fname  = signal
            proc.label  = objects.cfg["signal"][signal]["label"]
            proc.xs     = objects.xs_cfg[signal].as_float("xs")
            proc.weight = objects.xs_cfg[signal].as_float("weight")
            proc.nev    = objects.xs_cfg[signal].as_int("Nev")
            proc.hist.Scale(proc.weight * proc.xs * settings.luminosity / proc.nev)

            pads[plotting.pad_nr].signal.append(proc)



def cd(pad_number):
    """Switch to pad with number pad_number"""

    if pad_number > plotting.max_pad_nr:
        print "Pad number is larger than the overall number of pads:", plotting.max_pad_nr
        return

    plotting.canvas.cd(pad_number)
    plotting.pad_nr = pad_number - 1



def delete_old_processes():
    """Deletes loaded data, background and signal processes of the current pad."""
    
    pads[plotting.pad_nr].data = None
    pads[plotting.pad_nr].background = []
    pads[plotting.pad_nr].signal = []
    pads[plotting.pad_nr].background_stack = None
    pads[plotting.pad_nr].signal_stack = None


def order_histograms(histogram_list):
    """Order the list of histograms by their integral"""

    return sorted(histogram_list, key=lambda hist: hist.Integral())



def stack_histograms():
    """Create a THStack from the histograms belonging to the current pad."""

    # stacking backgrounds
    backgrounds = list(pads[plotting.pad_nr].background) # copy of list of backgrounds
    joined_backgrounds = []
    
    while backgrounds:
        # take the current label
        hist = backgrounds[0].hist.Clone()
        hist.SetName(hist.GetName()+str(id(hist)))
        label = backgrounds[0].label
        
        # loop over remaining backgrounds and add the ones with the same labels
        for j in range(1, len(backgrounds)):
            if backgrounds[j].label == label:
                
                hist.Add(backgrounds[j].hist)
                # remove added background
                backgrounds.pop(j)

        # append the joined background to the list
        joined_backgrounds.append(hist)
        # remove the joined background
        backgrounds.pop(0)
    


    # if there are actually any backgrounds ...
    if joined_backgrounds:
        # order the histograms according to their integral
        joined_backgrounds = order_histograms(joined_backgrounds)
        # add the histograms to a THStack and save it in the plotting class
        background_stack = THStack(get_draw_object().GetName(), get_draw_object().GetName())
        for background in joined_backgrounds:
            background_stack.Add(background)
        pads[plotting.pad_nr].background_stack = background_stack
    
    # stacking signal on top of background
    # TODO



def rebin(number_of_bins):
    """Rebin the data, background and signals."""

    # rebin the data histogram
    if pads[plotting.pad_nr].data:
        pads[plotting.pad_nr].data.hist.Rebin(number_of_bins)

    # rebin the individual backgrounds histograms
    if pads[plotting.pad_nr].background:
        for background in pads[plotting.pad_nr].background:
            background.hist.Rebin(number_of_bins)

    # rebin the individual signal histograms
    if pads[plotting.pad_nr].signal:
        for signal in pads[plotting.pad_nr].signal:
            signal.hist.Rebin(number_of_bins)

    draw_histograms()



def update_pad():
    """Updates the pad and redraws the axis"""
    
    if not gPad:
        print "No active pad."
        return

    gPad.Modified()
    gPad.Update()
    gPad.RedrawAxis()



def get_draw_object():
    """Returns the object, which was drawn first and therefore drew the axis etc."""

    # signal stack is drawn first
    if settings.draw_signal and settings.stack_signal and pads[plotting.pad_nr].signal_stack:
        return pads[plotting.pad_nr].signal_stack
    # then background stack
    elif settings.draw_background and pads[plotting.pad_nr].background_stack:
        return pads[plotting.pad_nr].background_stack
    # then signal lines
    elif settings.draw_signal and pads[plotting.pad_nr].signal:
        return pads[plotting.pad_nr].signal[0].hist
    # and last data
    elif settings.draw_data and pads[plotting.pad_nr].data:
        return pads[plotting.pad_nr].data.hist

    # if nothing is being drawn, return None
    return None



def maxy(maximum_value):
    """Sets the highest value on the y-axis that is being shown."""

    hist = get_draw_object()
    if hist:
        hist.SetMaximum(maximum_value)
    update_pad()



def miny(minimum_value):
    """Sets the lowest value on the y-axis that is being shown."""

    hist = get_draw_object()
    if hist:
        hist.SetMinimum(minimum_value)
    update_pad()



def logy(set_logy = True):
    """Sets the scale of current pad to logarithmic.""" 

    if gPad:
        gPad.SetLogy(set_logy)
        update_pad()
        



def title_x(x_axis_title):
    """Sets the title on the x-axis to x_axis_title."""

    hist = get_draw_object()
    if hist:
        hist.GetXaxis().SetTitle(x_axis_title)



def title_y(y_axis_title):
    """Sets the title on the y-axis to y_axis_title."""

    hist = get_draw_object()
    if hist:
        hist.GetYaxis().SetTitle(y_axis_title)



def draw_histograms():
    """Draw data, background and signal histograms."""

    # clear pad before drawing
    gPad.cd()
    gPad.Clear()

    # create stacked background and signal histograms
    stack_histograms()

    # plotting stacked backgrounds
    same = ""
    # signal stack is drawn first
    if settings.stack_signal and settings.draw_signal and pads[plotting.pad_nr].signal_stack:
        pads[plotting.pad_nr].signal_stack.Draw("HIST")
        same = "same"

    if settings.draw_background and pads[plotting.pad_nr].background_stack:
        # then background stack
        pads[plotting.pad_nr].background_stack.Draw("HIST" + same)
        same = "same"

    if settings.draw_signal and not settings.stack_signal and pads[plotting.pad_nr].signal:
        # then signal lines
        for signal in pads[plotting.pad_nr].signal:
            signal.hist.Draw("HIST" + same)
        same = "same"

    if settings.draw_data and pads[plotting.pad_nr].data:
        # and last data
        pads[plotting.pad_nr].data.hist.Draw("EP" + same)
    
    update_pad()



def plot(histogram_name):
    """Compose and draw a plot using the histograms called histogram_name."""

    # check for existing canvas
    if plotting.canvas is None:
        create_canvas()

    delete_old_processes() # delete old processes and stacks of the current pad
    read_processes(histogram_name) # load histogram of the processes
    draw_histograms() # draw the histograms



def remove_export_function(function_title):
    """Removes the function with the title function_title from the 'export.py' file."""

    with open("export.py", "r") as export:
        with open("temp.py", "w") as temp:
            for line in export:
                # write all lines into the temp file, that do not contain the
                # function header
                if not "def" + function_title + "(" in line.replace(" ", ""):
                    temp.write(line)
                else:
                    # if the function header has been found, skip all its contents
                    try:
                        line = export.next()
                        while line == "" or line.startswith(" ") or line.startswith("\t"):
                            line = export.next()
                    except StopIteration:
                        continue

    # create backup and rename file
    os.rename("export.py", "bkup_export.py")
    os.rename("temp.py", "export.py")



def export(function_title = "", export_selection = True, export_setup = False):
    """Exports the Python history up to the last call of plot() to a function in
    'export.py'. If no function_title is given, the histogram title will be
    used."""

    exclusion_list = ["quit", "export"]
    line_buffer = []
    plot_index = 0
    
    selection_index = 0
    
    # find the plot and selection commands
    for i in reversed(range(readline.get_current_history_length())):
        item = readline.get_history_item(i)
        
        # skip lines like quit() or export() to buffer
        for exclusion in exclusion_list:
            if item.startswith(exclusion):
                continue

        # add line to buffer
        line_buffer.append(item)

        # if the plot(...) command has been found, stop
        if item.startswith("plot("):
            plot_index = i
            break

    # check if there was a plot(...)
    if plot_index == 0:
        print "Could not find an instance of plot(...)!"
        return

    # add some additional lines if the options are given
    if export_selection:
        line_buffer.append("selection(" + settings.ana_dir + ")")

    if export_setup:
        line_buffer.append("selection(" + objects.cfg.filename.split("/")[2] + ")")

    # get function title
    if function_title == "":
        function_title = get_draw_object().GetName().replace(settings.hist_prefix, "")


    # checking for existing function in 'export.py'
    with open("export.py", "r") as f:
        # check if function exists already
        for line in f:
            if "def" + function_title + "(" in line.replace(" ", ""):
                # ask for action if function is found
                yorn = raw_input("The function " + function_title + " has been found in 'export.py', do you want to overwrite it? [y]/n: ")
                if yorn == "" or yorn == "y":
                    print "Overwriting function", function_title
                    remove_export_function(function_title)
                else:
                    print "Not exporting function", function_title
                    return

    # write function to 'export.py'
    with open("export.py", "a") as f:
        f.write("\n")
        f.write("def " + function_title + "():\n")
        for line in reversed(line_buffer):
            f.write("    " + line + "\n")
