#!/usr/bin/python

######################################################################
# header

# python imports
import os
import sys
import copy
import math
import readline
import itertools
from array import array
from collections import namedtuple

# importing root functionality
from ROOT import *

# importing local libraries
import style
from lib.configobj import ConfigObj
from lib.validate import Validator



######################################################################
# defining classes to have global variables

class Objects():
    validator   = Validator()
    def __init__(self):
        self.cfg         = None # config file
        self.xs_cfg      = None # xs config parser

objects = Objects()


class Settings():
    def __init__(self):
        # basic settings
        self.base_dir    = "" # base directory for analyses
        self.ana_dir     = "" # analysis files subdirectory in base_dir
        self.file_dir    = "" # ROOT files subdirectory in the ana_dir
        self.tree_name   = "" # name of tree in root files
        self.hist_prefix = "" # prefix of histograms, sth like "h1_0_..."

        # draw options
        self.cms_text    = "" # CMS data taking period/publication/preliminary
        self.luminosity  = 0 # luminosity

        # switches
        self.draw_data          = True # do or dont draw
        self.draw_background    = True # do or dont draw
        self.draw_signal        = True # do or dont draw
        self.draw_systematics   = True # do or dont draw

        self.do_chi2quantil     = False # draw chi2 errors for data points
        self.stack_signal       = False # do or dont stack signal on background

        # bin width to which variable bins are normalized to
        # for values equal or less than 0.0, smallest bin width in histogram is used
        self.bin_normalization_width = 0.0
        

settings = Settings()


# class containing the information for an individual process
class Process():
    def __init__(self):
        self.path       = ""    # path to file
        self.label      = ""    # label of process
        self.hist       = None  # TH1D histogram
        self.style      = ""    # plotting style
        self.xs         = 0.    # cross section in pb
        self.nev        = 0     # number of events
        self.weight     = 0.    # weight/scale factor


# class containing the drawing objects and information of a ratio pad
class Ratio():
    def __init__(self):
        self.pad        = None  # the TPad of the ratio
        self.hist       = None  # ratio TH1D histogram
        self.systematics= None  # systematics ratio TH1D histogram
        self.line       = None  # TLine drawn at 1.


# class containing the drawing objects and information of a pad
class Pad():
    def reset(self):
        # raw processes
        self.raw_data           = []   # process : data
        self.raw_backgrounds    = []   # process : background
        self.raw_signals        = []   # process : signal
        self.raw_systematics    = []   # process : systematic

        # composed, aka merged and ordered processes
        self.data                = None # process : data
        self.backgrounds         = []   # process : background
        self.signals             = []   # process : signal
        self.systematics         = None # process : systematic

        self.ordered_processes   = []   # order of plotting

        # misc drawing objects
        self.legend              = None # tlegend
        self.ratio               = None # Ratio : ratio object
        self.latex               = []   # list of latex objects

        self.misc                = [] # list to append miscellaneous draw objects

    def __init__(self):
        self.reset()

pads = [] # list of pads proportional to number of pads


# class containing the basic plotting informatio and objects
class Canvas():
    def __init__(self):
        self.canvas     = None  # global canvas

        self.pad_nr     = 0     # current pad number
        self.max_pad_nr = 0     # overall number of pads

canvas = Canvas()



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

    # reading cms text
    settings.cms_text = objects.cfg["general"]["cms_text"]

    # reading switches
    #
    settings.chi2_quantile = objects.cfg["switches"].as_float("chi2_quantile")
    # draw options
    settings.draw_data = objects.cfg["switches"].as_bool("draw_data")
    settings.stack_signal = objects.cfg["switches"].as_bool("stack_signal")
    settings.draw_systematics = objects.cfg["switches"].as_bool("draw_systematics")

    settings.bin_normalization_width = objects.cfg["switches"].as_float("bin_normalization_width")

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

    style.set_tdr_style() # using TDR style for plotting
    setup("plot.cfg") # setup using the default plot.cfg
    selection("pytest")



