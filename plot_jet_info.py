# This code is used to study the shape of the signal events for the process X -> YH -> bbbb.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

gen_data = np.load("gen_data.npz") # Generated events
reco_data = np.load("reco_data.npz") # Reconstructed events
analysis = np.load("analysis.npz") # Selected reconstructed events (analysis selections have been done)

def setupPlotting(kinematic):
    """
    This function is used to set the parameters for the histograms so they will all have a similar layout.
    """
    plt.yscale('log')
    bins = 100
    if 'pt' in kinematic:
        range = [0,1400]
        plt.title(r'Jet Kinematics ($p_T$)')
        plt.xlabel(r'$p_T$ [GeV]')
    elif 'eta' in kinematic:
        range = [-2*np.pi, 2*np.pi]
        plt.title(r'Jet Kinematics ($\eta$)')
        plt.xlabel(r'$\eta$')
    elif 'phi' in kinematic:
        range = None
        plt.title(r'Jet Kinematics ($\phi$)')
        plt.xlabel(r'$\phi$ [rad]')
    elif 'btag' in kinematic:
        range = None
        plt.title(r'Jet DeepFlavour Tag')
        plt.xlabel(r'DeepFlavour Tag')
    elif 'jetID' in kinematic:
        range = None
        plt.title(r'Jet ID')
        plt.xlabel(r'Jet ID Tag')
    elif 'PUID' in kinematic:
        range = None
        plt.title(r'Jet Jet PU ID')
        plt.xlabel(r'Jet PU ID Tag')
    elif 'nJet' in kinematic:
        range = None
        plt.title(r'Jet Multiplicity')
        plt.xlabel('Number of Jets in Event')
        plt.yscale('linear')
        bins = np.arange(0,22,1)
    return range, bins

def generateMask(cut_info, dataset):
    """
    Generate a boolean mask to apply cuts on kinematics.
    selection = a branch of the ROOT file
    cut = value of the cut
    isMin = True for a minimum (e.g. pT, btagscore) and False for a maximum (e.g. eta)
    """
    selection = cut_info[0]
    cut = cut_info[1]
    isMin = cut_info[2]

    if dataset == 'gen': dat = gen_data
    elif dataset == 'reco': dat = reco_data
    elif dataset == 'analysis': dat = analysis

    if isMin: mask = [i > cut for i in dat[selection]]
    else: mask = [i < cut for i in dat[selection]]

    return np.asarray(mask)

def generateMasks(cut_info, isGen):
    masks = []
    for i in range(len(cut_info)): masks.append([])
    for icut, cuts in enumerate(cut_info):
        selection = cuts[0]
        cut = cuts[1]
        isMin = cuts[2]
        if isGen: dat = gen_data
        else: dat = reco_data
        if isMin: 
            masks[icut] = [i > cut for i in dat[selection]]
        else: 
            masks[icut] = [i < cut for i in dat[selection]]
    # mask = np.ones(len(masks[0]))
    # for i in range(len(masks)):
    #     mask = np.logical_and(mask, masks[i])
    print "shape of masks is", np.shape(masks)
    return masks


def applyCutnOnJetMult(mask):
    """
    Applying cuts on jet multiplicity is a little more complicated than applying cuts on jets. This function counts the number of jets in each event that satisfy the cut.
    """

    count = 0
    nJet_cut = []
    
    for i in reco_data['nJet']:
        sum = 0
        i = int(i)
        for j in range(i):
            if mask[count] == True: sum += 1
            count+=1
        nJet_cut.append(sum)
    return nJet_cut

