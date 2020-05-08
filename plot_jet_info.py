# This code is used to study the shape of the signal events for the process X -> YH -> bbbb.

print "[INFO] Importing libraries..."
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

print "[INFO] Importing data..."
gen_data = np.load("gen_data.npz") # Generated events
reco_data = np.load("reco_data.npz") # Reconstructed events
analysis = np.load("analysis.npz") # Selected reconstructed events (analysis selections have been done)

print "[INFO] Initializing functions..."
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
        # range = [-2*np.pi, 2*np.pi]
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
        plt.title(r'Jet PU ID')
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
    elif dataset == 'sel': dat = analysis
    else:
        print("[ERROR] User has entered an unknown dataset.")

    if isMin: mask = [i > cut for i in dat[selection]]
    else: mask = [np.abs(i) < cut for i in dat[selection]]

    return np.asarray(mask)

def generateMasks(cut_info, isGen):
    """
    A work in progress... Does not do what I want it to do.
    """
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
            masks[icut] = [np.abs(i) < cut for i in dat[selection]]
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

def nbJet_mult_mask():
    """
    Checks whether or not the event has enough b jets and masks jets from events without enough b jets.
    """
    mask = []
    for nJ, nbJ in zip(analysis['nJet'], analysis['NbJets']):
        if int(nbJ) >= 4: mask.append([1]*int(nJ))
        else: mask.append([0]*int(nJ))
    mask = [item for sublist in mask for item in sublist]
    return np.asarray(mask)

def nbJet_mask():
    """
    Checks whether or not the event has enough b jets and masks jets from events without enough b jets.
    """
    mask = []
    for nbJ in analysis['NbJets']:
        if int(nbJ) >= 4: mask.append([True])
        else: mask.append([False])
    mask = [item for sublist in mask for item in sublist]
    return np.asarray(mask)

print "[INFO] Running nbJet_mask function..."
b_mult_mask = nbJet_mult_mask()
b_mask = nbJet_mask()




def PlotMe(data, kinematic, color, label, bins=None):
    """
    This function plots the kinematics in order to all have the same basic format (e.g. left).
    """
    try:
        if bins == None: range, bins = setupPlotting(kinematic)
        else: range, bins_temp = setupPlotting(kinematic)
    except: range, bins = setupPlotting(kinematic)
    n, bins, patches = plt.hist(data, range=range, bins=bins, histtype='step', align='mid', color=color, label=label)
    plt.legend(loc='best', prop={'size': 12})
    return n, bins, patches




######################################              GENERATED DATA            #####################################

# Generated data contains events propagated through the hadronizer and detector simulation and are reconstructed in order to test our analysis.

nGenJet       = gen_data['nGenJet']
gen_pt        = gen_data['gen_jet_pt']
gen_eta       = gen_data['gen_jet_eta']
gen_phi       = gen_data['gen_jet_phi']
gen_m         = gen_data['gen_jet_m']

print "[INFO] Loading ordered kinematics by pT..."
gen_ordered = np.load('gen_ordered.npz')


# gen_H_deltaPhi = np.subtract(gen_ordered['gen_H1_b1_phi'], gen_ordered['gen_H1_b2_phi'])
# gen_Y_deltaPhi = np.subtract(gen_ordered['gen_H2_b1_phi'], gen_ordered['gen_H2_b2_phi'])


######################################              RECONSTRUCTED DATA            #####################################

# Reco data is from a ROOT file made with no cuts. No min pT, no max eta, no min btagscore, no selections on PUID, no selections on Jet ID

nJet          = reco_data['nJet']
reco_pt       = reco_data['jet_pt']
reco_eta      = reco_data['jet_eta']
reco_phi      = reco_data['jet_phi']

btagscore     = reco_data['jet_bTagScore']
jetID         = reco_data['jet_jetID']
PUID          = reco_data['jet_PUID']


## Analysis data is extracted from a ROOT Afile with all the usual cuts. pT > 30 GeV, eta < 2.4, btag > 0.3093, tight Jet ID, medium PU ID.
# Analysis b jets are ordered by btagscore but it is interesting to see them ordered by pT instead.
# The ordering code is stored in ordered_kinematics.py
sel_ordered = np.load('analysis_ordered.npz')