def clear_and_prepare_pads(max_pad_number):
    """Delete the data, background and signal processes, as well as the stacks. Then
    create lists with lengths proportional to the number of pads."""

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

    # destroy old canvas
    if canvas.canvas:
       canvas.canvas = None

    # create canvas (used globally)
    x_size = 850 * divide_x
    y_size = 600 * divide_y
    canvas.canvas = TCanvas("gCanvas", "Analysis", 0, 0, x_size, y_size)

    canvas.canvas.Divide(divide_x, divide_y)
    canvas.canvas.cd(1)
    canvas.pad_nr = 0 # cd - 1 to start lists at [0]
    canvas.max_pad_nr = divide_x * divide_y

    # delete old processes and create new lists for them
    clear_and_prepare_pads(canvas.max_pad_nr)



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

    dir_path = settings.base_dir + settings.ana_dir + "/"
    if not os.path.exists(dir_path):
        print "Path", dir_path, " does not exist!"
        return

    # loop over data histograms and sum up luminosities
    settings.luminosity = 0.
    for data in objects.cfg["data"].sections:
        # normalize to sum of lumi of all given data
        settings.luminosity += objects.cfg["data"][data].as_float("luminosity")
        hist = read_histogram(data + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["data"].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["data"].as_int("fcolor"))
            hist.SetLineStyle  (objects.cfg["data"].as_int("lstyle"))
            hist.SetLineColor  (objects.cfg["data"].as_int("lcolor"))
            hist.SetMarkerStyle(objects.cfg["data"].as_int("mstyle"))
            hist.SetMarkerColor(objects.cfg["data"].as_int("mcolor"))
            hist.SetMarkerSize (objects.cfg["data"].as_float("msize"))

            proc        = Process()
            proc.style  = "E"
            proc.hist   = hist
            proc.fname  = data
            proc.label  = objects.cfg["data"]["label"]

            pads[canvas.pad_nr].raw_data.append(proc)


    # loop over backgrounds and load histograms
    for background in objects.cfg["backgrounds"].sections:
        hist = read_histogram(background + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["backgrounds"][background].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["backgrounds"][background].as_int("fcolor"))
            hist.SetLineStyle  (objects.cfg["backgrounds"][background].as_int("lstyle"))
            hist.SetLineColor  (objects.cfg["backgrounds"][background].as_int("fcolor"))
            hist.SetMarkerStyle(objects.cfg["backgrounds"][background].as_int("mstyle"))
            hist.SetMarkerColor(objects.cfg["backgrounds"][background].as_int("mcolor"))
            hist.SetMarkerSize (objects.cfg["backgrounds"][background].as_float("msize"))

            proc        = Process()
            proc.hist   = hist
            proc.style  = "HIST"
            proc.fname  = background
            proc.label  = objects.cfg["backgrounds"][background]["label"]
            proc.xs     = objects.xs_cfg[background].as_float("xs")
            proc.weight = objects.xs_cfg[background].as_float("weight")
            proc.nev    = objects.xs_cfg[background].as_int("Nev")
            proc.hist.Scale(proc.weight * proc.xs * settings.luminosity / proc.nev)

            pads[canvas.pad_nr].raw_backgrounds.append(proc)

    # loop over signals and load histograms
    for signal in objects.cfg["signals"].sections:
        hist = read_histogram(signal + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["signals"][signal].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["signals"][signal].as_int("fcolor"))
            hist.SetLineStyle  (objects.cfg["signals"][signal].as_int("lstyle"))
            hist.SetLineColor  (objects.cfg["signals"][signal].as_int("lcolor"))
            hist.SetMarkerStyle(objects.cfg["signals"][signal].as_int("mstyle"))
            hist.SetMarkerColor(objects.cfg["signals"][signal].as_int("mcolor"))
            hist.SetMarkerSize (objects.cfg["signals"][signal].as_float("msize"))

            proc        = Process()
            proc.hist   = hist
            proc.style  = "HIST"
            proc.fname  = signal
            proc.label  = objects.cfg["signals"][signal]["label"]
            proc.xs     = objects.xs_cfg[signal].as_float("xs")
            proc.weight = objects.xs_cfg[signal].as_float("weight")
            proc.nev    = objects.xs_cfg[signal].as_int("Nev")
            proc.hist.Scale(proc.weight * proc.xs * settings.luminosity / proc.nev)

            pads[canvas.pad_nr].raw_signals.append(proc)

    # loop over systematics and load histograms
    for systematic in objects.cfg["systematics"].sections:
        hist = read_histogram(systematic + ".root", histogram_name)
        if hist:
            hist.SetFillStyle  (objects.cfg["systematics"].as_int("fstyle"))
            hist.SetFillColor  (objects.cfg["systematics"].as_int("fcolor"))
            
            proc        = Process()
            proc.hist   = hist
            proc.style  = "E2"
            proc.fname  = systematic
            proc.label  = objects.cfg["systematics"]["label"]
            
            pads[canvas.pad_nr].raw_systematics.append(proc)



