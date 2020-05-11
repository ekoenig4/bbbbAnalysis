import numpy as np
import matplotlib.pyplot as plt

gen_data = np.load("gen_data.npz") # Generated events
analysis = np.load("analysis.npz") # Selected reconstructed events (analysis selections have been done)

swap_flag = True

def orderbypt(H1b1, H1b2, H2b1, H2b2, gen_or_sel):
    global swap_flag # Ensures that the reco swap only occurs once
    temp_flag = False # Ensures that the swap_flag isn't changed while still processing data.

    H1_b1_ordered, H1_b2_ordered, H2_b1_ordered, H2_b2_ordered = [], [], [], []

    if gen_or_sel == 'gen': 
        print "[INFO] Ordering generated kinematics by pT."
        H1b1_pt, H1b2_pt, H2b1_pt, H2b2_pt = gen_data['gen_H1_b1_pt'], gen_data['gen_H1_b2_pt'], gen_data['gen_H2_b1_pt'], gen_data['gen_H2_b2_pt']
    elif gen_or_sel == 'sel':
        print "[INFO] Ordering analysis kinematics by pT."
        H1b1_pt, H1b2_pt, H2b1_pt, H2b2_pt = analysis['H1_b1_pt'], analysis['H1_b2_pt'], analysis['H2_b1_pt'], analysis['H2_b2_pt']
    elif gen_or_sel == 'sel_gen':
        print "[INFO] Ordering analysis gen kinematics by pT."
        H1b1_pt, H1b2_pt, H2b1_pt, H2b2_pt = analysis['gen_H1_b1_pt'], analysis['gen_H1_b2_pt'], analysis['gen_H2_b1_pt'], analysis['gen_H2_b2_pt']
    else:
        print "User has entered an unknown datset. Please enter 'gen' or 'sel' to perform ordering."
        return 0

    count = 0
    for Hb1, Hb2, Yb1, Yb2 in zip(H1b1_pt, H1b2_pt, H2b1_pt, H2b2_pt):
        if Hb1 > Hb2:
            H1_b1_ordered.append(H1b1[count])
            H1_b2_ordered.append(H1b2[count])
        else:
            H1_b1_ordered.append(H1b2[count])
            H1_b2_ordered.append(H1b1[count])
            if gen_or_sel == 'sel' and swap_flag:
                # Swap the index of any gen jets matched to the swapped reco jets

                if ana_H1_b1_matchedflag[count] == 0: ana_H1_b1_matchedflag[count] = 1
                elif ana_H1_b1_matchedflag[count] == 1: ana_H1_b1_matchedflag[count] = 0
                if ana_H1_b2_matchedflag[count] == 0: ana_H1_b2_matchedflag[count] = 1
                elif ana_H1_b2_matchedflag[count] == 1: ana_H1_b2_matchedflag[count] = 0

                if ana_H1_b1_matchedjet[count] == 0: ana_H1_b1_matchedjet[count] = 1
                elif ana_H1_b1_matchedjet[count] == 1: ana_H1_b1_matchedjet[count] = 0
                if ana_H1_b2_matchedjet[count] == 0: ana_H1_b2_matchedjet[count] = 1
                elif ana_H1_b2_matchedjet[count] == 1: ana_H1_b2_matchedjet[count] = 0
                if ana_H2_b1_matchedjet[count] == 0: ana_H2_b1_matchedjet[count] = 1
                elif ana_H2_b1_matchedjet[count] == 1: ana_H2_b1_matchedjet[count] = 0
                if ana_H2_b2_matchedjet[count] == 0: ana_H2_b2_matchedjet[count] = 1
                elif ana_H2_b2_matchedjet[count] == 1: ana_H2_b2_matchedjet[count] = 0

                temp_flag = True

        if Yb1 > Yb2:
            H2_b1_ordered.append(H2b1[count])
            H2_b2_ordered.append(H2b2[count])
        else:
            H2_b1_ordered.append(H2b2[count])
            H2_b2_ordered.append(H2b1[count])
            if gen_or_sel == 'sel' and swap_flag:
                if ana_H2_b1_matchedflag[count] == 0: ana_H2_b1_matchedflag[count] = 1
                elif ana_H2_b1_matchedflag[count] == 1: ana_H2_b1_matchedflag[count] = 0
                if ana_H2_b2_matchedflag[count] == 0: ana_H2_b2_matchedflag[count] = 1
                elif ana_H2_b2_matchedflag[count] == 1: ana_H2_b2_matchedflag[count] = 0

                if ana_H1_b1_matchedjet[count] == 2: ana_H1_b1_matchedjet[count] = 3
                elif ana_H1_b1_matchedjet[count] == 3: ana_H1_b1_matchedjet[count] = 2
                if ana_H1_b2_matchedjet[count] == 2: ana_H1_b2_matchedjet[count] = 3
                elif ana_H1_b2_matchedjet[count] == 3: ana_H1_b2_matchedjet[count] = 2
                if ana_H2_b1_matchedjet[count] == 2: ana_H2_b1_matchedjet[count] = 3
                elif ana_H2_b1_matchedjet[count] == 3: ana_H2_b1_matchedjet[count] = 2
                if ana_H2_b2_matchedjet[count] == 2: ana_H2_b2_matchedjet[count] = 3
                elif ana_H2_b2_matchedjet[count] == 3: ana_H2_b2_matchedjet[count] = 2

                temp_flag = True
        count += 1
    if temp_flag: swap_flag = False
    return np.asarray(H1_b1_ordered), np.asarray(H1_b2_ordered), np.asarray(H2_b1_ordered), np.asarray(H2_b2_ordered)

