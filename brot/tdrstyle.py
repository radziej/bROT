from ROOT import gStyle

def set_tdr_style():
    """Recommended plotting parameters are being set."""

    print "Using the TDR plotting style."
    # canvas
    gStyle.SetCanvasBorderMode(0)
    gStyle.SetCanvasColor(0)
    gStyle.SetCanvasDefH(600)
    gStyle.SetCanvasDefW(600)
    gStyle.SetCanvasDefX(0)
    gStyle.SetCanvasDefY(0)

    # pad
    gStyle.SetPadBorderMode(0)
    # gStyle.SetPadBorderSize(Width_t size = 1)
    gStyle.SetPadColor(0)
    gStyle.SetPadGridX(False)
    gStyle.SetPadGridY(False)
    gStyle.SetGridColor(0)
    gStyle.SetGridStyle(3)
    gStyle.SetGridWidth(1)

    # margins
    gStyle.SetPadTopMargin(0.06)
    gStyle.SetPadBottomMargin(0.13)
    gStyle.SetPadLeftMargin(0.13)
    gStyle.SetPadRightMargin(0.05)

    # frame
    gStyle.SetFrameBorderMode(0)
    gStyle.SetFrameBorderSize(1)
    gStyle.SetFrameFillColor(0)
    gStyle.SetFrameFillStyle(0)
    gStyle.SetFrameLineColor(1)
    gStyle.SetFrameLineStyle(1)
    gStyle.SetFrameLineWidth(1)

    # histo
    # gStyle.SetHistFillColor(63)
    # gStyle.SetHistFillStyle(0)
    gStyle.SetHistLineColor(1)
    gStyle.SetHistLineStyle(0)
    gStyle.SetHistLineWidth(1)
    # gStyle.SetLegoInnerR(Float_t rad = 0.5)
    # gStyle.SetNumberContours(Int_t number = 20)

    # gStyle.SetEndErrorSize(0)
    # gStyle.SetErrorX(0.)
    # gStyle.SetErrorMarker(20)

    # gStyle.SetMarkerStyle(20)

    # fit/function
    gStyle.SetOptFit(1)
    gStyle.SetFitFormat("5.4g")
    gStyle.SetFuncColor(2)
    gStyle.SetFuncStyle(1)
    gStyle.SetFuncWidth(1)

    # date
    gStyle.SetOptDate(0)
    # gStyle.SetDateX(Float_t x = 0.01)
    # gStyle.SetDateY(Float_t y = 0.01)

    # statistics box
    gStyle.SetOptFile(0)
    gStyle.SetOptStat(0) # To display the mean and RMS:   SetOptStat("mr")
    gStyle.SetStatColor(0)
    gStyle.SetStatFont(42)
    gStyle.SetStatFontSize(0.025)
    gStyle.SetStatTextColor(1)
    gStyle.SetStatFormat("6.4g")
    gStyle.SetStatBorderSize(1)
    gStyle.SetStatH(0.1)
    gStyle.SetStatW(0.15)
    # gStyle.SetStatStyle(Style_t style = 1001)
    # gStyle.SetStatX(Float_t x = 0)
    # gStyle.SetStatY(Float_t y = 0)

    # global title
    gStyle.SetOptTitle(0)
    gStyle.SetTitleFont(42)
    gStyle.SetTitleColor(1)
    gStyle.SetTitleTextColor(1)
    gStyle.SetTitleFillColor(10)
    gStyle.SetTitleFontSize(0.05)
    # gStyle.SetTitleH(0) # Set the height of the title box
    # gStyle.SetTitleW(0) # Set the width of the title box
    # gStyle.SetTitleX(0) # Set the position of the title box
    # gStyle.SetTitleY(0.985) # Set the position of the title box
    # gStyle.SetTitleStyle(Style_t style = 1001)
    # gStyle.SetTitleBorderSize(2)

    # axis titles
    gStyle.SetTitleColor(1, "XYZ")
    gStyle.SetTitleFont(42, "XYZ")
    gStyle.SetTitleSize(0.06, "XYZ")
    # gStyle.SetTitleXSize(Float_t size = 0.02)
    # gStyle.SetTitleYSize(Float_t size = 0.02)
    gStyle.SetTitleXOffset(0.9)
    gStyle.SetTitleYOffset(1.05)
    # gStyle.SetTitleOffset(1.1, "Y") # Another way to set the Offset

    # axis labels
    gStyle.SetLabelColor(1, "XYZ")
    gStyle.SetLabelFont(42, "XYZ")
    gStyle.SetLabelOffset(0.007, "XYZ")
    gStyle.SetLabelSize(0.05, "XYZ")

    # axis
    gStyle.SetAxisColor(1, "XYZ")
    gStyle.SetStripDecimals(1)
    gStyle.SetTickLength(0.03, "XYZ")
    gStyle.SetNdivisions(508, "XYZ")
    gStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
    gStyle.SetPadTickY(1)

    # log plots
    gStyle.SetOptLogx(0)
    gStyle.SetOptLogy(0)
    gStyle.SetOptLogz(0)

    # legend
    gStyle.SetLegendBorderSize(0)
    gStyle.SetLegendFillColor(0)
    gStyle.SetLegendFont(42)

    # Postscript options:
    # gStyle.SetPaperSize(15.,15.)
    # gStyle.SetLineScalePS(Float_t scale = 3)
    # gStyle.SetLineStyleString(Int_t i, const char* text)
    # gStyle.SetHeaderPS(const char* header)
    # gStyle.SetTitlePS(const char* pstitle)

    # gStyle.SetBarOffset(Float_t baroff = 0.5)
    # gStyle.SetBarWidth(Float_t barwidth = 0.5)
    # gStyle.SetPaintTextFormat(const char* format = "g")
    # gStyle.SetPalette(Int_t ncolors = 0, Int_t* colors = 0)
    # gStyle.SetTimeOffset(Double_t toffset)
    # gStyle.SetHistMinimumZero(kTRUE)