def cd(pad_number):
    """Switch to pad with number pad_number"""

    if pad_number > canvas.max_pad_nr or 1 > pad_number:
        print "Pad number must be between", canvas.max_pad_nr, "and 1."
        return

    canvas.canvas.cd(pad_number)
    canvas.pad_nr = pad_number - 1



def delete_pad_objects():
    """Deletes loaded data, background and signal processes of the current pad."""

    pads[canvas.pad_nr].reset()



def order_processes(process_list):
    """Order the list of processes by the integral of their histogram."""

    return sorted(process_list, key=lambda proc: proc.hist.Integral())



def merge_processes(process_list, style="linear"):
    """Merge the processes that carry the same label."""

    joined_processes = []

    while process_list:
        # take the current label
        hist = process_list[0].hist.Clone()
        hist.SetName(hist.GetName())#+str(id(hist)))
        label = process_list[0].label

        # loop over remaining process_list and add the ones with the same labels
        for j in range(1, len(process_list)):
            if process_list[j].label == label:

                # add the bin contents linearly
                if style == "linear":
                    hist.Add(process_list[j].hist)

                # add the bin contents quadratically
                if style == "quadratic":
                    for i in range(1, hist.GetXaxis().GetNbins()):
                        hist.SetBinContent(i, sqrt(pow(hist.GetBinContent(i), 2) +
                                                   pow(process_list[j].hist.GetBinContent(i), 2)))
                        
                # remove added background
                process_list.pop(j)

        # create a copy of the process and set its histogram to the cloned one
        process_copy = copy.copy(process_list[0])
        process_copy.hist = hist

        # append the joined process to the list
        joined_processes.append(process_copy)
        # remove the joined process
        process_list.pop(0)

    return joined_processes



def stack_processes(process_list):
    """Create a THStack from the histograms belonging to the current pad."""

    # if there are actually any processes ...
    if process_list:
        # add the histograms to a THStack and save it in the plot class
        process_stack = THStack(process_list[0].hist.GetName(), process_list[0].hist.GetName()) #"stack" + str(id(process_list[0].hist)),
                                #"stack" + str(id(process_list[0].hist)))
        for process in process_list:
            process_stack.Add(process.hist)
            
        return process_stack

    # else return empy stack
    print "Warning! THStack is empty!"
    return THStack()