# All gen b jets.
gen_H1_b1_pt, gen_H1_b2_pt, gen_H2_b1_pt, gen_H2_b2_pt = orderbypt(gen_data['gen_H1_b1_pt'], gen_data['gen_H1_b2_pt'], gen_data['gen_H2_b1_pt'], gen_data['gen_H2_b2_pt'], 'gen')

gen_H1_b1_eta, gen_H1_b2_eta, gen_H2_b1_eta, gen_H2_b2_eta = orderbypt(gen_data['gen_H1_b1_eta'], gen_data['gen_H1_b2_eta'], gen_data['gen_H2_b1_eta'], gen_data['gen_H2_b2_eta'], 'gen')

gen_H1_b1_phi, gen_H1_b2_phi, gen_H2_b1_phi, gen_H2_b2_phi = orderbypt(gen_data['gen_H1_b1_phi'], gen_data['gen_H1_b2_phi'], gen_data['gen_H2_b1_phi'], gen_data['gen_H2_b2_phi'], 'gen')

# Matched gen b jets.
ana_gen_H1_b1_pt, ana_gen_H1_b2_pt, ana_gen_H2_b1_pt, ana_gen_H2_b2_pt = orderbypt(analysis['gen_H1_b1_pt'], analysis['gen_H1_b2_pt'], analysis['gen_H2_b1_pt'], analysis['gen_H2_b2_pt'], 'sel_gen')

ana_gen_H1_b1_eta, ana_gen_H1_b2_eta, ana_gen_H2_b1_eta, ana_gen_H2_b2_eta = orderbypt(analysis['gen_H1_b1_eta'], analysis['gen_H1_b2_eta'], analysis['gen_H2_b1_eta'], analysis['gen_H2_b2_eta'], 'sel_gen')

ana_gen_H1_b1_phi, ana_gen_H1_b2_phi, ana_gen_H2_b1_phi, ana_gen_H2_b2_phi = orderbypt(analysis['gen_H1_b1_phi'], analysis['gen_H1_b2_phi'], analysis['gen_H2_b1_phi'], analysis['gen_H2_b2_phi'], 'sel_gen')

ana_H1_b1_matchedflag, ana_H1_b2_matchedflag, ana_H2_b1_matchedflag, ana_H2_b2_matchedflag = orderbypt(analysis['gen_H1_b1_matchedflag'], analysis['gen_H1_b2_matchedflag'], analysis['gen_H2_b1_matchedflag'], analysis['gen_H2_b2_matchedflag'], 'sel_gen')

# print ana_H1_b1_matchedflag[0:20]

# count = 0
# for i in range(len(ana_gen_H1_b1_pt)):
#     if ana_H1_b1_matchedflag[i] == analysis['gen_H1_b1_matchedflag'][i]:# or ana_H1_b1_matchedflag[i] == analysis['gen_H1_b2_matchedflag'][i]:
#         count += 1
# print count
# print "Compared to the length..."
# print len(ana_gen_H1_b1_pt)

ana_H1_b1_matchedjet, ana_H1_b2_matchedjet, ana_H2_b1_matchedjet, ana_H2_b2_matchedjet = orderbypt(analysis['gen_H1_b1_matchedjet'], analysis['gen_H1_b2_matchedjet'], analysis['gen_H2_b1_matchedjet'], analysis['gen_H2_b2_matchedjet'], 'sel_gen')

# Selected b jets
ana_H1_b1_pt, ana_H1_b2_pt, ana_H2_b1_pt, ana_H2_b2_pt = orderbypt(analysis['H1_b1_pt'], analysis['H1_b2_pt'], analysis['H2_b1_pt'], analysis['H2_b2_pt'], 'sel')

ana_H1_b1_eta, ana_H1_b2_eta, ana_H2_b1_eta, ana_H2_b2_eta = orderbypt(analysis['H1_b1_eta'], analysis['H1_b2_eta'], analysis['H2_b1_eta'], analysis['H2_b2_eta'], 'sel')

ana_H1_b1_phi, ana_H1_b2_phi, ana_H2_b1_phi, ana_H2_b2_phi = orderbypt(analysis['H1_b1_phi'], analysis['H1_b2_phi'], analysis['H2_b1_phi'], analysis['H2_b2_phi'], 'sel')

ana_H1_b1_btag, ana_H1_b2_btag, ana_H2_b1_btag, ana_H2_b2_btag = orderbypt(analysis['H1_b1_deepCSV'], analysis['H1_b2_deepCSV'], analysis['H2_b1_deepCSV'], analysis['H2_b2_deepCSV'], 'sel')