def orderbs(kinematic, dataset):
    """
    Order b jets by pT such that H1_b1_pt > H1_b2_pt and H2_b1_pt > H2_b2_pt.
    """

    H1b1, H1b2, H2b1, H2b2 = 'H1_b1_', 'H1_b2_', 'H2_b1_', 'H2_b2_'

    if dataset == 'gen':
        data = gen_data
        H1b1, H1b2, H2b1, H2b2 = 'gen' + H1_b1, 'gen' + H1_b2, 'gen' + H2_b1, 'gen' + H2_b2
    elif dataset == 'reco':
        data = reco_data
    elif dataset == 'analysis':
        data = analysis
    else: print("User has entered unknown dataset.")

    H_b1_ord, H_b2_ord = [], []
    count = 0
    for i,j in zip(data[H1b1 + 'pt'], data[H1b2 + 'pt']):
        if i > j:
            H_b1_ord.append(data[H1b1 + kinematic][count])
            H_b2_ord.append(data[H1b2 + kinematic][count])
        else:
            H_b2_ord.append(data[H1b1 + kinematic][count])
            H_b1_ord.append(data[H1b2 + kinematic][count])
        count += 1
    # Order Y b jets.
    count = 0
    Y_b1_ord, Y_b2_ord = [], []
    for i,j in zip(data[H2b1 + 'pt'], data[H2b2 + 'pt']):
        if i > j:
            Y_b1_ord.append(data[H2b1 + kinematic][count])
            Y_b2_ord.append(data[H2b2 + kinematic][count])
        else:
            Y_b2_ord.append(data[H2b1 + kinematic][count])
            Y_b1_ord.append(data[H2b2 + kinematic][count])
        count += 1
    return np.asarray(H_b1_ord), np.asarray(H_b2_ord), np.asarray(Y_b1_ord), np.asarray(Y_b2_ord)
    

def PlotMe(data, kinematic, color, label, bins=None):
    """
    This function plots the kinematics to all have the same basic format (e.g. left).
    """
    try: 
        if bins == None: 
            range, bins = setupPlotting(kinematic)
    except: range, bins_temp = setupPlotting(kinematic)
    n, bins, patches = plt.hist(data, range=range, bins=bins, histtype='step', align='mid', color=color, label=label)
    plt.legend(loc='best', prop={'size': 12})
    return n, bins, patches





info = [['jet_PUID', 5, True], ['jet_jetID', 2, True]]

mask1 = generateMask(info[0], False)
mask2 = generateMask(info[1], False)
mask3 = generateMask(['jet_bTagScore', 0.3093, True], False)

mask = np.logical_and(mask1, mask2)



# n, bins, patches = PlotMe(reco_data['jet_pt'], kinematic='pt', color='blueviolet', label='no mask1')
# PlotMe(reco_data['jet_pt'][mask1], kinematic='pt', color='forestgreen', bins=bins, label='mask1')
# PlotMe(reco_data['jet_pt'][masks], kinematic='pt', color='deepskyblue', bins=bins, label='masks[0][0]')
# plt.show()







######################################              GENERATED DATA            #####################################


nGenJet       = gen_data['nGenJet']
gen_pt        = gen_data['gen_jet_pt']
gen_eta       = gen_data['gen_jet_eta']
gen_phi       = gen_data['gen_jet_phi']
gen_m         = gen_data['gen_jet_m']
gen_H1_b1_pt,  gen_H1_b2_pt,  gen_H2_b1_pt,  gen_H2_b2_pt  = orderbs('pt')
gen_H1_b1_eta, gen_H1_b2_eta, gen_H2_b1_eta, gen_H2_b2_eta = orderbs('eta')
gen_H1_b1_phi, gen_H1_b2_phi, gen_H2_b1_phi, gen_H2_b2_phi = orderbs('phi')

gen_H_deltaPhi = np.diff(gen_H1_b1_phi, gen_H1_b2_phi)
gen_Y_deltaPhi = np.diff(gen_H2_b1_phi, gen_H2_b2_phi)


# range, bins = setupPlotting('pt')
# plt.hist(gen_pt, range=range, bins=bins, histtype='step', align='mid', color='blue', label='all jets')
# plt.hist(gen_H1_b1_pt, range=range, bins=bins, histtype='step', align='mid', color='tab:cyan', label='b1 Higgs')
# plt.hist(gen_H1_b2_pt, range=range, bins=bins, histtype='step', align='mid', color='magenta', label='b2 Higgs')
# # plt.hist(gen_H2_b1_pt, range=range, bins=bins, histtype='step', align='mid', color='mediumseagreen', label='b1 Y')
# # plt.hist(gen_H2_b2_pt, range=range, bins=bins, histtype='step', align='mid', color='blueviolet', label='b2 Y')
# plt.legend(loc='best', prop={'size': 12})
# plt.savefig('jet_plot_id.png')


######################################              RECONSTRUCTED DATA            #####################################

# Reco data is from a ROOT file made with no cuts. No min pT, no max eta, no min btagscore, no selections on PUID, no selections on Jet ID