# sel_H_deltaPhi = np.subtract(sel_ordered['sel_H1_b1_phi'], sel_ordered['sel_H1_b2_phi'])
# sel_Y_deltaPhi = np.subtract(sel_ordered['sel_H2_b1_phi'], sel_ordered['sel_H2_b2_phi'])

######################################             MATCHING GEN TO RECO           #####################################

# # Matching gen jet to reco jet by parent particle

H1b1mf_shift = sel_ordered['gen_H1_b1_matchedflag'] + 1
H1b1mf_bool = H1b1mf_shift.astype(bool)
H1b2mf_shift = sel_ordered['gen_H1_b2_matchedflag'] + 1
H1b2mf_bool = H1b2mf_shift.astype(bool)
H2b1mf_shift = sel_ordered['gen_H2_b1_matchedflag'] + 1
H2b1mf_bool = H2b1mf_shift.astype(bool)
H2b2mf_shift = sel_ordered['gen_H2_b2_matchedflag'] + 1
H2b2mf_bool = H2b2mf_shift.astype(bool)

H_b_jets_matched = np.logical_and(H1b1mf_bool, H1b2mf_bool)
Y_b_jets_matched = np.logical_and(H2b1mf_bool, H2b2mf_bool)
parent_gen_b_jets_matched = np.logical_and(H_b_jets_matched, Y_b_jets_matched)

all_matched_gen_b_pt = np.concatenate((sel_ordered['ana_gen_H1_b1_pt'][H1b1mf_bool], sel_ordered['ana_gen_H1_b2_pt'][H1b2mf_bool], sel_ordered['ana_gen_H2_b1_pt'][H2b1mf_bool], sel_ordered['ana_gen_H2_b2_pt'][H2b2mf_bool]), axis=None)
all_matched_gen_b_eta = np.concatenate((sel_ordered['ana_gen_H1_b1_eta'][H1b1mf_bool], sel_ordered['ana_gen_H1_b2_eta'][H1b2mf_bool], sel_ordered['ana_gen_H2_b1_eta'][H2b1mf_bool], sel_ordered['ana_gen_H2_b2_eta'][H2b2mf_bool]), axis=None)

count = 0
matched_btags = []
unmatched_btags = []
for H1b1_mf, H1b2_mf, H2b1_mf, H2b2_mf in zip(sel_ordered['gen_H1_b1_matchedflag'], sel_ordered['gen_H1_b2_matchedflag'], sel_ordered['gen_H2_b1_matchedflag'], sel_ordered['gen_H2_b2_matchedflag']):
    current = [H1b1_mf, H1b2_mf] 
    for i,jet in enumerate(current):
        if jet == 0: matched_btags.append(sel_ordered['ana_H1_b1_btag'][count])
        elif jet == 1: matched_btags.append(sel_ordered['ana_H1_b2_btag'][count])
        else: continue
    current = [H2b1_mf, H2b2_mf]
    for i,jet in enumerate(current):
        if jet == 0: matched_btags.append(sel_ordered['ana_H2_b1_btag'][count])
        elif jet == 1: matched_btags.append(sel_ordered['ana_H2_b2_btag'][count])
        else: continue
    count += 1

matched_btags = np.asarray(matched_btags)
print np.shape(matched_btags)

# Matching gen jet to reco jet with no constraints on parent particle
H1b1mj_shift = sel_ordered['gen_H1_b1_matchedjet'] + 1
H1b1mj_bool = H1b1mf_shift.astype(bool)
H1b2mj_shift = sel_ordered['gen_H1_b2_matchedjet'] + 1
H1b2mj_bool = H1b2mf_shift.astype(bool)
H2b1mj_shift = sel_ordered['gen_H2_b1_matchedjet'] + 1
H2b1mj_bool = H2b1mf_shift.astype(bool)
H2b2mj_shift = sel_ordered['gen_H2_b2_matchedjet'] + 1
H2b2mj_bool = H2b2mf_shift.astype(bool)

H_b_jets_matched_all = np.logical_and(H1b1mj_bool, H1b2mj_bool)
Y_b_jets_matched_all = np.logical_and(H2b1mj_bool, H2b2mj_bool)
all_gen_b_jets_matched = np.logical_and(H_b_jets_matched, Y_b_jets_matched)

all_matched_jet_pt = np.concatenate((sel_ordered['ana_gen_H1_b1_pt'][H1b1mj_bool], sel_ordered['ana_gen_H1_b2_pt'][H1b2mj_bool], sel_ordered['ana_gen_H2_b1_pt'][H2b1mj_bool], sel_ordered['ana_gen_H2_b2_pt'][H2b2mj_bool]), axis=None)


