import pandas as pd
from ROOT import TFile
import ROOT
import matplotlib.pyplot as plt
import pickle

def goLoop(filename,treename,branches,min_cuts=None,max_cuts=None):
    """
    branches = list of names (strings) of branches
    min_cuts = dictionary of branches and their desired min values
    max_cuts = dictionary of branches and their desired max values
    """

    f = TFile(filename)
    t = f.Get(treename)

    df = pd.DataFrame(columns=branches)
    empty_lists = [[] for i in range(len(branches))]

    count = 0 
    for evt in t:
        # if count > 10: continue
        if min_cuts != None:
            # print("I should not be printing.")
            for cut in min_cuts:
                if getattr(evt, cut) < min_cuts[i]: continue # This is wrong. Should be reading a dict.
        if max_cuts != None:
            # print("Neither should I.")
            for cut in max_cuts:
                if getattr(evt, cut) < max_cuts[i]: continue # This is wrong. Should read a dict.
        for i,branch in enumerate(branches):
            # print("Adding to df...")
            # print(i,branch)
            df = df.append({branch:getattr(evt,branch)},ignore_index=True)
            try: 
                val = int(getattr(evt,branch))
                empty_lists[i].append(val)
                # print("Adding {} to emptylist[{}]".format(val,i))
            except:
                for j in range(len(getattr(evt,branch))):
                    # print("Adding {} to emptylist[{}]".format(getattr(evt,branch)[j],i))
                    empty_lists[i].append(getattr(evt,branch)[j])
            # print(getattr(evt,branch))
        # print(evt.gen_jet_pt.size())
        # for i in range(evt.gen_jet_pt.size()):
            # print(evt.gen_jet_pt[i])
        count += 1
    # print(empty_lists[0])

    return empty_lists


lists = goLoop('test_NMSSM_XYH_bbbb_MC_selectedJets_test_nocuts.root', 'bbbbTree', ['nJet','gen_jet_pt','gen_jet_eta','gen_jet_phi','gen_jet_m'])

with open("gen_jet_pt.txt","wb") as fb:
    pickle.dump(lists[1],fb)
with open("gen_jet_eta.txt","wb") as fb:
    pickle.dump(lists[2],fb)
with open("gen_jet_phi.txt","wb") as fb:
    pickle.dump(lists[3],fb)
with open("gen_jet_m.txt","wb") as fb:
    pickle.dump(lists[4],fb)

# print(df['gen_jet_pt'][0:10])
# plt.hist(df['nJet'])
# plt.show()   

# plt.hist(lists[1],bins=100)
# plt.semilogy()
# plt.show()