def rebin(bins):
    """Rebin the data, background and signals. If 'bins' is an integer, it merges
    the respective number of bins. If it is an array, the bin borders are
    adjusted individually."""

    if pads[canvas.pad_nr].raw_systematics and settings.draw_systematics:
        print "Cannot call rebin() when showing the systematics."
        return
    
    # merge bins
    if type(bins) is int:
        for process in list(itertools.chain(pads[canvas.pad_nr].raw_data,
                                        pads[canvas.pad_nr].raw_backgrounds,
                                        pads[canvas.pad_nr].raw_signals)):
            process.hist.Rebin(bins)

        # redraw processes
        draw_processes()

    # variable binning
    if type(bins) is list:
        for process in list(itertools.chain(pads[canvas.pad_nr].raw_data,
                                        pads[canvas.pad_nr].raw_backgrounds,
                                        pads[canvas.pad_nr].raw_signals)):

            # replace old histograms
            process.hist = process.hist.Rebin(int(len(bins)-1), # arraylength - 1
                                              process.hist.GetName(), # new name of histogram
                                              array("d", bins)) # array of bin (lower) edges

        # create merged processes
        order_all_processes()
        # scales bin heights if bin widths are variable
        scale_bin_heights()
        # redraw
        draw()



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

    if pads[canvas.pad_nr].ordered_processes:
        return pads[canvas.pad_nr].ordered_processes[0].hist
    
    # if nothing is being drawn, return None
    return None



def ymax(maximum_value):
    """Sets the highest value on the y-axis that is being shown."""

    hist = get_draw_object()
    if hist:
        hist.SetMaximum(maximum_value)
    update_pad()



def ymin(minimum_value):
    """Sets the lowest value on the y-axis that is being shown."""

    # has to be set for all draw objects to prevent error messages when turning
    # axis logarithmic
    for process in pads[canvas.pad_nr].ordered_processes:
        process.hist.SetMinimum(minimum_value)
    update_pad()



def zoom(minimum_value, maximum_value):
    """Shows the area of the x-axis specified by the minimum and maximum value."""

    hist = get_draw_object()
    if hist:
        hist.GetXaxis().SetRangeUser(minimum_value, maximum_value)
    update_pad()



def logy(set_logy = True):
    """Sets the scale of current pad to logarithmic."""

    if gPad:
        cd(canvas.pad_nr + 1)
        # if get_draw_object().GetMinimum() <= 0:
        # TODO
        gPad.SetLogy(set_logy)
        draw_processes()
        update_pad()



def set_text_style(tlatex, size = 0.05):
    """Sets the default style for TLatex text objects."""
    
    tlatex.SetNDC()
    tlatex.SetTextFont(42)
    tlatex.SetTextSize(size)



def cms_text(position = "top", additional_text = ""):
    """Draws the luminosity and CMS text."""

    if not gPad:
        print "No pad."
        return

    cd(1)

    # clearing old latex objects
    if pads[canvas.pad_nr].latex:
        del pads[canvas.pad_nr].latex[:]

    # luminosity text on the top right
    right_text = TLatex(0.74, 0.955, "{0:.1f}".format(settings.luminosity/1000) + " fb^{-1} (8 TeV)" )
    #"#lower[-0.05]{#scale[0.5]{#int}} L #lower[-0.1]{=} %.1f fb^{-1}  #sqrt{s} = 8 TeV" %(settings.luminosity/1000) )
    set_text_style(right_text, 0.04)
    right_text.Draw()
    pads[canvas.pad_nr].latex.append(right_text)

    # determine coordinates and draw cms text
    cms_x = 0.16
    cms_y = 0.955
    if position == "top":
        cms_text = TLatex(cms_x, cms_y, "#font[62]{CMS} #scale[0.8]{#font[52]{" + settings.cms_text + "}}   #scale[0.8]{" + additional_text + "}")
        set_text_style(cms_text)
        cms_text.Draw()

        # done
        pads[canvas.pad_nr].latex.append(cms_text)
        return

    elif position == "left":
        cms_x = 0.16
        cms_y = 0.87
    elif position == "center":
        cms_x = 0.48
        cms_y = 0.87
    elif position == "right":
        cms_x = 0.74
        cms_y = 0.87

    cms_text  = TLatex(cms_x, cms_y, "#font[62]{CMS}")
    cms_text2 = TLatex(cms_x, cms_y - 0.05, "#scale[0.8]{#font[52]{" + settings.cms_text + "}}")
    cms_text3 = TLatex(cms_x, cms_y - 0.13, "#scale[0.8]{" + additional_text + "}")

    set_text_style(cms_text)
    set_text_style(cms_text2)
    set_text_style(cms_text3)

    cms_text.Draw()
    cms_text2.Draw()
    cms_text3.Draw()

    pads[canvas.pad_nr].latex.extend([cms_text, cms_text2, cms_text3])



