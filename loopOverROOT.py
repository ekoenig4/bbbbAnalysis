import pandas as pd
from ROOT import TFile
import ROOT
import matplotlib.pyplot as plt
import pickle
import numpy as np


directory = 'root://cmseos.fnal.gov//store/user/srosenzw/bbbb_ntuples/'
jobtitle = 'fastSim_maxDeltaR-pt25_mH-125'
mass_point = jobtitle + '/SKIM_NMSSM_XYH_bbbb_MX_700_NANOAOD_v7_MY_300/output/bbbbNtuple_0.root'

def goLoop(filename,treename,branches):
    """
    branches = list of names (strings) of branches
    """

    f = TFile.Open(filename)
    t = f.Get(treename)
    length = int(t.GetEntries())

    empty_lists = [[] for i in range(len(branches))]

    count = 0 
    for evt in t:
        # if count > 10: continue
        if count % 100 == 0: print('Looping over event # {} / {}'.format(count,length)) 
        for i,branch in enumerate(branches):
            try: 
                val = int(getattr(evt,branch))
                val = float(getattr(evt,branch))
                empty_lists[i].append(val)
            except:
                # print("{}: EXCEPT".format(i))
                for j in range(len(getattr(evt,branch))):
                    # print("Adding {} to emptylist[{}]".format(getattr(evt,branch)[j],i))
                    empty_lists[i].append(getattr(evt,branch)[j])
        count += 1

    return empty_lists

gen_data = ['nGenJet', 'gen_jet_pt','gen_jet_eta', 'gen_jet_phi','gen_jet_m','gen_H1_b1_eta', 'gen_H1_b1_phi',  'gen_H1_b2_eta','gen_H1_b2_phi', 'gen_H2_b1_eta','gen_H2_b1_phi', 'gen_H2_b2_eta','gen_H2_b2_phi', 'gen_H1_b1_pt', 'gen_H1_b2_pt', 'gen_H2_b1_pt', 'gen_H2_b2_pt']

# reco_data = ['nJet', 'jet_pt', 'jet_eta', 'jet_phi', 'jet_bTagScore', 'jet_jetID', 'jet_PUID', 'H1_b1_pt', 'H1_b1_eta', 'H1_b1_phi', 'H1_b2_pt', 'H1_b2_eta', 'H1_b2_phi', 'H2_b1_pt', 'H2_b1_eta', 'H2_b1_phi', 'H2_b2_pt', 'H2_b2_eta', 'H2_b2_phi']

# Analysis data
reco_data = ['nJet', 'jet_pt', 'jet_eta', 'jet_phi', 'jet_bTagScore', 'jet_jetID', 'jet_PUID', 'H1_b1_pt', 'H1_b1_eta', 'H1_b1_phi', 'H1_b2_pt', 'H1_b2_eta', 'H1_b2_phi', 'H2_b1_pt', 'H2_b1_eta', 'H2_b1_phi', 'H2_b2_pt', 'H2_b2_eta', 'H2_b2_phi', 'gen_H1_b1_matchedflag', 'gen_H1_b2_matchedflag', 'gen_H2_b1_matchedflag', 'gen_H2_b2_matchedflag', 'recoJetMatchedToGenJet1', 'recoJetMatchedToGenJet2', 'recoJetMatchedToGenJet3', 'recoJetMatchedToGenJet4', 'jet_pt_smeared', 'jet_eta_smeared', 'jet_phi_smeared', 'jcu']

gen_and_reco = gen_data + reco_data

lists = goLoop('test_NMSSM_XYH_bbbb_MC_20200504_withjcu.root', 'bbbbTree', reco_data)
 
# np.savez('gen_data', nGenJet=lists[0], gen_jet_pt=lists[1], gen_jet_eta=lists[2], gen_jet_phi=lists[3],gen_jet_m=lists[4], gen_H1_b1_eta=lists[5], gen_H1_b1_phi=lists[6], gen_H1_b2_eta=lists[7], gen_H1_b2_phi=lists[8], gen_H2_b1_eta=lists[9], gen_H2_b1_phi=lists[10], gen_H2_b2_eta=lists[11],gen_H2_b2_phi=lists[12], gen_H1_b1_pt=lists[13], gen_H1_b2_pt=lists[14], gen_H2_b1_pt=lists[15], gen_H2_b2_pt=lists[16] )
# np.savez('reco_data', nJet=lists[17], jet_pt=lists[18], jet_eta=lists[19], jet_phi=lists[20], jet_bTagScore=lists[21], jet_jetID=lists[22], jet_PUID=lists[23], H1_b1_pt=lists[24], H1_b1_eta=lists[25], H1_b1_phi=lists[26], H1_b2_pt=lists[27], H1_b2_eta=lists[28], H1_b2_phi=lists[29], H2_b1_pt=lists[30], H2_b1_eta=lists[31], H2_b1_phi=lists[32], H2_b2_pt=lists[33], H2_b2_eta=lists[34], H2_b2_phi=lists[35], jet_pt_smeared=lists[44], jet_eta_smeared=lists[45], jet_phi_smeared=lists[46], jcu=lists[47])


np.savez('analysis', nJet=lists[0], jet_pt=lists[1], jet_eta=lists[2], jet_phi=lists[3], jet_bTagScore=lists[4], jet_jetID=lists[5], jet_PUID=lists[6], H1_b1_pt=lists[7], H1_b1_eta=lists[8], H1_b1_phi=lists[9], H1_b2_pt=lists[10], H1_b2_eta=lists[11], H1_b2_phi=lists[12], H2_b1_pt=lists[13], H2_b1_eta=lists[14], H2_b1_phi=lists[15], H2_b2_pt=lists[16], H2_b2_eta=lists[17], H2_b2_phi=lists[18], gen_H1_b1_matchedflag=lists[19], gen_H1_b2_matchedflag=lists[20], gen_H2_b1_matchedflag=lists[21], gen_H2_b2_matchedflag=lists[22], recoJetMatchedToGenJet1=lists[23], recoJetMatchedToGenJet2=lists[24], recoJetMatchedToGenJet3=lists[25], recoJetMatchedToGenJet4=lists[26], jet_pt_smeared=lists[27], jet_eta_smeared=lists[28], jet_phi_smeared=lists[29], jec=lists[30])

