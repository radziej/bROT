#!/usr/bin/python

######################################################################
# header

# python imports
import os
import sys
import math
from collections import namedtuple

# importing root functionality
from ROOT import *

# importing local libraries
sys.path.append("lib/")
from configobj import ConfigObj
from validate import Validator


######################################################################
# defining classes to have global variables

class Objects():
    cfg         = None # config file
    xs_cfg      = None # xs config parser
    validator   = Validator()

objects = Objects()


class Settings():
    base_dir    = None # base directory for analyses
    ana_dir     = None # analysis files subdirectory in base_dir
    file_dir    = None # ROOT files subdirectory in the ana_dir
    tree_name   = None # name of tree in root files
    luminosity  = 0 # luminosity
    stack_signal= False # do or dont stack signal on background

settings = Settings()

class Process():
    path        = ""
    label       = ""
    hist        = None
    xs          = 0.
    nev         = 0
    weight      = 0.

Processes = namedtuple("Processes", ["data", "background", "signal"]) # define a collection of histograms
processes = Processes([], [], []) # list of Processes defined beforehand created proportional to number of pads

class Plotting():
    canvas              = None # global canvas
    pad_nr              = 0 # current pad number
    max_pad_nr          = 0 # overall number of pads
    background_stack    = [] # list of background THStacks
    signal_stack        = [] # list of signal THStacks

plotting = Plotting()



######################################################################
# functions

def setup(config_file):
    """Reading the config file and doing a rudementary setup based upon it"""

    print "Reading config file", config_file

    # reading the plotting config file
    objects.cfg = ConfigObj(config_file, configspec = "plot_spec.cfg")
    # enter default values and check for errors
    if not objects.cfg.validate(objects.validator):
        print "Failed config file validation."
        
    # reading the cross section config file
    objects.xs_cfg = ConfigObj(objects.cfg["general"]["xs_file"])

    # reading base directory
    settings.base_dir = objects.cfg["general"]["base_dir"]
    # reading ROOT files sub-directory
    settings.file_dir = objects.cfg["general"]["file_dir"]
    # reading tree name
    settings.tree_name = objects.cfg["general"]["tree_name"]

    # reading luminosity value
    settings.luminosity = objects.cfg["data"].as_float("luminosity")
    # reading switches
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



def clear_and_prepare_processes(max_pad_number):
    """Delete the data, background and signal processes, as well as the stacks.
    Then create lists with lengths proportional to the number of pads."""

    # delete old processes
    if len(processes.data) is not 0:
        del processes.data[pad_number]
    if len(processes.background) is not 0:
        del processes.background[:]
    if len(processes.signal) is not 0:
        del processes.signal[:]

    # delete old stacks
    if len(plotting.background_stack) is not 0:
        del plotting.background_stack[:]
    if len(plotting.signal_stack) is not 0:
        del plotting.signal_stack[:]

    # create process lists proportional to number of pads
    for i in range(max_pad_number):
        processes.data.append(None)
        processes.background.append([])
        processes.signal.append([])
        
        plotting.signal_stack.append(None)
        plotting.background_stack.append(None)



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
    clear_and_prepare_processes(plotting.max_pad_nr)



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

    if settings.ana_dir is None:
        print "No selection done yet. Use selection('fullrun75')"
        return

    dir_path = settings.base_dir + settings.ana_dir + "/"
    if not os.path.exists(dir_path):
        print "Path", dir_path, " does not exist!"
        return

    # load data histogram
    hist = read_histogram(objects.cfg["data"]["file"] + ".root", histogram_name)
    if hist:
        hist.SetFillStyle  (objects.cfg["data"]["fstyle"])
        hist.SetFillColor  (objects.cfg["data"]["fcolor"])
        hist.SetLineStyle  (objects.cfg["data"]["fstyle"])
        hist.SetLineColor  (objects.cfg["data"]["fcolor"])
        hist.SetMarkerStyle(objects.cfg["data"]["mstyle"])
        hist.SetMarkerColor(objects.cfg["data"]["mcolor"])
        hist.SetMarkerSize (objects.cfg["data"]["msize"])
        
        proc        = Process()
        proc.hist   = hist
        proc.fname  = objects.cfg["data"]["file"]
        proc.label  = objects.cfg["data"]["label"]

        processes.data[plotting.pad_nr] = proc

    # loop over backgrounds and load histograms
    for background in objects.cfg["background"]:
        hist = read_histogram(background + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["background"][background].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["background"][background].as_int("fcolor"))
            hist.SetLineStyle  (objects.cfg["background"][background].as_int("fstyle"))
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

            processes.background[plotting.pad_nr].append(proc)

    # loop over signals and load histograms
    for signal in objects.cfg["signal"]:
        hist = read_histogram(signal + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["signal"][signal].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["signal"][signal].as_int("fcolor"))
            hist.SetLineStyle  (objects.cfg["signal"][signal].as_int("fstyle"))
            hist.SetLineColor  (objects.cfg["signal"][signal].as_int("fcolor"))
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

            processes.signal[plotting.pad_nr].append(proc)