def xtitle(x_axis_title = ""):
    """Sets the title on the x-axis to x_axis_title."""

    hist = get_draw_object()
    if hist:
        hist.GetXaxis().SetTitle(x_axis_title)



def ytitle(y_axis_title = ""):
    """Sets the title on the y-axis to y_axis_title. By default this is the number
    of events and the bin width."""

    hist = get_draw_object()
    if hist:
        if y_axis_title:
            hist.GetYaxis().SetTitle(y_axis_title)

        else:
            # parse x-axis title for unit
            units = ["GeV", "TeV", "cm", "rad"]
            # take last part of the title
            x_axis_unit = get_draw_object().GetXaxis().GetTitle().split()[::-1][0]
            unit = ""

            for u in units:
                if u in x_axis_unit:
                    unit = u

            # retrieve bin width
            bin_width = hist.GetXaxis().GetBinWidth(hist.GetXaxis().GetFirst())

            # if there is no unit and width is 1, dont add it to the text
            if unit is "" and bin_width == 1:
                y_axis_title = "Events"
            else:
                y_axis_title = "Events / {0:.2g} ".format(bin_width) + unit

            hist.GetYaxis().SetTitle(y_axis_title)


def filter_by_bin_height(minimum_bin_height, processes):
    """Filters the given processes by requiring a minimum height of their highest
    bins."""

    valid_processes = []
    for process in processes:
        if not process.hist.GetBinContent(process.hist.GetMaximumBin()) < minimum_bin_height:
            valid_processes.append(process)

    return valid_processes



def legend(minimum_bin_height = 1e-3, number_of_columns = 1, x1 = None, y1 = None, x2 = None, y2 = None):
    """Draws a legend containing the process labels. Same labels, meaning stacked
    histograms, are only drawn once."""

    # delete old legend
    if pads[canvas.pad_nr].legend:
        pads[canvas.pad_nr].legend = None

    # collect backgrounds, data and ordered signals

    data = (pads[canvas.pad_nr].data if settings.draw_data else None)
    systematics = (pads[canvas.pad_nr].systematics if settings.draw_systematics else None)
    backgrounds = (filter_by_bin_height(minimum_bin_height, pads[canvas.pad_nr].backgrounds) if settings.draw_background else [])
    signals = (filter_by_bin_height(minimum_bin_height, pads[canvas.pad_nr].signals) if settings.draw_signal else [])

    # set the unspecified size variables
    if x1 is None:
        x1 = 0.67
    if y1 is None:
        y1 = 0.92
    if x2 is None:
        x2 = 0.91
    if y2 is None:
        # adjust y2 for number of entries
        y2 = 0.92
        size_per_entry = 0.08
        y2 -= size_per_entry * (len(backgrounds) + len(signals) + (1 if data else 0))

    legend = TLegend(x1, y1, x2, y2)

    # take the ordered backgrounds
    for background in backgrounds[::-1]:
        legend.AddEntry(background.hist, background.label, "f")

    if systematics:
        legend.AddEntry(systematics.hist, systematics.label, "f")
    
    if data:
        legend.AddEntry(data.hist, data.label, "pe")

    for signal in signals[::-1]:
        legend.AddEntry(signal.hist, signal.label, "l")

    # legend settings and drawing
    legend.SetFillColor(kWhite)
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.SetTextFont(42)
    legend.SetNColumns(number_of_columns)
    cd(canvas.pad_nr + 1)
    legend.Draw()
    pads[canvas.pad_nr].legend = legend