# count = 0
# matched_btags = []
# for H1b1_mf, H1b2_mf, H2b1_mf, H2b2_mf in zip(sel_ordered['gen_H1_b1_matchedflag'], sel_ordered['gen_H1_b2_matchedflag'], sel_ordered['gen_H2_b1_matchedflag'], sel_ordered['gen_H2_b2_matchedflag']):
#     current = [H1b1_mf, H1b2_mf, H2b1_mf, H2b2_mf]
#     for i,jet in enumerate(current):
#         if jet == 0: matched_btags.append(sel_ordered['ana_H1_b1_btag'][count])
#         elif jet == 1: matched_btags.append(sel_ordered['ana_H1_b2_btag'][count])
#         elif jet == 2: matched_btags.append(sel_ordered['ana_H2_b1_btag'][count])
#         elif jet == 3: matched_btags.append(sel_ordered['ana_H2_b2_btag'][count])
#         else: continue
#     count += 1

######################################              PLOTS            #####################################



print "[INFO] Creating plots and saving to pdf..."
showbs = False
show_Hbs = False
show_Ybs = False
show_b1s = False
show_b2s = False
color1, color2, color3, color4 = 'deepskyblue', 'magenta', 'mediumslateblue', 'mediumseagreen'
label1, label2, label3, label4 = r'$b_{1,H}$', r'$b_{2,H}$', r'$b_{1,Y}$', r'$b_{2,Y}$'

# cut = 'btag'
cut = ''