nJet          = reco_data['nJet']
reco_pt       = reco_data['jet_pt']
reco_eta      = reco_data['jet_eta']
reco_phi      = reco_data['jet_phi']

btagscore     = reco_data['jet_bTagScore']
jetID         = reco_data['jet_jetID']
PUID          = reco_data['jet_PUID']



reco_H1_b1_pt  = reco_data['H1_b1_pt']
reco_H1_b2_pt  = reco_data['H1_b2_pt']
reco_H2_b1_pt  = reco_data['H2_b1_pt']
reco_H2_b2_pt  = reco_data['H2_b2_pt']
reco_H1_b1_eta = reco_data['H1_b1_eta']
reco_H1_b2_eta = reco_data['H1_b2_eta']
reco_H2_b1_eta = reco_data['H2_b1_eta']
reco_H2_b2_eta = reco_data['H2_b2_eta']
reco_H1_b1_phi = reco_data['H1_b1_phi']
reco_H1_b2_phi = reco_data['H1_b2_phi']
reco_H2_b1_phi = reco_data['H2_b1_phi']
reco_H2_b2_phi = reco_data['H2_b2_phi']


## Analysis data is extracted from a ROOT file with all the usual cuts. pT > 30 GeV, eta < 2.4, btag > 0.3093, tight Jet ID, medium PU ID.

sel_H1_b1_pt  = analysis['H1_b1_pt']
sel_H1_b2_pt  = analysis['H1_b2_pt']
sel_H2_b1_pt  = analysis['H2_b1_pt']
sel_H2_b2_pt  = analysis['H2_b2_pt']
sel_H1_b1_eta = analysis['H1_b1_eta']
sel_H1_b2_eta = analysis['H1_b2_eta']
sel_H2_b1_eta = analysis['H2_b1_eta']
sel_H2_b2_eta = analysis['H2_b2_eta']
sel_H1_b1_phi = analysis['H1_b1_phi']
sel_H1_b2_phi = analysis['H1_b2_phi']
sel_H2_b1_phi = analysis['H2_b1_phi']
sel_H2_b2_phi = analysis['H2_b2_phi']
sel_H1_b1_mb = analysis['gen_H1_b1_matchedflag']
sel_H1_b2_mb = analysis['gen_H1_b2_matchedflag']
sel_H2_b1_mb = analysis['gen_H2_b1_matchedflag']
sel_H2_b2_mb = analysis['gen_H2_b2_matchedflag']
sel_H1_b1_mj = analysis['recoJetMatchedToGenJet1']
sel_H1_b2_mj = analysis['recoJetMatchedToGenJet2']
sel_H2_b1_mj = analysis['recoJetMatchedToGenJet3']
sel_H2_b2_mj = analysis['recoJetMatchedToGenJet4']
analysis_btag = analysis['jet_bTagScore']



######################################             MATCHING GEN TO RECO           #####################################

# Matching gen jet to reco jet by parent particle
all_b_matched_mask = np.asarray([i >= 0 and j >= 0 and k >= 0 and l >= 0 for i,j,k,l in zip(sel_H1_b1_mb,sel_H1_b2_mb,sel_H2_b1_mb,sel_H2_b2_mb)])
H_b1_matched = [i >= 0 for i in sel_H1_b1_mb]
H_b2_matched = [i >= 0 for i in sel_H1_b2_mb]
Y_b1_matched = [i >= 0 for i in sel_H2_b1_mb]
Y_b2_matched = [i >= 0 for i in sel_H2_b2_mb]


# Matching gen jet to reco jet with no constraints on parent particle
all_jet_matched_mask = np.asarray([i >= 0 and j >= 0 and k >= 0 and l >= 0 for i,j,k,l in zip(sel_H1_b1_mj,sel_H1_b2_mj,sel_H2_b1_mj,sel_H2_b2_mj)])
b1_matched = [i >= 0 for i in sel_H1_b1_mj]
b2_matched = [i >= 0 for i in sel_H1_b2_mj]
b3_matched = [i >= 0 for i in sel_H2_b1_mj]
b4_matched = [i >= 0 for i in sel_H2_b2_mj]

######################################              ORDERING BY pT           #####################################