ana_H1_b1_jetID, ana_H1_b2_jetID, ana_H2_b1_jetID, ana_H2_b2_jetID = orderbypt(analysis['H1_b1_jetId'], analysis['H1_b2_jetId'], analysis['H2_b1_jetId'], analysis['H2_b2_jetId'], 'sel')

ana_H1_b1_PUID, ana_H1_b2_PUID, ana_H2_b1_PUID, ana_H2_b2_PUID = orderbypt(analysis['H1_b1_puId'], analysis['H1_b2_puId'], analysis['H2_b1_puId'], analysis['H2_b2_puId'], 'sel')

# print ana_H1_b1_matchedflag[0:20]
# print analysis['H1_b1_pt'][0:20]
# print ana_H1_b1_pt[0:20]

# count = 0
# for i in range(len(ana_H1_b1_pt)):
#     if ana_H1_b1_matchedflag[i] == analysis['gen_H1_b1_matchedflag'][i]:# or ana_H1_b1_matchedflag[i] == analysis['gen_H1_b2_matchedflag'][i]:
#         count += 1
# print count
# print "Compared to the length..."
# print len(ana_H1_b1_pt)


print "Saving ordered generated data as gen_ordered.npz"
np.savez("gen_ordered", gen_H1_b1_pt=gen_H1_b1_pt, gen_H1_b2_pt=gen_H1_b2_pt, gen_H2_b1_pt=gen_H2_b1_pt, gen_H2_b2_pt=gen_H2_b2_pt, gen_H1_b1_eta=gen_H1_b1_eta, gen_H1_b2_eta=gen_H1_b2_eta, gen_H2_b1_eta=gen_H2_b1_eta, gen_H2_b2_eta=gen_H2_b2_eta, gen_H1_b1_phi=gen_H1_b1_phi, gen_H1_b2_phi=gen_H1_b2_phi, gen_H2_b1_phi=gen_H2_b1_phi, gen_H2_b2_phi=gen_H2_b2_phi)

print "Saving ordered analyzed data as analysis_ordered.npz"
np.savez("analysis_ordered", gen_H1_b1_pt=ana_gen_H1_b1_pt, gen_H1_b2_pt=ana_gen_H1_b2_pt, gen_H2_b1_pt=ana_gen_H2_b1_pt, gen_H2_b2_pt=ana_gen_H2_b2_pt, gen_H1_b1_eta=ana_gen_H1_b1_eta, gen_H1_b2_eta=ana_gen_H1_b2_eta, gen_H2_b1_eta=ana_gen_H2_b1_eta, gen_H2_b2_eta=ana_gen_H2_b2_eta, gen_H1_b1_phi=ana_gen_H1_b1_phi, gen_H1_b2_phi=ana_gen_H1_b2_phi, gen_H2_b1_phi=ana_gen_H2_b1_phi, gen_H2_b2_phi=ana_gen_H2_b2_phi, H1_b1_pt=ana_H1_b1_pt, H1_b2_pt=ana_H1_b2_pt, H2_b1_pt=ana_H2_b1_pt, H2_b2_pt=ana_H2_b2_pt, H1_b1_eta=ana_H1_b1_eta, H1_b2_eta=ana_H1_b2_eta, H2_b1_eta=ana_H2_b1_eta, H2_b2_eta=ana_H2_b2_eta, H1_b1_phi=ana_H1_b1_phi, H1_b2_phi=ana_H1_b2_phi, H2_b1_phi=ana_H2_b1_phi, H2_b2_phi=ana_H2_b2_phi, H1_b1_btag=ana_H1_b1_btag, H1_b2_btag=ana_H1_b2_btag, H2_b1_btag=ana_H2_b1_btag, H2_b2_btag=ana_H2_b2_btag, H1_b1_jetID=ana_H1_b1_jetID, H1_b2_jetID=ana_H1_b2_jetID, H2_b1_jetID=ana_H2_b1_jetID, H2_b2_jetID=ana_H2_b2_jetID, H1_b1_PUID=ana_H1_b1_PUID, H1_b2_PUID=ana_H1_b2_PUID, H2_b1_PUID=ana_H2_b1_PUID, H2_b2_PUID=ana_H2_b2_PUID, gen_H1_b1_matchedflag=ana_H1_b1_matchedflag, gen_H1_b2_matchedflag=ana_H1_b2_matchedflag, gen_H2_b1_matchedflag=ana_H2_b1_matchedflag, gen_H2_b2_matchedflag=ana_H2_b2_matchedflag, gen_H1_b1_matchedjet=ana_H1_b1_matchedjet, gen_H1_b2_matchedjet=ana_H1_b2_matchedjet, gen_H2_b1_matchedjet=ana_H2_b1_matchedjet, gen_H2_b2_matchedjet=ana_H2_b2_matchedjet) 








# bins = 100
# range = [0,1400]
# plt.title(r'Jet Kinematics ($p_T$)')
# plt.xlabel(r'$p_T$ [GeV]')
# plt.yscale('log')
# n, bins, patches = plt.hist(gen_data['gen_H1_b1_pt'], range=range, bins=bins, histtype='step', align='mid', color='magenta', label='gen H1 b1')
# plt.show()