def cd(pad_number):
    """Switch to pad with number pad_number"""

    if pad_number > plotting.max_pad_nr:
        print "Pad number is larger than the overall number of pads:", plotting.max_pad_nr
        return

    plotting.canvas.cd(pad_number)
    plotting.pad_nr = pad_number - 1



def delete_old_processes():
    """Deletes loaded data, background and signal processes of the current pad."""
    
    if processes.data[plotting.pad_nr]:
        processes.data[plotting.pad_nr] = None
    if processes.background[plotting.pad_nr]:
        processes.background[plotting.pad_nr] = []
    if processes.signal[plotting.pad_nr]:
        processes.signal[plotting.pad_nr] = []

    if plotting.background_stack[plotting.pad_nr]:
        plotting.background_stack[plotting.pad_nr] = None
    if plotting.signal_stack[plotting.pad_nr]:
        plotting.signal_stack[plotting.pad_nr] = None
    


def order_histograms(histogram_list):
    """Order the list of histograms by their integral"""

    return sorted(histogram_list, key=lambda hist: hist.Integral())



def stack_histograms():
    """Create a THStack from the histograms belonging to the current pad."""

    # stacking backgrounds
    backgrounds = list(processes.background[plotting.pad_nr]) # copy of list of backgrounds
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
    
    # order the histograms according to their integral
    joined_backgrounds = order_histograms(joined_backgrounds)

    # add the histograms to a THStack and save it in the plotting class
    background_stack = THStack("background_stack", "THStack of Backgrounds")    
    for background in joined_backgrounds:
        background_stack.Add(background)
    plotting.background_stack[plotting.pad_nr] = background_stack
    
    
    # stacking signal on top of background

    

def rebin(number_of_bins):
    """Rebin the data, background and signals."""

    # rebin the data histogram
    if processes.data[plotting.pad_nr]:
        processes.data[plotting.pad_nr].hist.Rebin(number_of_bins)

    # rebin the individual backgrounds histograms
    if processes.background[plotting.pad_nr]:
        for background in processes.background[plotting.pad_nr]:
            background.hist.Rebin(number_of_bins)

    # rebin the individual signal histograms
    if processes.signal[plotting.pad_nr]:
        for signal in processes.signal[plotting.pad_nr]:
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



def max(maximum_value):
    """Sets the highest value on the y-axis that is being shown."""

    if settings.stack_signal:
        plotting.signal_stack[plotting.pad_nr].SetMaximum(maximum_value)
    else:
        plotting.background_stack[plotting.pad_nr].SetMaximum(maximum_value)

    update_pad()



def min(minimum_value):
    """Sets the lowest value on the y-axis that is being shown."""

    if settings.stack_signal:
        plotting.signal_stack[plotting.pad_nr].SetMinimum(minimum_value)
    else:
        plotting.background_stack[plotting.pad_nr].SetMinimum(minimum_value)

    update_pad()
    


def draw_histograms():
    """Draw data, background and signal histograms."""

    # clear pad before drawing
    gPad.cd()
    gPad.Clear()

    # create stacked background and signal histograms
    stack_histograms()

    # plotting stacked backgrounds
    plotting.background_stack[plotting.pad_nr].Draw("hist")

    # plotting signals
    

    # plotting data
    processes.data[plotting.pad_nr].hist.Draw("EPsame")

    update_pad()


def plot(histogram_name):
    """Compose and draw a plot using the histograms called histogram_name."""

    # check for existing canvas
    if plotting.canvas is None:
        create_canvas()

    delete_old_processes() # delete old processes and stacks of the current pad
    read_processes(histogram_name) # load histogram of the processes
    draw_histograms() # draw the histograms
    # draw_histograms()