count = 0
H_b1_matched_pto, H_b2_matched_pto, Y_b1_matched_pto, Y_b2_matched_pto = [], [], [], []
for i,j,k,l in zip(gen_H1_b1_pt, gen_H1_b2_pt, gen_H2_b1_pt, gen_H2_b2_pt):
    if i > j: 
        H_b1_matched_pto.append(H_b1_matched[count])
        H_b2_matched_pto.append(H_b2_matched[count])
    else:
        H_b2_matched_pto.append(H_b1_matched[count])
        H_b1_matched_pto.append(H_b2_matched[count])
    if k > l: 
        Y_b1_matched_pto.append(Y_b1_matched[count])
        Y_b2_matched_pto.append(Y_b2_matched[count])
    else:
        Y_b2_matched_pto.append(Y_b1_matched[count])
        Y_b1_matched_pto.append(H_b2_matched[count])

# H_b1_matched_pto, H_b2_matched_pto, Y_b1_matched_pto, Y_b2_matched_pto = np.asarray(H_b1_matched_pto), np.asarray(H_b2_matched_pto), np.asarray(Y_b1_matched_pto), np.asarray(Y_b2_matched_pto)
# H_b1_matched_pto, H_b2_matched_pto, Y_b1_matched_pto, Y_b2_matched_pto = H_b1_matched_pto, H_b2_matched_pto, Y_b1_matched_pto, Y_b2_matched_pto


# matched_bs = np.concatenate((gen_H1_b1_pt_o, gen_H1_b2_pt_o, gen_H2_b1_pt_o, gen_H2_b2_pt_o), axis=None)
# gen_H1_b1_pt_o, gen_H1_b2_pt_o, gen_H2_b1_pt_o, gen_H2_b2_pt_o = orderbs('pt')
gen_H1_b1_eta_o, gen_H1_b2_eta_o, gen_H2_b1_eta_o, gen_H2_b2_eta_o = orderbs('eta')
# all_b_pt = np.concatenate((gen_H1_b1_pt_o, gen_H1_b2_pt_o, gen_H2_b1_pt_o, gen_H2_b2_pt_o), axis=None)



# # sel_H1_b1_pt, sel_H1_b2_pt, sel_H2_b1_pt, sel_H2_b2_pt = orderrecobs('pt')
# range, bins = setupPlotting('eta')
# n, bins, patches = plt.hist(gen_eta, range=range, bins=bins, histtype='step', align='mid', color=['blue'], label="gen jets")
# plt.hist(gen_H1_b1_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['tab:cyan'], label=r"$b_{1,H}$")
# plt.hist(gen_H1_b2_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['magenta'], label=r"$b_{2,H}$")
# # plt.hist(gen_H2_b1_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['mediumseagreen'], label=r"$b_{1,Y}$")
# # plt.hist(gen_H2_b2_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['blueviolet'], label=r"$b_{2,Y}$")

# plt.legend(loc='best', prop={'size': 12})
# plt.savefig('plot_jet_id.pdf')

# sel_H1_b1_pt, sel_H1_b2_pt, sel_H2_b1_pt, sel_H2_b2_pt = orderrecobs('pt')
# range, bins = setupPlotting('jetmult')
# n, bins, patches = plt.hist(nJet, range=range, bins=bins, histtype='step', align='mid', color=['blue'], label="No selections")
# plt.hist(nJet[all_b_matched_mask], range=range, bins=bins, histtype='step', align='mid', color=['green'], label=r"all reco b jets matched to gen jet, same parent")
# plt.hist(nJet[all_jet_matched_mask], range=range, bins=bins, histtype='step', align='mid', color=['blueviolet'], label=r"all reco b jets matched to any one gen b jet")
# plt.title(r"Jet Multiplicity")
# plt.legend(loc='best', prop={'size': 10})
# plt.savefig('jet_plot_id.png')


######################################              MASKS            #####################################



# jet_id_mask = np.asarray([i >= 3 for i in jetID])

# puid_mask=[]
# for i,j in zip(PUID, reco_pt):
#     if j< 50:
#         if i >= 6: puid_mask.append(True)
#         else: puid_mask.append(False)
#     else: puid_mask.append(True)
# jet_puid_mask = np.asarray(puid_mask)

# jet_id_puid_mask = np.asarray( [ i and j for i,j in zip(jet_id_mask, jet_puid_mask) ] )
jet_btagscore_mask = np.asarray( [i > 0.3093 for i in btagscore])



######################################              PLOTS            #####################################




