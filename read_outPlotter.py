import numpy as np
from ROOT import TFile
import pandas as pd
import matplotlib.pyplot as plt
from GenHisto import Histogram
import argparse
import os
import sys, fileinput

mx = np.load("mX_values.npz")
my = np.load("mY_values.npz")

mx = np.append(mx['arr_0'],2000)
my = np.append(my['arr_0'],1600)
my = np.append(my,1800)

directory = 'plotterListFiles/2016Resonant_NMSSM_XYH_bbbb/'

def replaceLines(f, arg1, arg2):
    for line in f:
        line = line.replace(arg1, arg2)
        sys.stdout.write(line)

def rewriteFiles(old_job, new_job):

    print("[INFO] Rewriting job tag in plotterListFiles...")

    for mX in mx:
        for mY in my:
            filename = 'FileList_NMSSM_XYH_bbbb_MX_{}_MY_{}_Fast.txt'.format(str(mX),str(mY)) 
            file_path = directory + filename 
            # print("[INFO] Opening file {}".format(filename))
            try: 
                f = fileinput.input(file_path, inplace=True)
                replaceLines(f, old_job, new_job)
            except: continue
    
    filename = 'BTagCSV_Data_FileList_NMSSM_XYH_bbbb_Suz.txt'
    print("[INFO] Rewriting job tag in file {}".format(filename))
    file_path = directory + filename
    f = fileinput.input(file_path, inplace=True)
    replaceLines(f, old_job, new_job)

    filename = 'config/Resonant_NMSSM_bbbb/MXless1000_MYgreater140/plotter_2016Resonant_NMSSM_XYH_bbbb.cfg'
    print("[INFO] Rewriting job tag in file {}".format(filename))
    f = fileinput.input(filename, inplace=True)
    replaceLines(f, old_job, new_job)



parser = argparse.ArgumentParser(description='Command line parser of running options')
parser.add_argument('--job_tag',          dest='job_tag',      help='tag used to ID job',         default=None)
args = parser.parse_args()
print(args.job_tag)

# Rewrite FileLists so reflect new job tag.
old_job_tag = 'fastSim_maxDeltaR-pt25_mH-125' # Change this to the old job tag
job_tag     = 'fastSim_DeepFlavB_v3' # Change this to the new job tag
rewriteFiles(old_job_tag, job_tag)

if not os.path.exists('2016DataPlots_NMSSM_XYH_bbbb_Fast_{}'.format(job_tag)):
    os.system("fill_histograms.exe config/Resonant_NMSSM_bbbb/MXless1000_MYgreater140/plotter_2016Resonant_NMSSM_XYH_bbbb.cfg")
else:
    inp = raw_input("Directory with job tag already exists. To proceed with plotting, press any key. To exit, type 'exit'.")
    print('test')
    if inp == 'exit': 
        sys.exit("Program ended by user.")

filename = '2016DataPlots_NMSSM_XYH_bbbb_Fast_{}/outPlotter.root'.format(job_tag)
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

df_eff_sel = df.pivot(index='mY',columns='mX',values='eff_sel')
df_pur_sel = df.pivot(index='mY',columns='mX',values='pur_sel')
df_alt_pur_sel = df.pivot(index='mY',columns='mX',values='alt_pur_sel')

print("[INFO] Plotting efficiencies...")

hist_eff_sel = Histogram(filesave='eff_sel_{}.pdf'.format(job_tag), xdata=df_eff_sel, isDataFrame=True, label=True, comap='rainbow', vmin=0.0, vmax=1.0, fmt='.3f', labelsize=10, title='Efficiency')
hist_eff_sel.saveHist('eff_sel_{}.pdf'.format(job_tag))

print("[INFO] Plotting purities...")
hist_pur_sel = Histogram(filesave='pur_HY_sel_{}.pdf'.format(job_tag), xdata=df_pur_sel, isDataFrame=True, label=True, comap='rainbow', vmin=0.0, vmax=1.0, fmt='.3f', labelsize=10, title='Purity (gen matching per candidate)')
hist_pur_sel.saveHist('pur_HY_sel_{}.pdf'.format(job_tag))

hist_eff_sel_alt = Histogram(filesave='pur_jet_sel_{}.pdf'.format(job_tag), xdata=df_alt_pur_sel, isDataFrame=True, label=True, comap='rainbow', vmin=0.0, vmax=1.0, fmt='.3f', labelsize=10, title='Purity (gen matching per jet)')
hist_eff_sel_alt.saveHist('pur_jet_sel_{}.pdf'.format(job_tag))




# pdf.close()