with PdfPages('plot_jet_id.pdf') as pdf:

    # color, label = 'blue', 'gen jets'

    # kin = 'pt'
    # n, bins, patches = PlotMe(gen_pt, kin, color, label)
    # if showbs or show_Hbs or show_b1s:
    #     PlotMe(gen_ordered['gen_H1_b1_pt'], kin, color1, 'gen ' + label1, bins=bins)
    # if showbs or show_Hbs or show_b2s:
    #     PlotMe(gen_ordered['gen_H1_b2_pt'], kin, color2, 'gen ' + label2, bins=bins)
    # if showbs or show_Ybs or show_b1s:
    #     PlotMe(gen_ordered['gen_H2_b1_pt'], kin, color3, 'gen ' + label3, bins=bins)
    # if showbs or show_Ybs or show_b2s:
    #     PlotMe(gen_ordered['gen_H2_b2_pt'], kin, color4, 'gen ' + label4, bins=bins)
    # pdf.savefig()
    # plt.clf()

    # kin = 'eta'
    # n, bins, patches = PlotMe(gen_eta, kin, color, label)
    # if showbs or show_Hbs or show_b1s:
    #     PlotMe(gen_ordered['gen_H1_b1_eta'], kin, color1, label1, bins=bins)
    # if showbs or show_Hbs or show_b2s:
    #     PlotMe(gen_ordered['gen_H1_b2_eta'], kin, color2, label2, bins=bins)
    # if showbs or show_Ybs or show_b1s:
    #     PlotMe(gen_ordered['gen_H2_b1_eta'], kin, color3, label3, bins=bins)
    # if showbs or show_Ybs or show_b2s:
    #     PlotMe(gen_ordered['gen_H2_b2_eta'], kin, color4, label4, bins=bins)
    # pdf.savefig()
    # plt.clf()

    # kin = 'phi'
    # n, bins, patches = PlotMe(gen_phi, kin, color, label)
    # if showbs or show_Hbs or show_b1s:
    #     PlotMe(gen_ordered['gen_H1_b1_phi'], kin, color1, label1, bins=bins)
    # if showbs or show_Hbs or show_b2s:
    #     PlotMe(gen_ordered['gen_H1_b2_phi'], kin, color2, label2, bins=bins)
    # if showbs or show_Ybs or show_b1s:
    #     PlotMe(gen_ordered['gen_H2_b1_phi'], kin, color3, label3, bins=bins)
    # if showbs or show_Ybs or show_b2s:
    #     PlotMe(gen_ordered['gen_H2_b2_phi'], kin, color4, label4, bins=bins)
    # pdf.savefig()
    # plt.clf()

    # kin = 'nJet'
    # PlotMe(nGenJet, kin, color, label)
    # pdf.savefig()
    # plt.clf()




    color, label = 'green', 'reco jets'
    # color1, color2, color3, coslor4 = 'darkblue', 'orange', 'limegreen', 'indigo'

    ####--------------------------------------    pT   ----------------------------------------------#####
    kin = 'pt'

    n, bins, patches = PlotMe(reco_pt, kin, color, label)
    bins = 100
    if cut == 'btag':
        PlotMe(reco_pt[generateMask(['jet_bTagScore', 0.3093, True], 'reco')], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if cut == 'jetID':
        PlotMe(reco_pt[generateMask(['jet_jetID', 2.9, True], 'reco')], kin, 'black', r'Tight Jet ID ($\geq 3$)', bins=bins)
    if cut == 'PUID':
        PlotMe(reco_pt[np.logical_or(generateMask(['jet_PUID', 5.9, True], 'reco'), generateMask(['jet_pt', 50, True], 'reco'))], kin, 'black', r'Medium PU ID ($\geq 6$)', bins=bins)
    if cut == 'pt':
        PlotMe(reco_pt[generateMask(['jet_pt', 30, True], 'reco')], kin, 'black', r'$p_T > 30$ GeV', bins=bins)
    if cut == 'eta':
        PlotMe(reco_pt[generateMask(['jet_eta', 2.4, False], 'reco')], kin, 'black', r'$|\eta| < 2.4$', bins=bins)
    
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_ordered['sel_H1_b1_pt'], kin, color1, 'reco ' + label1, bins=bins)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_ordered['sel_H1_b2_pt'], kin, color2, 'reco ' + label2, bins=bins)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_ordered['sel_H2_b1_pt'], kin, color3, 'reco ' + label3, bins=bins)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_ordered['sel_H2_b2_pt'], kin, color4, 'reco ' + label4, bins=bins)
    pdf.savefig()
    plt.clf()


    ####--------------------------------------    eta   ----------------------------------------------#####
    kin = 'eta'
    n, bins, patches = PlotMe(reco_eta, kin, color, label)

    if cut == 'btag':
        PlotMe(reco_eta[generateMask(['jet_bTagScore', 0.3093, True], 'reco')], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if cut == 'jetID':
        PlotMe(reco_eta[np.logical_or(generateMask(['jet_PUID', 5.9, True], 'reco'), generateMask(['jet_pt', 50, True], 'reco'))], kin, 'black', r'Tight Jet ID ($\geq 3$)', bins=bins)
    if cut == 'PUID':
        PlotMe(reco_eta[generateMask(['jet_PUID', 5.9, True], 'reco')], kin, 'black', r'Medium PU ID ($\geq 6$)', bins=bins)
    if cut == 'pt':
        PlotMe(reco_eta[generateMask(['jet_pt', 30, True], 'reco')], kin, 'black', r'$p_T > 30$ GeV', bins=bins)
    if cut == 'eta':
        PlotMe(reco_eta[generateMask(['jet_eta', 2.4, False], 'reco')], kin, 'black', r'$|\eta| < 2.4$', bins=bins)
    
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_ordered['sel_H1_b1_eta'], kin, color1, 'reco ' + label1, bins=bins)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_ordered['sel_H1_b2_eta'], kin, color2, 'reco ' + label2, bins=bins)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_ordered['sel_H2_b1_eta'], kin, color3, 'reco ' + label3, bins=bins)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_ordered['sel_H2_b2_eta'], kin, color4, 'reco ' + label4, bins=bins)
    pdf.savefig()
    plt.clf()


    ####--------------------------------------    phi   ----------------------------------------------#####
    kin = 'phi'
    n, bins, patches = PlotMe(reco_phi, kin, color, label)

    if cut == 'btag':
        PlotMe(reco_phi[generateMask(['jet_bTagScore', 0.3093, True], 'reco')], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if cut == 'jetID':
        PlotMe(reco_phi[generateMask(['jet_jetID', 2.9, True], 'reco')], kin, 'black', r'Tight Jet ID ($\geq 3$)', bins=bins)
    if cut == 'PUID':
        PlotMe(reco_phi[np.logical_or(generateMask(['jet_PUID', 5.9, True], 'reco'), generateMask(['jet_pt', 50, True], 'reco'))], kin, 'black', r'Medium PU ID ($\geq 6$)', bins=bins)
    if cut == 'pt':
        PlotMe(reco_phi[generateMask(['jet_pt', 30, True], 'reco')], kin, 'black', r'$p_T > 30$ GeV', bins=bins)
    if cut == 'eta':
        PlotMe(reco_phi[generateMask(['jet_eta', 2.4, False], 'reco')], kin, 'black', r'$|\eta| < 2.4$', bins=bins)

    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_ordered['sel_H1_b1_phi'], kin, color1, 'reco ' + label1, bins=bins)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_ordered['sel_H1_b2_phi'], kin, color2, 'reco ' + label2, bins=bins)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_ordered['sel_H2_b1_phi'], kin, color3, 'reco ' + label3, bins=bins)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_ordered['sel_H2_b2_phi'], kin, color4, 'reco ' + label4, bins=bins)
    pdf.savefig()
    plt.clf()


    ####--------------------------------------    btag  ----------------------------------------------#####
    kin = 'btag'
    n, bins, patches = PlotMe(btagscore, kin, color, label)
    PlotMe(matched_btags, kin, 'black', 'matched jets')
    

    if cut == 'btag':
        PlotMe(btagscore[generateMask(['jet_bTagScore', 0.3093, True], 'reco')], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if cut == 'jetID':
        PlotMe(btagscore[generateMask(['jet_jetID', 2.9, True], 'reco')], kin, 'black', r'Tight Jet ID ($\geq 3$)', bins=bins)
    if cut == 'PUID':
        PlotMe(btagscore[np.logical_or(generateMask(['jet_PUID', 5.9, True], 'reco'), generateMask(['jet_pt', 50, True], 'reco'))], kin, 'black', r'Medium PU ID ($\geq 6$)', bins=bins)
    if cut == 'pt':
        PlotMe(btagscore[generateMask(['jet_pt', 30, True], 'reco')], kin, 'black', r'$p_T > 30$ GeV', bins=bins)
    if cut == 'eta':
        PlotMe(btagscore[generateMask(['jet_eta', 2.4, False], 'reco')], kin, 'black', r'$|\eta| < 2.4$', bins=bins)
    
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_ordered['sel_H1_b1_btag'], kin, color1, 'reco ' + label1, bins=bins)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_ordered['sel_H1_b2_btag'], kin, color2, 'reco ' + label2, bins=bins)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_ordered['sel_H2_b1_btag'], kin, color3, 'reco ' + label3, bins=bins)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_ordered['sel_H2_b2_btag'], kin, color4, 'reco ' + label4, bins=bins)
    pdf.savefig()
    plt.clf()



    ####---------------------------------------  jetID  ----------------------------------------------#####
    kin = 'jetID'
    n, bins, patches = PlotMe(jetID, kin, color, label)

    if cut == 'btag':
        PlotMe(jetID[generateMask(['jet_bTagScore', 0.3093, True], 'reco')], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if cut == 'jetID':
        PlotMe(jetID[generateMask(['jet_jetID', 2.9, True], 'reco')], kin, 'black', r'Tight Jet ID ($\geq 3$)', bins=bins)
    if cut == 'PUID':
        PlotMe(jetID[np.logical_or(generateMask(['jet_PUID', 5.9, True], 'reco'), generateMask(['jet_pt', 50, True], 'reco'))], kin, 'black', r'Medium PU ID ($\geq 6$)', bins=bins)
    if cut == 'pt':
        PlotMe(jetID[generateMask(['jet_pt', 30, True], 'reco')], kin, 'black', r'$p_T > 30$ GeV', bins=bins)
    if cut == 'eta':
        PlotMe(jetID[generateMask(['jet_eta', 2.4, False], 'reco')], kin, 'black', r'$|\eta| < 2.4$', bins=bins)
    
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_ordered['sel_H1_b1_jetid'], kin, color1, 'reco ' + label1, bins=bins)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_ordered['sel_H1_b2_jetid'], kin, color2, 'reco ' + label2, bins=bins)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_ordered['sel_H2_b1_jetid'], kin, color3, 'reco ' + label3, bins=bins)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_ordered['sel_H2_b2_jetid'], kin, color4, 'reco ' + label4, bins=bins)
    pdf.savefig()
    plt.clf()



    ####---------------------------------------  PUID  ----------------------------------------------#####
    kin = 'PUID'
    n, bins, patches = PlotMe(PUID, kin, color, label)

    if cut == 'btag':
        PlotMe(PUID[generateMask(['jet_bTagScore', 0.3093, True], 'reco')], kin, 'black', 'DeepFlavB > 0.3093', bins=bins)
    if cut == 'jetID':
        PlotMe(PUID[generateMask(['jet_jetID', 2.9, True], 'reco')], kin, 'black', r'Tight Jet ID ($\geq 3$)', bins=bins)
    if cut == 'PUID':
        PlotMe(PUID[np.logical_or(generateMask(['jet_PUID', 5.9, True], 'reco'), generateMask(['jet_pt', 50, True], 'reco'))], kin, 'black', r'Medium PU ID ($\geq 6$)', bins=bins)
    if cut == 'pt':
        PlotMe(PUID[generateMask(['jet_pt', 30, True], 'reco')], kin, 'black', r'$p_T > 30$ GeV', bins=bins)
    if cut == 'eta':
        PlotMe(PUID[generateMask(['jet_eta', 2.4, False], 'reco')], kin, 'black', r'$|\eta| < 2.4$', bins=bins)
    
    if showbs or show_Hbs or show_b1s:
        PlotMe(sel_ordered['sel_H1_b1_PUID'], kin, color1, 'reco ' + label1)
    if showbs or show_Hbs or show_b2s:
        PlotMe(sel_ordered['sel_H1_b2_PUID'], kin, color2, 'reco ' + label2)
    if showbs or show_Ybs or show_b1s:
        PlotMe(sel_ordered['sel_H2_b1_PUID'], kin, color3, 'reco ' + label3)
    if showbs or show_Ybs or show_b2s:
        PlotMe(sel_ordered['sel_H2_b2_PUID'], kin, color4, 'reco ' + label4)
    pdf.savefig()
    plt.clf()
    

    ####--------------------------------------  jet mult  --------------------------------------------#####
    kin = 'nJet'
    PlotMe(nJet, kin, color, label)
    plt.yscale('log')
    if cut == 'btag':
        PlotMe(applyCutnOnJetMult(generateMask(['jet_bTagScore', 0.3093, True], 'reco')), 'nJet', 'black', 'DeepFlavB > 0.3093')
    if cut == 'jetID':
        PlotMe(applyCutnOnJetMult(generateMask(['jet_jetID', 2.9, True], 'reco')), 'nJet', 'black', r'Tight Jet ID ($\geq 3$)')
    if cut == 'PUID':
        PlotMe(applyCutnOnJetMult(np.logical_or(generateMask(['jet_PUID', 5.9, True], 'reco'), generateMask(['jet_pt', 50, True], 'reco'))), 'nJet', 'black', r'Medium PU ID ($\geq 6$)')
    if cut == 'pt':
        PlotMe(applyCutnOnJetMult(generateMask(['jet_pt', 30, True], 'reco')), 'nJet', 'black', r'$p_T > 30$ GeV')
    if cut == 'eta':
        PlotMe(applyCutnOnJetMult(generateMask(['jet_eta', 2.4, False], 'reco')), 'nJet', 'black', r'$|\eta| < 2.4$')
    # PlotMe(applyCutnOnJetMult(mask), 'nJet', 'blueviolet', 'DeepFlavB > 0.3093')
    pdf.savefig()

    plt.clf()

    # n, bins, patches = PlotMe(reco_data['NbJets'], kin, 'green', 'reco jets')
    n, bins, patches = PlotMe(analysis['NbJets'], kin, 'green', 'NbJets', bins=bins)
    PlotMe(analysis['NbJets'][b_mask], kin, 'black', 'NbJets >= 4', bins=bins)
    plt.yscale('log')
    pdf.savefig()
    plt.clf()



    # kin = 'phi'
    # PlotMe(gen_H_deltaPhi, kin, 'magenta', r'gen $\Delta\phi_H$', bins=100)
    # PlotMe(gen_Y_deltaPhi, kin, 'mediumslateblue', r'gen $\Delta\phi_Y$', bins=100)
    # # PlotMe(sel_H_deltaPhi, kin, 'deepskyblue', r'reco $\Delta\phi_H$', bins=100)
    # # PlotMe(sel_Y_deltaPhi, kin, 'mediumseagreen', r'reco $\Delta\phi_Y$', bins=100)
    # plt.xlabel(r'$\Delta\phi$ [rad]')
    # plt.ylim(10**1, None)
    # pdf.savefig()
    # plt.clf()