# range, bins = setupPlotting('pt')
# n, bins, patches = plt.hist(reco_pt, range=range, bins=bins, histtype='step', align='mid', color=['green'], label="No selections")
# plt.hist(reco_pt[jet_btagscore_mask], range=range, bins=bins, histtype='step', align='mid', color=['black'], label="DeepFlavour > 0.3093")
# plt.hist(reco_pt[jet_btagscore_mask], range=range, bins=bins, histtype='step', align='mid', color=['black'], label="No selections")





# bins_njet = np.arange(0,22,1)
# range, bins = setupPlotting('eta')
# n, bins, patches = plt.hist(reco_eta, range=range, bins=bins, histtype='step', align='mid', color=['black'], label='no cuts')
# eta_min, eta_max = bins[49], bins[50]

# hat_phi, hat_pt, hat_jetid, hat_puid, hat_btag = [], [], [], [], []
# for eta, phi, pt, jid, pid, btag in zip(reco_eta, reco_phi, reco_pt, jetID, PUID, analysis_btag):
#     if (eta > eta_min and eta < eta_max):
#         hat_phi.append(phi)
#         hat_pt.append(pt)
#         hat_jetid.append(jid)
#         hat_puid.append(pid)
#         hat_btag.append(btag)


# plt.clf()

# range, bins = setupPlotting('pt')
# n, bins, patches = plt.hist(reco_pt, range=range, bins=bins, histtype='step', align='mid', color=['green'], label="all jets")
# plt.hist(hat_pt, range=range, bins=bins, histtype='step', align='mid', color=['black'], label=r"$\eta \approx 0$")
# plt.legend(loc='best', prop={'size': 12})
# plt.savefig('jet_plot_id.png')


# pt_mask = generateMask(['jet_pt', 30, True], False)
# range, bins = setupPlotting('eta')
# n, bins, patches = plt.hist(reco_eta, range=range, bins=bins, histtype='step', align='mid', color=['green'], label="all jets")
# plt.hist(reco_eta[pt_mask], range=range, bins=bins, histtype='step', align='mid', color=['black'], label=r"$p_T > 30$ GeV")
# plt.legend(loc='best', prop={'size': 12})
# plt.savefig('jet_plot_id.png')


showbs = False
show_Hbs = False
show_Ybs = False
show_b1s = False
show_b2s = False
color1, color2, color3, color4 = 'tab:cyan', 'magenta', 'mediumseagreen', 'blueviolet'
label1, label2, label3, label4 = r'$b_{1,H}$', r'$b_{2,H}$', r'$b_{1,Y}$', r'$b_{2,Y}$'