def accumulate_histogram(histogram):
    """Transforms one histogram into a cumulative distribution."""

    for i in range(1, histogram.GetXaxis().GetNbins()):
        integral_error = Double(0)
        integral = histogram.IntegralAndError(i,
                                              histogram.GetXaxis().GetNbins(),
                                              integral_error)

        histogram.SetBinContent(i, integral)
        histogram.SetBinError(i, integral_error)



def cumulative():
    """Takes the histograms of the current pad transforms them into cumulative
    distributions."""

    if not get_draw_object():
        print "Use plot(histogram_name) first."
        return

    if pads[canvas.pad_nr].raw_systematics and settings.draw_systematics:
        print "Cannot call cumulative() when showing the systematics."
        return

    for process in list(itertools.chain(pads[canvas.pad_nr].raw_data,
                                        pads[canvas.pad_nr].raw_backgrounds,
                                        pads[canvas.pad_nr].raw_signals)):
        accumulate_histogram(process.hist)

    draw_processes()



def order_all_processes():
    """Merges and orderes processes and stores them in the pads class."""

    if pads[canvas.pad_nr].raw_backgrounds:
        pads[canvas.pad_nr].backgrounds = order_processes(merge_processes(list(pads[canvas.pad_nr].raw_backgrounds)))
    
    if pads[canvas.pad_nr].raw_data:
        pads[canvas.pad_nr].data = merge_processes(list(pads[canvas.pad_nr].raw_data))[0]

    if pads[canvas.pad_nr].raw_signals:
        pads[canvas.pad_nr].signals = order_processes(list(pads[canvas.pad_nr].raw_signals))

    if pads[canvas.pad_nr].raw_systematics:
        pads[canvas.pad_nr].systematics = merge_processes(list(pads[canvas.pad_nr].raw_systematics), "quadratic")[0]



def compose_draw_objects():
    """Gather information and prepare processes to be drawn."""

    # reset plotting order
    if pads[canvas.pad_nr].ordered_processes:
        pads[canvas.pad_nr].ordered_processes = []

    # backgrounds
    if pads[canvas.pad_nr].backgrounds:

        # create THStack
        stacked_backgrounds = Process()
        stacked_backgrounds.hist = stack_processes(list(pads[canvas.pad_nr].backgrounds))
        stacked_backgrounds.label = "Stacked Backgrounds"
        stacked_backgrounds.style = "HIST"

        if settings.draw_background:
            pads[canvas.pad_nr].ordered_processes.append(stacked_backgrounds)

    # systematics
    if pads[canvas.pad_nr].systematics:

        # check if systematics should be drawn
        if settings.draw_systematics:

            # create systematics uncertainty band process
            uncertainty_band = Process()
            uncertainty_band.hist = pads[canvas.pad_nr].systematics.hist
            uncertainty_band.label = pads[canvas.pad_nr].systematics.label
            uncertainty_band.style = pads[canvas.pad_nr].systematics.style

            # calculate and store uncertainty band
            stack = pads[canvas.pad_nr].ordered_processes[0].hist.GetStack().Last()
            for i in range(1, uncertainty_band.hist.GetXaxis().GetNbins()):
                uncertainty_band.hist.SetBinError(i, uncertainty_band.hist.GetBinContent(i) *
                                                     stack.GetBinContent(i))
                uncertainty_band.hist.SetBinContent(i, stack.GetBinContent(i))

            pads[canvas.pad_nr].ordered_processes.append(uncertainty_band)

    # data
    if pads[canvas.pad_nr].data:

        # append data
        if settings.draw_data:
            # set additional error option
            if settings.chi2_quantile == 1.0:
                pads[canvas.pad_nr].data.hist.Sumw2(False)
                pads[canvas.pad_nr].data.hist.SetBinErrorOption(TH1.kPoisson)

            pads[canvas.pad_nr].ordered_processes.append(pads[canvas.pad_nr].data)

    # signals
    if pads[canvas.pad_nr].signals:

        # stack signals on top of background if required 
        if settings.stack_signal:
            for signal in pads[canvas.pad_nr].signals:
                for background in pads[canvas.pad_nr].backgrounds:
                    signal.hist.Add(background.hist)

        # insert or append signals
        if settings.draw_signal:
            if settings.stack_signal:
                # draw first
                for signal in pads[canvas.pad_nr].signals:
                    pads[canvas.pad_nr].ordered_processes.insert(0, signal)
            else:
                # draw last
                for signal in pads[canvas.pad_nr].signals:
                    pads[canvas.pad_nr].ordered_processes.append(signal)



