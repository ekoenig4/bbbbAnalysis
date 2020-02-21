hadd -f SingleMuon_Data_forTrigger_MuonPt30_matched.root                   `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_matched/SKIM_SingleMuon_Data_forTrigger/output`                    &
hadd -f TTbar_MC_forTrigger_MuonPt30_matched.root                          `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_matched/SKIM_MC_TT_TuneCUETP8M2T4_13TeV_forTrigger/output`         &
hadd -f WJetsToLNu_Data_forTrigger_MuonPt30_matched.root                   `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_matched/SKIM_MC_WJetsToLNu_TuneCUETP8M1_13TeV_forTrigger/output`   &
hadd -f NMSSM_XYHbbbb_privateProduction_forTrigger_MuonPt30_matched.root   `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_matched/SKIM_NMSSM_XYHbbbb_privateProduction_forTrigger/output`    &

hadd -f SingleMuon_Data_forTrigger_MuonPt30_unMatched.root                 `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_unMatched/SKIM_SingleMuon_Data_forTrigger/output`                  &
hadd -f TTbar_MC_forTrigger_MuonPt30_unMatched.root                        `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_unMatched/SKIM_MC_TT_TuneCUETP8M2T4_13TeV_forTrigger/output`       &
hadd -f WJetsToLNu_Data_forTrigger_MuonPt30_unMatched.root                 `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_unMatched/SKIM_MC_WJetsToLNu_TuneCUETP8M1_13TeV_forTrigger/output` &
hadd -f NMSSM_XYHbbbb_privateProduction_forTrigger_MuonPt30_unMatched.root `xrdfsls -u /store/user/fravera/bbbb_ntuples_CMSDAS_trigger/ntuples_20Jan2020_MuonCut30GeV_v23_unMatched/SKIM_NMSSM_XYHbbbb_privateProduction_forTrigger/output`  &





# hadd -f TriggerClosure_notTriggered.root `xrdfsls -u /store/user/fravera/bbbb_ntuples/TTbar_Closure_notTriggered_v1/SKIM_MC_TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/output/`  &