with PdfPages('multipage_pdf.pdf') as pdf:

    color, label = 'blue', 'gen jets'

    kin = 'pt'
    PlotMe(gen_pt, kin, color, label)
    if showbs or show_Hbs or show_b1s:
        PlotMe(gen_H1_b1_pt, kin, color1, 'gen ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(gen_H1_b2_pt, kin, color2, 'gen ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(gen_H2_b1_pt, kin, color3, 'gen ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(gen_H2_b2_pt, kin, color4, 'gen ' + label4)
    pdf.savefig()
    plt.clf()

    kin = 'eta'
    PlotMe(gen_eta, kin, color, label)
    if showbs or show_Hbs or show_b1s:
        PlotMe(gen_H1_b1_eta, kin, color1, label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(gen_H1_b2_eta, kin, color2, label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(gen_H2_b1_eta, kin, color3, label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(gen_H2_b2_eta, kin, color4, label4)
    pdf.savefig()
    plt.clf()

    kin = 'phi'
    PlotMe(gen_phi, kin, color, label)
    if showbs or show_Hbs or show_b1s:
        PlotMe(gen_H1_b1_phi, kin, color1, label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(gen_H1_b2_phi, kin, color2, label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(gen_H2_b1_phi, kin, color3, label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(gen_H2_b2_phi, kin, color4, label4)
    pdf.savefig()
    plt.clf()

    kin = 'nJet'
    PlotMe(nGenJet, kin, color, label)
    pdf.savefig()
    plt.clf()




    color, label = 'green', 'reco jets'
    color1, color2, color3, color4 = 'darkturquoise', 'orchid', 'teal', 'indigo'

    kin = 'pt'
    n, bins, patches = PlotMe(reco_pt, kin, color, label)
    # PlotMe(reco_pt[generateMask(['jet_bTagScore', 0.3093, True], False)], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_H1_b1_pt, kin, color1, 'reco ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_H1_b2_pt, kin, color2, 'reco ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_H2_b1_pt, kin, color3, 'reco ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_H2_b2_pt, kin, color4, 'reco ' + label4)
    pdf.savefig()
    plt.clf()

    kin = 'eta'
    n, bins, patches = PlotMe(reco_eta, kin, color, label)
    # PlotMe(reco_eta[generateMask(['jet_bTagScore', 0.3093, True], False)], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_H1_b1_eta, kin, color1, 'reco ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_H1_b2_eta, kin, color2, 'reco ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_H2_b1_eta, kin, color3, 'reco ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_H2_b2_eta, kin, color4, 'reco ' + label4)
    pdf.savefig()
    plt.clf()

    kin = 'phi'
    n, bins, patches = PlotMe(reco_phi, kin, color, label)
    # PlotMe(reco_phi[generateMask(['jet_bTagScore', 0.3093, True], False)], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_H1_b1_phi, kin, color1, 'reco ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_H1_b2_phi, kin, color2, 'reco ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_H2_b1_phi, kin, color3, 'reco ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_H2_b2_phi, kin, color4, 'reco ' + label4)
    pdf.savefig()
    plt.clf()

    kin = 'btag'
    n, bins, pathces = PlotMe(btagscore, kin, color, label)
    # PlotMe(btagscore[generateMask(['jet_bTagScore', 0.3093, True], False)], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_H1_b1_phi, kin, color1, 'reco ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_H1_b2_phi, kin, color2, 'reco ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_H2_b1_phi, kin, color3, 'reco ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_H2_b2_phi, kin, color4, 'reco ' + label4)
    pdf.savefig()
    plt.clf()

    kin = 'jetID'
    n, bins, pathces = PlotMe(jetID, kin, color, label)
    # PlotMe(btagscore[generateMask(['jet_bTagScore', 0.3093, True], False)], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_H1_b1_phi, kin, color1, 'reco ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_H1_b2_phi, kin, color2, 'reco ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_H2_b1_phi, kin, color3, 'reco ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_H2_b2_phi, kin, color4, 'reco ' + label4)
    pdf.savefig()
    plt.clf()

    kin = 'PUID'
    n, bins, pathces = PlotMe(PUID, kin, color, label)
    # PlotMe(btagscore[generateMask(['jet_bTagScore', 0.3093, True], False)], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_H1_b1_phi, kin, color1, 'reco ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_H1_b2_phi, kin, color2, 'reco ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_H2_b1_phi, kin, color3, 'reco ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_H2_b2_phi, kin, color4, 'reco ' + label4)
    pdf.savefig()
    plt.clf()

    kin = 'nJet'
    PlotMe(nJet, kin, color, label)
    # PlotMe(applyCutnOnJetMult(generateMask(['jet_bTagScore', 0.3093, True], False)), 'nJet', 'black', 'DeepFlavB > 0.3093')
    # PlotMe(applyCutnOnJetMult(mask), 'nJet', 'blueviolet', 'DeepFlavB > 0.3093')
    pdf.savefig()
    plt.clf()





######################################              PLOT b JETS            #####################################

# with PdfPages('multipage_pdf.pdf') as pdf:
#     range, bins = setupPlotting('eta')
#     n, bins, patches = plt.hist(gen_eta, range=range, bins=bins, histtype='step', align='mid', color=['blue'], label="gen jets")
#     plt.hist(gen_H1_b1_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['tab:cyan'], label=r"$b_{1,H}$")
#     plt.hist(gen_H1_b2_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['magenta'], label=r"$b_{2,H}$")
#     pdf.attach_note("b jets from Higgs")
#     pdf.savefig()
#     plt.clf()
#     range, bins = setupPlotting('eta')
#     n, bins, patches = plt.hist(gen_eta, range=range, bins=bins, histtype='step', align='mid', color=['blue'], label="gen jets")
#     plt.hist(gen_H2_b1_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['mediumseagreen'], label=r"$b_{1,Y}$")
#     plt.hist(gen_H2_b2_eta_o, range=range, bins=bins, histtype='step', align='mid', color=['blueviolet'], label=r"$b_{2,Y}$")
#     pdf.attach_note("b jets from Y")
#     pdf.savefig()
#     plt.close()