def scale_bin_heights(base_width = 1.0):
    """Scales the bin heights according their width relative to the 'base_width'."""

    # use default value if no base_width is supplied
    if base_width <= 0.0:
        base_width = settings.bin_normalization_width
        # if default value is set to 0.0 (or less), use smallest bin width
        if base_width <= 0.0:
            x_axis = get_draw_object().GetXaxis()
            for i in range(1, x_axis.GetNbins()):
                base_width = min(base_width, x_axis.GetBinWidth(i))

    # scale the bin content and error
    for process in list(itertools.chain([pads[canvas.pad_nr].data],
                                        pads[canvas.pad_nr].backgrounds,
                                        pads[canvas.pad_nr].signals)):
        hist = process.hist
        for i in range(1, hist.GetNbinsX()+1):
            scale_factor = base_width / hist.GetBinWidth(i)
            hist.SetBinContent(i, hist.GetBinContent(i) * scale_factor)
            hist.SetBinError(i, hist.GetBinError(i) * scale_factor)



def draw():
    """Composes the drawing objects and plots them."""

    # clear pad before drawing
    cd(canvas.pad_nr + 1) # pad_nr starts at 0
    gPad.Clear()

    # collect information and set up processes for drawing
    compose_draw_objects()

    # plot all the backgrounds
    same = ""
    for process in pads[canvas.pad_nr].ordered_processes:
        process.hist.Draw(process.style + same)
        same = "same"

    update_pad()



def draw_processes():
    """Draw data, background and signal histograms."""

    # ensure working on the right pad
    # cd(canvas.pad_nr + 1) # pad_nr starts at 0

    # merge and order processes
    order_all_processes()

    # draw
    draw()



