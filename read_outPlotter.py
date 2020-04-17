import numpy as np
from ROOT import TFile
import pandas as pd
import matplotlib.pyplot as plt
# from matplotlib import cm
# from matplotlib.colors import ListedColormap
from GenHisto import Histogram
# import matplotlib.backends.backend_pdf
# pdf = matplotlib.backends.backend_pdf.PdfPages("eff_and_pur_v6.pdf")

# # This block of code causes bins with zero value to appear as white.
# col_map = cm.get_cmap('rainbow', 256)
# newcolors = col_map(np.linspace(0, 1, 256))
# white = np.array([1, 1, 1, 1])    # White background (Red, Green, Blue, Alpha).
# newcolors[0, :] = white    # Only change bins with 0 entries.
# newcmp = ListedColormap(newcolors)

filename = '2016DataPlots_NMSSM_XYH_bbbb_Fast_fastSim_v6_swapHY/outPlotter.root '

print("[INFO] Opening file {}".format(filename))
f = TFile(filename)

mX = np.arange(300,900,100)
mY = np.array([60,70,80,90,100,125,150,200,250,300,400,500,600,700])

print("[INFO] Creating Pandas DataFrame....")
df = pd.DataFrame(columns=['mX','mY','Ntot_w','Ntrig_w','Nsel_w','selectionbJets_ControlRegion','selectionbJets_SideBandRegion','selectionbJets_SignalRegion','selectionbJets_genMatched_ControlRegion','selectionbJets_genMatched_SideBandRegion','selectionbJets_genMatched_SignalRegion','eff_tot','eff_trig','eff_sel','pur_tot','pur_trig','pur_sel','alt_pur_sel'])

print("[INFO] Looping over directories in {}".format(filename))
for MX in mX:
    for MY in mY: 
        MX_s, MY_s = str(MX), str(MY)
        name = 'sig_NMSSM_bbbb_MX_' + MX_s + '_MY_' + MY_s
        try:
            t = f.Get(name)
            h = t.Get(name)
        except: continue

        Ntot_w                        = h.GetBinContent(1)
        Ntrig_w                       = h.GetBinContent(2)
        Nsel_w                        = h.GetBinContent(3)
        selectionbJets_ControlRegion  = h.GetBinContent(4)
        selectionbJets_SideBandRegion = h.GetBinContent(5)
        selectionbJets_SignalRegion   = h.GetBinContent(6)
        selectionbJets_genMatched_ControlRegion = h.GetBinContent(7)
        selectionbJets_genMatched_SideBandRegion = h.GetBinContent(8)
        selectionbJets_genMatched_SignalRegion = h.GetBinContent(9)
        selectionbJets_genMatchedjet_SignalRegion = h.GetBinContent(12)

        eff_tot = selectionbJets_SignalRegion / Ntot_w
        eff_trig = selectionbJets_SignalRegion / Ntrig_w
        eff_sel = selectionbJets_SignalRegion / Nsel_w

        pur_tot = selectionbJets_genMatched_SignalRegion / Ntot_w
        pur_trig = selectionbJets_genMatched_SignalRegion / Ntrig_w
        pur_sel = selectionbJets_genMatched_SignalRegion / selectionbJets_SignalRegion

        alt_pur_sel = selectionbJets_genMatchedjet_SignalRegion / selectionbJets_SignalRegion


        df = df.append({'mX':MX, 'mY':MY, 'Ntot_w':Ntot_w, 'Nsel_w':Nsel_w,'selectionbJets_ControlRegion':selectionbJets_ControlRegion, 'selectionbJets_SideBandRegion':selectionbJets_SideBandRegion,'selectionbJets_SignalRegion':selectionbJets_SignalRegion, 'selectionbJets_genMatched_ControlRegion':selectionbJets_genMatched_ControlRegion, 'selectionbJets_genMatched_SideBandRegion':selectionbJets_genMatched_SideBandRegion, 'selectionbJets_genMatched_SignalRegion':selectionbJets_genMatched_SignalRegion, 'eff_tot':eff_tot, 'eff_trig':eff_trig, 'eff_sel':eff_sel,'pur_tot':pur_tot, 'pur_trig':pur_trig, 'pur_sel':pur_sel, 'alt_pur_sel':alt_pur_sel}, ignore_index=True)

# print("[INFO] Saving Pandas DataFrame to {}".format("outPlotter_efficiencies.csv"))
# df.to_csv("outPlotter_efficiencies.csv",index=False) # Save DataFrame values as csv.

tag = '_fastSim_v6'

df_eff_sel = df.pivot(index='mY',columns='mX',values='eff_sel')
df_pur_sel = df.pivot(index='mY',columns='mX',values='pur_sel')
df_alt_pur_sel = df.pivot(index='mY',columns='mX',values='alt_pur_sel')

print(df_eff_sel)
print(df_pur_sel)
print(df_alt_pur_sel)

print("[INFO] Plotting efficiencies...")

hist_eff_sel = Histogram(filesave='eff_sel{}.pdf'.format(tag), xdata=df_eff_sel, isDataFrame=True, label=True, comap='rainbow', vmin=0.0, vmax=1.0, fmt='.3f', labelsize=10, title='Efficiency, mH=125 GeV')
hist_eff_sel.saveHist('eff_HYswap.png')

print("[INFO] Plotting purities...")
hist_pur_sel = Histogram(filesave='pur_sel.pdf', xdata=df_pur_sel, isDataFrame=True, label=True, comap='rainbow', vmin=0.0, vmax=1.0, fmt='.3f', labelsize=10, title='Purity (gen matching per candidate)')
hist_pur_sel.saveHist('pur_HYswap.png')

hist_eff_sel_alt = Histogram(filesave='alt_pur_sel.pdf', xdata=df_alt_pur_sel, isDataFrame=True, label=True, comap='rainbow', vmin=0.0, vmax=1.0, fmt='.3f', labelsize=10, title='Purity (gen matching per jet)')
hist_eff_sel_alt.saveHist('pur2_HYswap.png')




# pdf.close()