def ratio():
    """Draws the ratio of the histogram in an additional pad below."""

    # create new ratio object
    pads[canvas.pad_nr].ratio = Ratio()

    
    if not pads[canvas.pad_nr].backgrounds:
        print "There are no backgrounds."
        return

    # sum up the backgrounds    
    background_sum = pads[canvas.pad_nr].backgrounds[0].hist.Clone()
    for i in range(1, len(pads[canvas.pad_nr].backgrounds)):
        background_sum.Add(pads[canvas.pad_nr].backgrounds[i].hist)

    draw_object = get_draw_object()

    if not pads[canvas.pad_nr].ratio.pad:
        # setup the window and pads to draw a ratio
        cd(canvas.pad_nr + 1)

        # expand canvas
        expansion_factor = 1.25
        canvas.canvas.SetWindowSize(850, int(floor(600 * expansion_factor)))

        # resize drawing pad
        # base length - ( base length / expansion factor )
        y_ndc = 0.97 - (0.97 / expansion_factor)
        gPad.SetPad(0.01, y_ndc, 0.98, 0.98)
        update_pad()

        # draw new pad for ratio on canvas
        canvas.canvas.cd()
        # base length - ( drawing pad bottom margin * base length / expansion factor )
        y_ndc = 0.97 - ((1 - gPad.GetBottomMargin()) * 0.97 / expansion_factor)
        ratio_pad = TPad("ratiopad" + str(canvas.pad_nr), "ratiopad" + str(canvas.pad_nr),
                         0.01, 0.01, 0.98, y_ndc)

        # adjust settings, due to different scale
        ratio_pad.SetTopMargin(0.0)
        ratio_pad.SetBottomMargin(0.30)
        ratio_pad.Draw()
        pads[canvas.pad_nr].ratio.pad = ratio_pad


    pads[canvas.pad_nr].ratio.pad.cd()

    # calculate the ratio
    ratio = pads[canvas.pad_nr].data.hist.Clone()
    ratio.Divide(background_sum)
    ratio.SetMaximum(-1111)
    ratio.SetMinimum(-1111)

    # y axis
    ratio.GetYaxis().SetTitle("Data / MC");
    ratio.GetYaxis().SetNdivisions(504)
    ratio.GetYaxis().CenterTitle()

    ratio.GetYaxis().SetTitleOffset(0.45)
    ratio.GetYaxis().SetTitleSize(0.13)
    ratio.GetYaxis().SetLabelSize(0.13)

    # x axis
    ratio.GetXaxis().SetRange(draw_object.GetXaxis().GetFirst(), draw_object.GetXaxis().GetLast())
    ratio.GetXaxis().SetTitle(draw_object.GetXaxis().GetTitle())
    # ratio.GetXaxis().CenterTitle()

    ratio.GetXaxis().SetTitleOffset(0.95)
    ratio.GetXaxis().SetTitleSize(0.15)
    ratio.GetXaxis().SetLabelSize(0.15)
    ratio.GetXaxis().SetNdivisions(507)

    ratio.Draw("EP")
    pads[canvas.pad_nr].ratio.hist = ratio

    # line
    line = TLine(ratio.GetXaxis().GetBinLowEdge(ratio.GetXaxis().GetFirst()), 1.,
                 ratio.GetXaxis().GetBinUpEdge(ratio.GetXaxis().GetLast()), 1.);
    line.SetLineWidth(2);
    line.SetLineStyle(2);
    line.SetLineColor(kRed+1);
    line.Draw();
    pads[canvas.pad_nr].ratio.line = line

    update_pad()

    cd(canvas.pad_nr + 1) # pad_nr starts at 0



def plot(histogram_name):
    """Compose and draw a plot using the histograms called histogram_name."""

    # check for existing cfg file
    if objects.cfg is None:
        print "No config file loaded! Use setup('canvas.cfg')"
        return

    # check for existing selection
    if settings.ana_dir is "":
        print "No selection done yet. Use selection('insert_run_name')"
        return

    # check for existing canvas
    if canvas.canvas is None:
        create_canvas()

    delete_pad_objects() # delete old objects of the pad
    read_processes(histogram_name) # load histogram of the processes
    draw_processes() # draw the histograms
    cd(canvas.pad_nr + 1) # pad_nr starts at 0



def save(file_name = ""):
    """Saves the current TCanvas into a file with the name file_name. By default,
    the histogram's name is being used and saved as a '.pdf' to the subfolder 'plots'."""
    
    if not file_name:
        file_name = "plots/" + get_draw_object().GetName().replace(settings.hist_prefix, "") + ".pdf"
    
    path = ("./" + file_name).rsplit("/", 1)[0]
    if not os.path.exists(path):
        os.makedirs(path)
    canvas.canvas.SaveAs(file_name)

    

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
    'export.py'. If no function_title is given, the histogram title will be used."""

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
            # get the title of the histogram
            function_title = item.split('"', 1)[1].rsplit('"', 1)[0]
            plot_index = i
            break

    # check if there was a plot(...)
    if plot_index == 0:
        print "Could not find an instance of plot(...)!"
        return

    # add some additional lines if the options are given
    if export_selection:
        line_buffer.append("selection(\"" + settings.ana_dir + "\")")

    if export_setup:
        line_buffer.append("selection(\"" + objects.cfg.filename.split("/")[2] + "\")")

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

