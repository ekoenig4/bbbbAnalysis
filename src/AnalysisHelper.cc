#include "AnalysisHelper.h"
#include "TString.h" // just for Form, else use string
#include "TTreeFormulaGroup.h"
#include "TTreeFormula.h"
#include <iomanip>
#include <boost/variant.hpp>
#include <unordered_map>
#include <sstream>
#include <sys/stat.h>
#include <regex>

using namespace std;

#define DEBUG false

// helper function 
bool is_dir(const char* path) {
    struct stat buf;
    stat(path, &buf);
    return S_ISDIR(buf.st_mode);
}

AnalysisHelper::AnalysisHelper(string cfgname)
{
    TH1::SetDefaultSumw2(true);

    nominal_name_ = "NOMINAL"; // used for nominal systematics

    nsplit_   = 1; // default: only 1 job
    idxsplit_ = 0;

    sample_tree_name_ = "HTauTauTree"; // names to access the sample and efficiency histo
    sample_heff_name_ = "h_eff";

    cout << "@@ Parsing main config : " << cfgname << endl;
    mainCfg_ = unique_ptr<CfgParser>(new CfgParser(cfgname));
    bool success = readMainInfo();
    if (!success){
        cerr << "** AnalysisHelper : error : some information could not be retrieved from config" << endl;
        throw std::runtime_error("Error in initializaton from config");
    }
}

AnalysisHelper::~AnalysisHelper()
{}

bool AnalysisHelper::readMainInfo()
{
    if (!mainCfg_->hasOpt("configs::cutCfg") || !mainCfg_->hasOpt("configs::sampleCfg"))
    {
        cerr << "** AnalysisHelper : error : configs for sample and cut not provided in main cfg" << endl;
        return false;
    }
    string sampleCfgName = mainCfg_->readStringOpt("configs::sampleCfg");
    string cutCfgName = mainCfg_->readStringOpt("configs::cutCfg");
    cout << "@@ sample cfg          : " << sampleCfgName << endl;
    cout << "@@ selection cfg       : " << cutCfgName << endl;
    
    cutCfg_ = unique_ptr<CfgParser>(new CfgParser(cutCfgName));
    sampleCfg_ = unique_ptr<CfgParser>(new CfgParser(sampleCfgName));

    if (!(mainCfg_->hasOpt("general::numberOfThreads"))){
        multithreaded_ = false;
        cout << "@@ multithreaded       : " << std::boolalpha << multithreaded_ << std::noboolalpha << endl;
    }
    else{
        multithreaded_ = true;
        numberOfThreads_ = mainCfg_->readIntOpt("general::numberOfThreads");
        cout << "@@ multithreaded       : " << std::boolalpha << multithreaded_ << " with " << std::noboolalpha << (int) numberOfThreads_ << " threads" << endl;
    }

    if (!(mainCfg_->hasOpt("general::lumi"))) return false;
    lumi_ = mainCfg_->readFloatOpt("general::lumi");
    cout << "@@ lumi                : " << lumi_ << endl;   
    
    if (!(mainCfg_->hasOpt("general::outputFolder"))) return false;
    outputFolder_ = mainCfg_->readStringOpt("general::outputFolder");   
    cout << "@@ output folder       : " << outputFolder_<< endl;

    if (is_dir(outputFolder_.data()))
    {
        cout << "... Output folder " << outputFolder_ << " already exist, delated it or change name\n";
        return false;
    }

    outputFileName_ = "outPlotter.root"; // override default only if specified
    if (mainCfg_->hasOpt("general::outputFileName"))
        outputFileName_ = mainCfg_->readStringOpt("general::outputFileName");
    cout << "@@ output file  name   : " << outputFileName_<< endl;       
    
    if (mainCfg_->hasSect("merge"))
    {
        cout << "@@ will merge these samples: " << endl;
        vector<string> samps_to_merge = mainCfg_->readListOfOpts("merge");
        for (string s : samps_to_merge)
        {
            sample_merge_list_.append(s, mainCfg_->readStringListOpt( string("merge::")+s));
            cout << "   -- " << s << "   <==   ";
            for (unsigned int idx = 0; idx < sample_merge_list_.at(s).size(); ++idx)
            {
                cout << sample_merge_list_.at(s).at(idx);
                if (idx != sample_merge_list_.at(s).size() -1 ) cout << ", ";
                else cout << endl;
            }
        }
    }

    return true;
}

void AnalysisHelper::saveOutputsToFile()
{
    string outFile = outputFolder_ + "/" + outputFileName_ ;
    cout << "@@ Saving all plots to file : " << outFile << endl;
    system (Form("mkdir %s", outputFolder_.c_str())); // not checking if already exists, but return message is harmless

    system (Form("cp %s %s", (mainCfg_  ->getCfgName()).c_str() , outputFolder_.c_str()));
    system (Form("cp %s %s", (cutCfg_   ->getCfgName()).c_str() , outputFolder_.c_str()));
    system (Form("cp %s %s", (sampleCfg_->getCfgName()).c_str() , outputFolder_.c_str()));

    TFile* fOut = TFile::Open(outFile.c_str(), "recreate");
    vector <ordered_map <std::string, std::shared_ptr<Sample>> *> allToSave;
    allToSave.push_back(&data_samples_); 
    allToSave.push_back(&sig_samples_); 
    allToSave.push_back(&bkg_samples_); 
    allToSave.push_back(&datadriven_samples_); 
    
    // nesting orderd: type of events --> sample --> selection --> variable --> systematics

    for (uint itype = 0; itype < allToSave.size(); ++itype)        
    {
        // cout << "itype " << itype << "/" << allToSave.size() << endl;
        for (uint isample = 0; isample < allToSave.at(itype)->size(); ++isample)
        {
            fOut->cd();
            string sampleDir = "";
            sampleDir  = allToSave.at(itype)->at(isample)->getName();
            fOut->mkdir(sampleDir.data());
            fOut->cd   (sampleDir.data());

            // cout << "isample " << isample << "/" << allToSave.at(itype)->size() << endl;
            Sample::selColl& plotSet = allToSave.at(itype)->at(isample)->plots();
            // TH1F *selections = new TH1F((sampleDir + "_selections",plotSet.size(),0,plotSet.size());
            TH1F *hCutInSkimTmp = allToSave.at(itype)->at(isample)->getCutHistogram();

            for (uint isel = 0; isel < plotSet.size(); ++isel)
            {
                bool firstIteration=true;
                string selectionDir = plotSet.key(isel);
                string selectionFullDir = sampleDir + "/" + selectionDir;
                fOut->mkdir(selectionFullDir.data());
                fOut->cd   (selectionFullDir.data());
                // cout << "isel " << isel << "/" << plotSet.size() << endl;

                for (uint ivar = 0; ivar < plotSet.at(isel).size(); ++ivar)
                {
                     // cout << "ivar " << ivar << "/" << plotSet.at(isel).size() << endl;
                    for (uint isyst = 0; isyst < plotSet.at(isel).at(ivar).size(); ++isyst)
                    {
                        // cout << "isyst " << isyst << "/" << plotSet.at(isel).at(ivar).size() << endl;
                        if(firstIteration){
                            firstIteration=false;
                            bool foundBin = false;
                            for(int xBin=1; xBin<=hCutInSkimTmp->GetNbinsX(); ++xBin){
                                if(hCutInSkimTmp->GetXaxis()->GetBinLabel(xBin) == selectionDir){
                                    foundBin=true;
                                    hCutInSkimTmp->SetBinContent(xBin,plotSet.at(isel).at(ivar).at(isyst)->Integral(-1,plotSet.at(isel).at(ivar).at(isyst)->GetNbinsX()+1));
                                    break;
                                }
                            }
                            if(!foundBin) throw std::runtime_error("Bin corresponding to selection " + selectionDir + " not found in the cut histogram");
                        

                        }
                        plotSet.at(isel).at(ivar).at(isyst)->Write();
                        // cout << "DONE" << endl;
                    }
                }
            }
            fOut->cd(sampleDir.data());
            hCutInSkimTmp->Write();
        }
    }

    for (uint itype = 0; itype < allToSave.size(); ++itype)        
    {
        // cout << "itype " << itype << "/" << allToSave.size() << endl;
        for (uint isample = 0; isample < allToSave.at(itype)->size(); ++isample)
        {
            fOut->cd();
            string sampleDir = "";
            sampleDir  = allToSave.at(itype)->at(isample)->getName();
            fOut->cd   (sampleDir.data());
            // cout << "isample " << isample << "/" << allToSave.at(itype)->size() << endl;
            Sample::selColl2D& plotSet = allToSave.at(itype)->at(isample)->plots2D();
            for (uint isel = 0; isel < plotSet.size(); ++isel)
            {
                string selectionDir = plotSet.key(isel);
                string selectionFullDir = sampleDir + "/" + selectionDir;
                fOut->cd   (selectionFullDir.data());
                // cout << "isel " << isel << "/" << plotSet.size() << endl;
                for (uint ivar = 0; ivar < plotSet.at(isel).size(); ++ivar)
                {
                    // cout << "ivar " << ivar << "/" << plotSet.at(isel).size() << endl;
                    for (uint isyst = 0; isyst < plotSet.at(isel).at(ivar).size(); ++isyst)
                    {
                        // cout << "isyst " << isyst << "/" << plotSet.at(isel).at(ivar).size() << endl;
                        plotSet.at(isel).at(ivar).at(isyst)->Write();
                        plotSet.at(isel).at(ivar).at(isyst)->Delete();
                        // cout << "DONE" << endl;
                    }
                }
            }
        }
    }
    cout << "@@ ... saving completed, closing output file" << endl;
    fOut->Close();
    return;        
}

void AnalysisHelper::readSamples()
{
    vector<string> dataSampleNameList        = ( mainCfg_->hasOpt("general::data")        ? mainCfg_->readStringListOpt("general::data")        : vector<string>(0) );
    vector<string> sigSampleNameList         = ( mainCfg_->hasOpt("general::signals")     ? mainCfg_->readStringListOpt("general::signals")     : vector<string>(0) );
    vector<string> bkgSampleNameList         = ( mainCfg_->hasOpt("general::backgrounds") ? mainCfg_->readStringListOpt("general::backgrounds") : vector<string>(0) );
    vector<string> datadrivenSampleNameList  = ( mainCfg_->hasOpt("general::datadriven")  ? mainCfg_->readStringListOpt("general::datadriven")  : vector<string>(0) );

    cout << "@@ Samples : reading samples DATA : " << endl;       
    for (string name : dataSampleNameList)
    {
        shared_ptr<Sample> smp = openSample(name);
        smp->setType(Sample::kData);
        smp->clearWeights(); // no weights should be applied on data -- remove manually all weights read
        data_samples_.append(name, smp);
        // cout << " " << name;
    }
    cout << endl;   
    
    cout << "@@ Samples : reading samples sig  : " << endl;       
    for (string name : sigSampleNameList)
    {
        shared_ptr<Sample> smp = openSample(name);
        smp->setType(Sample::kSig);
        sig_samples_.append(name, smp);
        // cout << " " << name;
    }
    cout << endl;   

    cout << "@@ Samples : reading samples bkg  : " << endl;       
    for (string name : bkgSampleNameList)
    {
        shared_ptr<Sample> smp = openSample(name);
        smp->setType(Sample::kBkg);
        bkg_samples_.append(name, smp);
        if (DEBUG){
            cout << " ..........DEBUG: read bkg sample: " << smp->getName() << " nweights: " << smp->getWeights().size() << endl;
            for (uint iww = 0; iww < smp->getWeights().size(); ++iww)
                cout << " ..........DEBUG:    >> wname: " << smp->getWeights().at(iww).getName() << " nsyst: " << smp->getWeights().at(iww).getNSysts() << endl;
        }
        // cout << " " << name;
    }
    cout << endl;


    for (string name : datadrivenSampleNameList)
    {
        shared_ptr<Sample> smp = openSample(name);
        smp->setType(Sample::kDatadriven);
        datadriven_samples_.append(name, smp);
        if (DEBUG){
            cout << " ..........DEBUG: read datadriven sample: " << smp->getName() << " nweights: " << smp->getWeights().size() << endl;
            for (uint iww = 0; iww < smp->getWeights().size(); ++iww)
                cout << " ..........DEBUG:    >> wname: " << smp->getWeights().at(iww).getName() << " nsyst: " << smp->getWeights().at(iww).getNSysts() << endl;
        }
        // cout << " " << name;
    }
    cout << endl;


    // printSamples(true);

    return;
}

void AnalysisHelper::readAltSysSamples()
{
    // no samples declared
    if (!cutCfg_->hasOpt("altSamplesSystematics::group_list"))
        return;

    vector<string> group_list = cutCfg_->readStringListOpt("altSamplesSystematics::group_list");
    
    // should never happen anyway
    if (group_list.size() == 0)
        return;

    cout << "@@ AltSysSamples : an alternative list of samples for systematics is required for groups : " << endl;
    for (auto gl : group_list)
        cout << "   - " << gl << endl;

    std::vector < ordered_map <std::string, std::shared_ptr<Sample>> * > all_samples = {
        &data_samples_,
        &sig_samples_,
        &bkg_samples_,
        &datadriven_samples_,
    };

    // loop over all samples types
    for (auto group : group_list)
    {

        cout << "   -- -> doing : " << group << endl;
        // read the lists of samples concerned - cfgParser handles errors on missing sections
        vector<string> apply_to = cutCfg_->readStringListOpt(Form("%s::apply_to", group.c_str()));
        vector<string> sources  = cutCfg_->readStringListOpt(Form("%s::sources",  group.c_str()));

        // make the carthesian with directions if requested
        if (cutCfg_->hasOpt(Form("%s::directions",  group.c_str())))
        {
            vector<string> directions  = cutCfg_->readStringListOpt(Form("%s::directions",  group.c_str()));
            std::vector<string> tmp_sources;
            for (auto s : sources) {
                for (auto d : directions) {
                    string tot = s + "_" + d;
                    tmp_sources.push_back(tot);
                }
            }
            sources = tmp_sources;
        }

        // cout << "   -- -- -- individual sources are : " << endl;
        // for (auto s : sources)
        //     cout << "   -- -- -- -- " << s << endl;

        cout << "      -> this source is applied to the following samples : " << endl;
        for (auto s : apply_to)
            cout << "         -- " << s << endl;

        // for every sample, check if it is affected
        for (auto* samples : all_samples)
        {
            std::vector<std::pair<string, shared_ptr<Sample>>> new_samples;
            for (size_t isample = 0; isample < samples->size(); ++isample)
            {
                auto& sample = *(samples->at(isample));
                std::string samplename = sample.getName();

                // is it a sample that I have to do for systs?
                if (find(apply_to.begin(), apply_to.end(), samplename) == apply_to.end())
                    continue;

                // for every source create a new sample
                for (auto source : sources)
                {
                    string newsamplename = Form("%s_%s", samplename.c_str(), source.c_str());
                    string filelistname = "";
                    
                    // look for the new file name - first directly 
                    if (sampleCfg_->hasOpt( Form("samples_%s::%s", group.c_str(), newsamplename.c_str())))
                        filelistname = sampleCfg_->readStringOpt( Form("samples_%s::%s", group.c_str(), newsamplename.c_str()));

                    // try to resolve from variable substitution
                    else
                    {
                        std::vector<std::string> options = sampleCfg_->readListOfOpts(Form("samples_%s", group.c_str()));
                        for (string opt : options)
                        {
                            string repl_opt = std::regex_replace(opt, std::regex("\\$SOURCE"), source);
                            if (repl_opt == newsamplename)
                            {
                                filelistname = sampleCfg_->readStringOpt( Form("samples_%s::%s", group.c_str(), opt.c_str()));

                                if (filelistname.find("$SOURCE") == std::string::npos){
                                    cout << "[ERROR] : you are asking for an alternative sample name with a $SOURCE to be replaced, but the associated filelist has no source" << endl;
                                    cout << "        : sample name : " << newsamplename << endl;
                                    cout << "        : this is in principle wrong unless you REALLY want to have all systematics pointing to the same file (hence => no systematics)" << endl;
                                    cout << "        : aborting. If you want this behavior comment out this control in the code" << endl;
                                    throw std::runtime_error("AnalysisHelper::readAltSysSamples : malformed filelist of alt sample");
                                }

                                filelistname = std::regex_replace(filelistname, std::regex("\\$SOURCE"), source);
                                break;
                            }
                        }
                    }

                    // throw an error if the alt file was not found
                    if (filelistname.size() == 0)
                    {
                        cout << "[ERROR] : I cannot find the file list for the alternative sample " << newsamplename << endl;
                        cout << "          The options that are listed in the cfg are : " << endl; 
                        std::vector<std::string> options = sampleCfg_->readListOfOpts(Form("samples_%s", group.c_str()));
                        for (string opt : options)
                            cout << "           - " << opt << endl;

                        string msg = Form("AnalysisHelper::readAltSysSamples : cannot find the filelist for syst variation of %s", newsamplename.c_str());
                        throw std::runtime_error(msg);
                    }

                    shared_ptr<Sample> newsample (new Sample(newsamplename, filelistname, sample_tree_name_, sample_heff_name_));
                    bool success = newsample->openFileAndTree(selections_);
                    if (!success)
                        throw std::runtime_error("cannot open input file for sample " + newsamplename);

                    newsample->copyStructure(sample);
                    newsample->setType(sample.getType());

                    new_samples.push_back(make_pair(newsamplename, newsample));
                } // loop on sources
            } // loop on samples in this subset

            for (auto& p : new_samples)
                samples->append(p.first, p.second);

        } // loop on all_samples
    } // loop on group lists
}

shared_ptr<Sample> AnalysisHelper::openSample(string sampleName)
{
    if (DEBUG) cout << " ..........DEBUG: entering AnalysisHelper::openSample for sample " << sampleName << endl;

    string filename = sampleCfg_->readStringOpt(Form("samples::%s",sampleName.c_str()));
    
    // if filename is a list, open it directly, otherwise search for the good file list in the directory
    if (is_dir(filename.c_str())) // assume this is a directory then
    {
        if (DEBUG) cout << "..........DEBUG: " << filename << " is a directory, appending the standard list name" << endl;
        filename = filename + string("/goodfiles.txt");
    }
    else if (DEBUG) cout << "..........DEBUG: " << filename << " is a file" << endl;

    shared_ptr<Sample> sample (new Sample(sampleName, filename, sample_tree_name_, sample_heff_name_));
    // if (sampleCfg_->hasOpt(Form("userEffBin::%s",sampleName.c_str())))
    // {
    //     int ubin = sampleCfg_->readIntOpt(Form("userEffBin::%s",sampleName.c_str()));
    //     sample->setEffBin(ubin);
    // }

    bool success = sample->openFileAndTree(selections_);
    if (!success)
    {
        throw std::runtime_error("cannot open input file for sample " + sampleName);
    }

    // for the moment stored in selection cfg -- could be stored in sample cfg instead
    // but I prefer to have all the weights at the same place

    if (!cutCfg_->hasOpt(Form("sampleWeights::%s", sampleName.c_str())))
        return sample;    

    if (DEBUG) cout << " ..........DEBUG: " << sampleName << " has weights associated, will be listed" << endl;
    vector<string> weights = cutCfg_->readStringListOpt(Form("sampleWeights::%s", sampleName.c_str()));
    for (string wname : weights)
    {
        // cout << " +++ adding " << wname << endl;
        if (DEBUG) cout << " ..........DEBUG: -- " << wname << endl;
        Weight w (wname);
        vector<pair<string, string> > wsyst = readWeightSysts(wname, "systematics");
        if (DEBUG){
            cout << " ..........DEBUG:    > nsyst: " << wsyst.size() << endl;
            for (auto pp : wsyst) cout << "................>> DEBUG: " << pp.first << " " << pp.second << endl;
        }
        w.addSysts(wsyst); // can be empty as well
        updateWeightSystAliasesList(wsyst);
        sample->addWeight(w);
    }

    return sample;
}

void AnalysisHelper::readSelections()
{
    if (DEBUG) cout << " ..........DEBUG: entering AnalysisHelper::readSelections" << endl;

    vector<string> selListNames = mainCfg_->readStringListOpt("general::selections");
    vector<Selection> selList;
    cout << "@@ Selections : reading selections : ";       
    for (string sel : selListNames)
    {
        cout << " " << sel;
        selList.push_back(readSingleSelection(sel));
    }
    cout << endl;

    vector<string> CRListNames = mainCfg_->readStringListOpt("general::regions");
    vector<Selection> CRList;
    cout << "@@ Selections : reading regions    : ";       
    for (string sel : CRListNames)
    {
        cout << " " << sel;
        CRList.push_back(readSingleSelection(sel));
    }
    cout << endl;

    // combine
    for (Selection& sel : selList)
    {
        for (Selection& CR : CRList)
        {
            Selection s (sel.getName() + "_" + CR.getName(), "");
            s.extend(sel);
            s.extend(CR);
            selections_.push_back(s);
        }
    }

    if (DEBUG)
    {
        cout << " ..........DEBUG: printing selections" << endl;
        printSelections(true);
    }
    return;
}

void AnalysisHelper::readVariables()
{
    if (mainCfg_->hasOpt("general::variables"))
    {
        variables_ = mainCfg_->readStringListOpt("general::variables");
    }

    if (mainCfg_->hasOpt("general::variables2D"))
    {
        std::vector<string> variables2DPacked = mainCfg_->readStringListOpt("general::variables2D");
        for (string spack : variables2DPacked)
            variables2D_.push_back(unpack2DName(spack));
    }

    cout << "@@ Variables : reading variables : ";       
    for (string var : variables_)
        cout << " " << var;
    cout << endl;

    cout << "@@ Variables : reading 2D variables : ";       
    for (auto var : variables2D_)
        cout << " " << var.first << ":" << var.second;
    cout << endl;

    return;
}


void AnalysisHelper::prepareSamplesHistos()
{
    // to loop all in once
    vector <sampleColl*> allToInit;
    allToInit.push_back(&data_samples_); 
    allToInit.push_back(&sig_samples_); 
    allToInit.push_back(&bkg_samples_); 
    allToInit.push_back(&datadriven_samples_); 

    vector<int> doselW;
    doselW.push_back(0); // no sel W for data!
    doselW.push_back(1);
    doselW.push_back(1);
    doselW.push_back(0); // no sel w for datadriven!

    for (uint ismpc = 0; ismpc < allToInit.size(); ++ismpc) // loop on (data, sig, bkg)
    {
        sampleColl* samcoll = allToInit.at(ismpc);
        for (uint isample = 0; isample < samcoll->size(); ++isample) // loop on samples
        {             
            Sample::selColl& selcoll = samcoll->at(isample)->plots();
            for (uint isel = 0; isel < selections_.size(); ++isel)
            {
                selcoll.append(selections_.at(isel).getName(), Sample::varColl());
                Sample::varColl& varcoll = selcoll.back();
                for (uint ivar = 0; ivar < variables_.size(); ++ivar)
                {
                    string varName = variables_.at(ivar);

                    varcoll.append(varName, Sample::systColl());
                    Sample::systColl& systcoll = varcoll.back();
                    
                    bool   hasUserBinning = cutCfg_->hasOpt(Form("binning::%s", varName.c_str()));
                    int    nbins = -1;
                    float  xlow = -1.;
                    float  xup = -1.;
                    float* binning = 0;

                    if (hasUserBinning)
                    {
                        vector<float> vBins = cutCfg_->readFloatListOpt(Form("binning::%s", varName.c_str()));
                        nbins = vBins.size() -1;
                        
                        if (nbins < 1) // wrong
                        {
                            cerr << "** AnalysisHelper : prepareSamplesHistos : error : binning of " << varName << " must have at least 2 numbers, dummy one used" << endl;                        
                            vBins.clear();
                            vBins.push_back(0.);
                            vBins.push_back(1.);
                            nbins = 1;
                        }
                        
                        binning = new float[nbins+1] ;
                        for (uint ibin = 0; ibin < vBins.size(); ++ibin) binning[ibin] = vBins.at(ibin);
                    }
                    else // no user binning
                    {
                        if (!cutCfg_->hasOpt(Form("histos::%s", varName.c_str())))
                        {
                            cerr << "** AnalysisHelper : prepareSamplesHistos : error : did not find binning for var " << varName << " , dummy one used" << endl;
                            nbins = 1;
                            xlow = 0;
                            xup = 0;
                        }
                        else
                        {
                            vector<float> vBins  = cutCfg_->readFloatListOpt(Form("histos::%s", varName.c_str()));
                            nbins = (int) (vBins.at(0) + 0.5); // just to avoid numerical errors
                            xlow = vBins.at(1);
                            xup  = vBins.at(2);
                        }
                    }
    
                    // prepare histos -- first one is always the nominal one
                    const Sample& currSample = *(samcoll->at(isample));
                    const Selection& currSel = selections_.at(isel);
                    string sampleName = currSample.getName();
                    string selName    = currSel.getName();

                    string hname = formHistoName (sampleName, selName, varName, nominal_name_);
                    std::shared_ptr<TH1F> hist;
                    if (hasUserBinning) hist = make_shared<TH1F> (hname.c_str(), (hname+string(";")+varName+string(";events")).c_str(), nbins, binning);
                    else                hist = make_shared<TH1F> (hname.c_str(), (hname+string(";")+varName+string(";events")).c_str(), nbins, xlow, xup);
                    systcoll.append(nominal_name_, hist);

                    // now loop over available syst and create more histos
                    if (doselW.at(ismpc) == 1)
                    {
                        // sample
                        for (uint iw = 0; iw < currSample.getWeights().size(); ++iw)
                        {
                            const Weight& currW = currSample.getWeights().at(iw);
                            for (int isys = 0; isys < currW.getNSysts(); ++isys)
                            {
                                hname = formHistoName (sampleName, selName, varName, currW.getSystName(isys));
                                std::shared_ptr<TH1F> histS;
                                if (hasUserBinning) histS = make_shared<TH1F> (hname.c_str(), (hname+string(";")+varName+string(";events")).c_str(), nbins, binning);
                                else                histS = make_shared<TH1F> (hname.c_str(), (hname+string(";")+varName+string(";events")).c_str(), nbins, xlow, xup);
                                systcoll.append(currW.getSystName(isys), histS);
                            }
                        }

                        // selection
                        for (uint iw = 0; iw < currSel.getWeights().size(); ++iw)
                        {
                            const Weight& currW = currSel.getWeights().at(iw);
                            for (int isys = 0; isys < currW.getNSysts(); ++isys)
                            {
                                hname = formHistoName (sampleName, selName, varName, currW.getSystName(isys));
                                std::shared_ptr<TH1F> histS;
                                if (hasUserBinning) histS = make_shared<TH1F> (hname.c_str(), (hname+string(";")+varName+string(";events")).c_str(), nbins, binning);
                                else                histS = make_shared<TH1F> (hname.c_str(), (hname+string(";")+varName+string(";events")).c_str(), nbins, xlow, xup);
                                systcoll.append(currW.getSystName(isys), histS);
                            }
                        }
                    }

                    if (hasUserBinning) delete[] binning ; // was allocated with new

                    // set Sumw2() and other stuff for all the histos
                    for (uint ih = 0; ih < systcoll.size(); ++ih)
                    {
                        if (doselW.at(ismpc) != 1) // is data
                            systcoll.at(ih)->Sumw2();
                        else
                            systcoll.at(ih)->SetBinErrorOption(TH1::kPoisson);   
                    }

                } // end loop on 1D variables
            } // end loop on selections
        } // end loop on samples
    } // end loop on (data, sig, bkg)
}


void AnalysisHelper::prepareSamples2DHistos()
{
    // to loop all in once
    vector <sampleColl*> allToInit;
    allToInit.push_back(&data_samples_); 
    allToInit.push_back(&sig_samples_); 
    allToInit.push_back(&bkg_samples_); 
    allToInit.push_back(&datadriven_samples_); 

    vector<int> doselW;
    doselW.push_back(0); // no sel W for data!
    doselW.push_back(1);
    doselW.push_back(1);
    doselW.push_back(0); // no sel W for datadriven!

    for (uint ismpc = 0; ismpc < allToInit.size(); ++ismpc) // loop on (data, sig, bkg)
    {
        sampleColl* samcoll = allToInit.at(ismpc);
        for (uint isample = 0; isample < samcoll->size(); ++isample) // loop on samples
        {             
            Sample::selColl2D& selcoll = samcoll->at(isample)->plots2D();
            for (uint isel = 0; isel < selections_.size(); ++isel)
            {
                selcoll.append(selections_.at(isel).getName(), Sample::varColl2D());
                Sample::varColl2D& varcoll = selcoll.back();
                for (uint ivar = 0; ivar < variables2D_.size(); ++ivar)
                {
                    auto pairName = variables2D_.at(ivar);
                    string varName1 = pairName.first;
                    string varName2 = pairName.second;
                    string packedVarName = pack2DName(varName1, varName2);

                    varcoll.append(packedVarName, Sample::systColl2D());
                    Sample::systColl2D& systcoll = varcoll.back();

                    bool hasUserBinning1 = cutCfg_->hasOpt(Form("binning2D::%s@%s", packedVarName.c_str(), varName1.c_str()));
                    bool hasUserBinning2 = cutCfg_->hasOpt(Form("binning2D::%s@%s", packedVarName.c_str(), varName2.c_str()));

                    vector<float> binning;
                    if (!hasUserBinning1 || !hasUserBinning2) // at least one must have been specified
                      binning = cutCfg_->readFloatListOpt(Form("histos2D::%s", packedVarName.c_str()));

                    int    nbins1   = -1;
                    float  xlow1    = -1.;
                    float  xup1     = -1.;
                    double* binning1 = 0;

                    int    nbins2   = -1;
                    float  xlow2    = -1.;
                    float  xup2     = -1.;
                    double* binning2 = 0;

                    if (hasUserBinning1)
                    {
                        vector<float> vBins = cutCfg_->readFloatListOpt(Form("binning2D::%s@%s", packedVarName.c_str(), varName1.c_str()));
                        nbins1 = vBins.size() -1;
                        
                        if (nbins1 < 1) // wrong
                        {
                            cerr << "** AnalysisHelper : prepareSamples2DHistos : error : binning of " << packedVarName << "@" << varName1 << " must have at least 2 numbers, dummy one used" << endl;                        
                            vBins.clear();
                            vBins.push_back(0.);
                            vBins.push_back(1.);
                            nbins1 = 1;
                        }
                        
                        binning1 = new double[nbins1+1] ;
                        for (uint ibin = 0; ibin < vBins.size(); ++ibin) binning1[ibin] = vBins.at(ibin);
                    }
                    else
                    {
                        nbins1 =  (int) (binning.at(0) + 0.5); // just to avoid numerical errors
                        xlow1  =  binning.at(1);
                        xup1   =  binning.at(2);
                    }

                    if (hasUserBinning2)
                    {
                        vector<float> vBins = cutCfg_->readFloatListOpt(Form("binning2D::%s@%s", packedVarName.c_str(), varName2.c_str()));
                        nbins2 = vBins.size() -1;
                        
                        if (nbins2 < 1) // wrong
                        {
                            cerr << "** AnalysisHelper : prepareSamples2DHistos : error : binning of " << packedVarName << "@" << varName2 << " must have at least 2 numbers, dummy one used" << endl;                        
                            vBins.clear();
                            vBins.push_back(0.);
                            vBins.push_back(1.);
                            nbins2 = 1;
                        }
                        
                        binning2 = new double[nbins2+1] ;
                        for (uint ibin = 0; ibin < vBins.size(); ++ibin) binning2[ibin] = vBins.at(ibin);
                    }
                    else
                    {
                        nbins2 =  (int) (binning.at(3) + 0.5); // just to avoid numerical errors
                        xlow2  =  binning.at(4);
                        xup2   =  binning.at(5);
                    }

                    // prepare histos -- first one is always the nominal one
                    const Sample& currSample = *(samcoll->at(isample));
                    const Selection& currSel = selections_.at(isel);
                    string sampleName = currSample.getName();
                    string selName    = currSel.getName();

                    string hname = formHisto2DName (sampleName, selName, varName1, varName2, nominal_name_);
                    std::shared_ptr<TH2F> hist;
                    if (hasUserBinning1 && hasUserBinning2)        hist = make_shared<TH2F> (hname.c_str(), (hname+string(";")+varName1+string(";")+varName2).c_str(), nbins1, binning1, nbins2, binning2);
                    else if (hasUserBinning1 && !hasUserBinning2)  hist = make_shared<TH2F> (hname.c_str(), (hname+string(";")+varName1+string(";")+varName2).c_str(), nbins1, binning1, nbins2, xlow2, xup2);
                    else if (!hasUserBinning1 && hasUserBinning2)  hist = make_shared<TH2F> (hname.c_str(), (hname+string(";")+varName1+string(";")+varName2).c_str(), nbins1, xlow1, xup1, nbins2, binning2);
                    else                                           hist = make_shared<TH2F> (hname.c_str(), (hname+string(";")+varName1+string(";")+varName2).c_str(), nbins1, xlow1, xup1, nbins2, xlow2, xup2);
                    systcoll.append(nominal_name_, hist);

                    /*
                    // now loop over available syst and create more histos
                    if (doselW.at(ismpc) == 1)
                    {
                        // sample
                        for (uint iw = 0; iw < currSample.getWeights().size(); ++iw)
                        {
                            const Weight& currW = currSample.getWeights().at(iw);
                            for (int isys = 0; isys < currW.getNSysts(); ++isys)
                            {
                                hname = formHistoName (sampleName, selName, varName, currW.getSystName(isys));
                                std::shared_ptr<TH1F> histS;
                                if (hasUserBinning) histS = make_shared<TH1F> (hname.c_str(), hname.c_str(), nbins, binning);
                                else                histS = make_shared<TH1F> (hname.c_str(), hname.c_str(), nbins, xlow, xup);
                                systcoll.append(nominal_name_, histS);
                            }
                        }

                        // selection
                        for (uint iw = 0; iw < currSel.getWeights().size(); ++iw)
                        {
                            const Weight& currW = currSel.getWeights().at(iw);
                            for (int isys = 0; isys < currW.getNSysts(); ++isys)
                            {
                                hname = formHistoName (sampleName, selName, varName, currW.getSystName(isys));
                                std::shared_ptr<TH1F> histS;
                                if (hasUserBinning) histS = make_shared<TH1F> (hname.c_str(), hname.c_str(), nbins, binning);
                                else                histS = make_shared<TH1F> (hname.c_str(), hname.c_str(), nbins, xlow, xup);
                                systcoll.append(currW.getSystName(isys), histS);
                            }
                        }
                    }
                */
                    if (hasUserBinning1) delete[] binning1 ; // was allocated with new
                    if (hasUserBinning2) delete[] binning2 ; // was allocated with new

                    // set Sumw2() and other stuff for all the histos
                    for (uint ih = 0; ih < systcoll.size(); ++ih)
                    {
                        if (doselW.at(ismpc) != 1) // is data
                            systcoll.at(ih)->Sumw2();
                        else
                            systcoll.at(ih)->SetBinErrorOption(TH1::kPoisson);   
                    }

                } // end loop on 1D variables
            } // end loop on selections
        } // end loop on samples
    } // end loop on (data, sig, bkg)
}


vector<pair<string, string> > AnalysisHelper::readWeightSysts(std::string name, std::string section)
{
    vector<pair<string, string>> systs;
    if (!cutCfg_->hasOpt(Form("%s::%s", section.c_str(), name.c_str())))
    {
        return systs;
    }

    vector<string> v = cutCfg_->readStringListOpt(Form("%s::%s", section.c_str(), name.c_str()));
    for (string elem : v)
    {
        std::string delimiter = ":";
        size_t pos = 0;
        vector<std::string> tokens;
        while ((pos = elem.find(delimiter)) != std::string::npos)
        {
            tokens.push_back(elem.substr(0, pos));
            elem.erase(0, pos + delimiter.length());
        }
        tokens.push_back(elem); // last part splitted
        if(tokens.size() == 1) tokens.push_back(elem); //to handle better weights from samples
        if (tokens.size() != 2)
        {
            cerr << "** AnalysisHelper : readWeightSyst : error : could not parse entry " << elem << " of " << section << "::" << name << " , skipping..." << endl;
            continue;
        }

        systs.push_back(make_pair(tokens.at(0), tokens.at(1)));
    }
    return systs;

}

Selection AnalysisHelper::readSingleSelection (std::string name)
{
    if (!cutCfg_->hasOpt(Form("selections::%s",name.c_str())))
    {
        cerr << "** AnalysisHelper : readSingleSelection : error : could not find selection " << name << endl;
        return Selection("dummy", "1==0");
    }

    Selection s(name, "");
    vector<string> selDef = cutCfg_->readStringListOpt(Form("selections::%s", name.c_str())) ;
    for (string part : selDef)
    {
        if (cutCfg_->hasOpt(Form("selections::%s", part.c_str())))
            s.extend(readSingleSelection(part));
        else
            s.extend(part.c_str()); // was a block of selection in TCut form
    }
    
    // now fetch weights if any and update
    if (!cutCfg_->hasOpt(Form("selectionWeights::%s", name.c_str())))
        return s;
    
    vector<string> weights = cutCfg_->readStringListOpt(Form("selectionWeights::%s", name.c_str()));
    for (string wname : weights)
    {
        // cout << " +++ adding " << wname << endl;
        Weight w (wname);
        vector<pair<string, string> > wsyst = readWeightSysts(wname, "systematics");

        w.addSysts(wsyst); // can be empty as well
        updateWeightSystAliasesList(wsyst);
        s.addWeight(w);
    }

    return s;
}

void AnalysisHelper::printSelections(bool printWeights, bool printSysts)
{
    cout << "@@ Selection list ------- " << endl;
    for (unsigned int i = 0; i < selections_.size(); ++i)
    {
        cout << " >> " << selections_.at(i).getName() << " " << selections_.at(i).getValue().GetTitle() << endl;
        if (printWeights)
        {
            cout << "     ~~~> ";
            for (unsigned int iw = 0; iw < selections_.at(i).getWeights().size(); ++iw)
            {
                cout << selections_.at(i).getWeights().at(iw).getName() << " ";
            }
            cout << endl;
        }

        if (printSysts)
        {
            // syst of weights
            for (unsigned int iw = 0; iw < selections_.at(i).getWeights().size(); ++iw)
            {
                cout << selections_.at(i).getWeights().at(iw).getName() << " ::: ";
                for (int isys = 0; isys < selections_.at(i).getWeights().at(iw).getNSysts(); ++isys)
                    cout << selections_.at(i).getWeights().at(iw).getSystName(isys) <<"="<<selections_.at(i).getWeights().at(iw).getSyst(isys) << " , ";
                cout << endl;
            }
        }
    }
    cout << "   ---------------------- " << endl;
}

void AnalysisHelper::printSamples(bool printWeights, bool printSysts)
{
    cout << "@@ Samples list ------- " << endl;
    cout << "   Data:" << endl;
    for (unsigned int i = 0; i < data_samples_.size(); ++i)
    {
        cout << "   >> " << data_samples_.at(i)->getName() << endl;
        if (printWeights)
        {
            cout << "       ~~~> ";
            for (unsigned int iw = 0; iw < data_samples_.at(i)->getWeights().size(); ++iw)
            {
                cout << data_samples_.at(i)->getWeights().at(iw).getName() << " ";
            }
            cout << endl;
        }

        if (printSysts)
        {
            // syst of weights
            for (unsigned int iw = 0; iw < selections_.at(i).getWeights().size(); ++iw)
            {
                cout << selections_.at(i).getWeights().at(iw).getName() << " ::: ";
                for (int isys = 0; isys < selections_.at(i).getWeights().at(iw).getNSysts(); ++isys)
                    cout << selections_.at(i).getWeights().at(iw).getSystName(isys) <<"="<<selections_.at(i).getWeights().at(iw).getSyst(isys) << " , ";
                cout << endl;
            }
        }
    }

    cout << "   Signal:" << endl;
    for (unsigned int i = 0; i < sig_samples_.size(); ++i)
    {
        cout << "   >> " << sig_samples_.at(i)->getName() << endl;
        if (printWeights)
        {
            cout << "       ~~~> ";
            for (unsigned int iw = 0; iw < sig_samples_.at(i)->getWeights().size(); ++iw)
            {
                cout << sig_samples_.at(i)->getWeights().at(iw).getName() << " ";
            }
            cout << endl;
        }

        if (printSysts)
        {
            // syst of weights
            for (unsigned int iw = 0; iw < selections_.at(i).getWeights().size(); ++iw)
            {
                cout << selections_.at(i).getWeights().at(iw).getName() << " ::: ";
                for (int isys = 0; isys < selections_.at(i).getWeights().at(iw).getNSysts(); ++isys)
                    cout << selections_.at(i).getWeights().at(iw).getSystName(isys) <<"="<<selections_.at(i).getWeights().at(iw).getSyst(isys) << " , ";
                cout << endl;
            }
        }
    }

    cout << "   Background:" << endl;
    for (unsigned int i = 0; i < bkg_samples_.size(); ++i)
    {
        cout << "   >> " << bkg_samples_.at(i)->getName() << endl;
        if (printWeights)
        {
            cout << "       ~~~> ";
            for (unsigned int iw = 0; iw < bkg_samples_.at(i)->getWeights().size(); ++iw)
            {
                cout << bkg_samples_.at(i)->getWeights().at(iw).getName() << " ";
            }
            cout << endl;
        }

        if (printSysts)
        {
            // syst of weights
            for (unsigned int iw = 0; iw < selections_.at(i).getWeights().size(); ++iw)
            {
                cout << selections_.at(i).getWeights().at(iw).getName() << " ::: ";
                for (int isys = 0; isys < selections_.at(i).getWeights().at(iw).getNSysts(); ++isys)
                    cout << selections_.at(i).getWeights().at(iw).getSystName(isys) <<"="<<selections_.at(i).getWeights().at(iw).getSyst(isys) << " , ";
                cout << endl;
            }
        }
    }


    cout << "   Datadriven:" << endl;
    for (unsigned int i = 0; i < datadriven_samples_.size(); ++i)
    {
        cout << "   >> " << datadriven_samples_.at(i)->getName() << endl;
        if (printWeights)
        {
            cout << "       ~~~> ";
            for (unsigned int iw = 0; iw < datadriven_samples_.at(i)->getWeights().size(); ++iw)
            {
                cout << datadriven_samples_.at(i)->getWeights().at(iw).getName() << " ";
            }
            cout << endl;
        }

        if (printSysts)
        {
            // syst of weights
            for (unsigned int iw = 0; iw < selections_.at(i).getWeights().size(); ++iw)
            {
                cout << selections_.at(i).getWeights().at(iw).getName() << " ::: ";
                for (int isys = 0; isys < selections_.at(i).getWeights().at(iw).getNSysts(); ++isys)
                    cout << selections_.at(i).getWeights().at(iw).getSystName(isys) <<"="<<selections_.at(i).getWeights().at(iw).getSyst(isys) << " , ";
                cout << endl;
            }
        }
    }


    cout << "   ---------------------- " << endl;
}

string AnalysisHelper::formHistoName (string sample, string sel, string var, string syst)
{
    string name = "";
    name += sample;
    name += "_";
    name += sel;
    name += "_";
    name += var;
    if (syst != nominal_name_)
    {
        name += "_";
        name += syst;
    }
    return name;
}

string AnalysisHelper::formHisto2DName (string sample, string sel, string var1, string var2, string syst)
{
    string name = "";
    name += sample;
    name += "_";
    name += sel;
    name += "_";
    name += var1;
    name += "_";
    name += var2;
    if (syst != nominal_name_)
    {
        name += "_";
        name += syst;
    }
    return name;
}

void AnalysisHelper::fillHistosSample(Sample& sample, std::promise<void> thePromise)
{
    cout << "@@ Filling histograms of sample " << sample.getName() << endl;

    activateBranches(sample);

    TChain* tree = sample.getTree();
    
    // setup selection group
    shared_ptr<TTreeFormulaGroup> fg = make_shared<TTreeFormulaGroup>(true);
    vector<TTreeFormula*> vTTF;
    for (unsigned int isel = 0; isel < selections_.size(); ++isel)
    {
        // note: no need to call later delete, because fg is set as the owner of the member TTF
        // cout << selections_.at(isel).getValue().GetTitle() << endl;
        TTreeFormula* TTF = new TTreeFormula (Form("TTF_%i", isel), selections_.at(isel).getValue().GetTitle(), tree);
        vTTF.push_back(TTF);
        fg->SetNotify(TTF);
    }
    tree->SetNotify(fg.get());

    // prepare container for the variables and weights
    // data structure used: a unordered_map (fast lookup) with
    // map[name][variant]
    // the value is a variant type that can contain float, double, int, bools...
    // the name is the weight/variable name (same as used in setBranchAddress)
    //
    // NOTE: boost::variant also available in C++17, but no adequate compiler in CMSSW_7_4_7
    // could be in principle changed to std::variant if a newer release is used
    //
    // A second structure systMap is used to remap the systematics names in the histos to the
    // nominal and shifted weight names. Stored as systMap[systName as in histo] = <nominal_name in tree, syst_name in tree>
    // when histos systs are applied, retrieve the two names using the key that is stored in the histogram name

    typedef boost::variant<bool, int, float, double> varType;
    unordered_map<string, varType> valuesMap;
    unordered_map<string, pair<string, string>> systMap;

    if (DEBUG) cout << " ..........DEBUG: AnalysisHelper : fillHistosSample : going to setup map for SetBranchAddress --- VARS" << endl;
    // loop over all variables and weights to initialize the map
    for (unsigned int ivar = 0; ivar < variables_.size(); ++ivar)
    {
        if (valuesMap.find(variables_.at(ivar)) == valuesMap.end())
        {
            valuesMap[variables_.at(ivar)] = float(0); // after will change to the proper type
            if (DEBUG) cout << " .......... >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " , adding var " << variables_.at(ivar) << endl;
        }
        else
            cout << "** Warning: AnalysisHelper::fillHistosSample : sample : " << sample.getName() << " , variable " << variables_.at(ivar) << " was already added to valuesMap, duplicated?" << endl;
    }

    if (DEBUG) cout << " ..........DEBUG: AnalysisHelper : fillHistosSample : going to setup map for SetBranchAddress --- VARS 2D" << endl;
    for (unsigned int ivar = 0; ivar < variables2D_.size(); ++ivar)
    {
        string var1 = variables2D_.at(ivar).first;
        string var2 = variables2D_.at(ivar).second;
        if (valuesMap.find(var1) == valuesMap.end())
        {
            valuesMap[var1] = float(0); // after will change to the proper type
            if (DEBUG) cout << " .......... >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " , adding var 2D " << var1 << endl;
        }
        if (valuesMap.find(var2) == valuesMap.end())
        {
            valuesMap[var2] = float(0); // after will change to the proper type
            if (DEBUG) cout << " .......... >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " , adding var 2D " << var2 << endl;
        }
    }

    if (DEBUG) cout << " ..........DEBUG: AnalysisHelper : fillHistosSample : going to setup map for SetBranchAddress --- SAMPLE" << endl;
    // weoghts - sample
    if(sample.getType() != Sample::kData)
    {
        for (uint iw = 0; iw < sample.getWeights().size(); ++iw)
        {
            const Weight& currW = sample.getWeights().at(iw);
            string wname = currW.getName();
            if (valuesMap.find(wname) == valuesMap.end())
            {
                if (DEBUG) cout << " .......... >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " , adding sample weight " << wname << endl;
                valuesMap[wname] = float(0);
                for (int isys = 0; isys < currW.getNSysts(); ++isys)
                {
                    string sysName = currW.getSyst(isys);
                    if (valuesMap.find(sysName) == valuesMap.end())
                    {
                        if (DEBUG) cout << " .......... >> >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " , adding syst weight " << sysName << endl;
                        if (DEBUG) cout << " .......... >> >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " , adding syst map    " << currW.getSystName(isys) << " = [" << wname << " , " << sysName << "]" << endl;
                        valuesMap[sysName] = float(0);
                        systMap[currW.getSystName(isys)] = make_pair(wname, sysName);
                    }
                    else
                        cout << "** Warning: AnalysisHelper::fillHistosSample : sample : " << sample.getName() << " , syst " << sysName << " from weight " << wname << " was already added to valuesMap, duplicated?" << endl;
                }
            }
            else
                cout << "** Warning: AnalysisHelper::fillHistosSample : sample : " << sample.getName() << " , weight " << wname << " was already added to valuesMap, duplicated?" << endl;
        }

        if (DEBUG) cout << " ..........DEBUG: AnalysisHelper : fillHistosSample : going to setup map for SetBranchAddress --- SELECTIONS" << endl;
        // selection -- probably not the most efficient as many w are shared so will be chacked many times
        // but this function is called only a few times
        for (uint isel = 0; isel < selections_.size(); ++isel)
        {
            const Selection& currSel = selections_.at(isel);
            for (uint iw = 0; iw < currSel.getWeights().size(); ++iw)
            {
                const Weight& currW = currSel.getWeights().at(iw);
                string wname = currW.getName();
                if (valuesMap.find(wname) == valuesMap.end())
                {
                    if (DEBUG) cout << " .......... >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " : sel : " << currSel.getName() << " , adding selection weight " << wname << endl;
                    valuesMap[wname] = float(0);
                    for (int isys = 0; isys < currW.getNSysts(); ++isys)
                    {
                        string sysName = currW.getSyst(isys);
                        if (valuesMap.find(sysName) == valuesMap.end())
                        {
                            if (DEBUG) cout << " .......... >> >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " : sel : " << currSel.getName() << " , adding selection syst weight " << sysName << endl;
                            if (DEBUG) cout << " .......... >> >> DEBUG: AnalysisHelper : fillHistosSample : sample : " << sample.getName() << " : sel : " << currSel.getName() << " , adding selection syst map    " << currW.getSystName(isys) << " = [" << wname << " , " << sysName << "]" << endl;
                            valuesMap[sysName] = float(0);
                            systMap[currW.getSystName(isys)] = make_pair(wname, sysName);
                        }
                    }
                }
            }
        }
    }

    if (DEBUG) cout << " ..........DEBUG: AnalysisHelper : fillHistosSample : valueMap created, going to assess branch types... " << endl;

    // decide types
    TObjArray *branchList = tree->GetListOfBranches();
    for (auto it = valuesMap.begin(); it != valuesMap.end(); ++it)
    {
        TBranch* br = (TBranch*) branchList->FindObject(it->first.c_str());
        if (!br){
            // if branch not found, check if a default version is fiven in the cfg
            // if (sampleCfg_ -> hasOpt( Form("defaultWeight::%s",sample.getName().c_str())))
            if (hasDefaultWeight(it->first.c_str()))
            {
                double def_val = getDefaultWeight(it->first.c_str());
                cout << " >> INFO: in sample " << sample.getName() << " will use the default value of " << def_val << " for weight " << it->first.c_str() << endl;
                it->second = def_val;
                continue; // do not continue to set the branch address
            }
            else
            {
                // cerr << endl << "** ERROR: AnalysisHelper::fillHistosSample : sample : " << sample.getName() << " does not have branch " << it->first << ", expect a crash..." << endl;
                cerr << endl << "** ERROR: AnalysisHelper::fillHistosSample : sample : " << sample.getName() << " does not have branch " << it->first << ", aborting to avoid a crash..." << endl;
                cerr <<         "**        Please note that you can set a default value for a missing branch using the syntax [defaultWeight] weight_name = default_value in the selection cfg" << endl;
                exit(1);
            }
        }

        string brName = br->GetTitle();
        if (brName.find(string("/F")) != string::npos) // F : a 32 bit floating point (Float_t)
        {
            it->second = float(0.0);
            tree->SetBranchAddress(it->first.c_str(), &boost::get<float>(it->second));
        }
        else if (brName.find(string("/I")) != string::npos) // I : a 32 bit signed integer (Int_t)
        {
            it->second = int(0);
            tree->SetBranchAddress(it->first.c_str(), &boost::get<int>(it->second));
        }

        else if (brName.find(string("/D")) != string::npos) // D : a 64 bit floating point (Double_t)
        {
            it->second = double(0.0);
            tree->SetBranchAddress(it->first.c_str(), &boost::get<double>(it->second));
        }
        
        else if (brName.find(string("/O")) != string::npos) // O : [the letter o, not a zero] a boolean (Bool_t)
        {
            it->second = bool(false);
            tree->SetBranchAddress(it->first.c_str(), &boost::get<bool>(it->second));
        }
        
        else
        {
            cerr << "** AnalysisHelper : error : could not detect the type of var " << it->first
            << " (title: " << br->GetTitle() << " , name: " << br->GetName() << " , className: " << br->GetClassName() << ")" << endl;
            cerr << "   ... assuming float, but errors could happen" << endl;
            it->second = float(0.0);
            tree->SetBranchAddress(it->first.c_str(), &boost::get<float>(it->second));
        }
    }



    //////////////////////////////////////
    ////////////////////// loop on entries

    long long int nEvts  = sample.getEntries();
    long long int nStep  = nEvts/nsplit_;
    long long int nStart = nStep*idxsplit_;
    long long int nStop  = nStart+nStep;

    // to avoid for numerical errors (summing 1 to a TH1F can give rounding errors --> nEvts != chain.getEnries())
    // if the splitted job is the last one, let it go until chain completion
    // at the same time, it ensures that the remainder of the integer division is not skipped
    
    bool isLast = (idxsplit_ == nsplit_-1 ? true : false);
    // the last jobs takes up all the remainder of division -- as long as nsplit is O(10-100) is not a big problem
    // if (idxsplit_ == nsplit_-1)
    //     nStop = nEvts;

    if (DEBUG) cout << " ..........DEBUG: AnalysisHelper : fillHistosSample : going to loop on tree entries... " << endl;
    Sample::selColl& plots = sample.plots();
    Sample::selColl2D& plots2D = sample.plots2D();
    for (long long iEv = nStart; true; ++iEv)
    {
        int got = tree->GetEntry(iEv);
        if (!isLast && iEv >= nStop) break;
        if (got == 0) break; // end of the chain
        if (iEv % 500000 == 0) cout << "   ... reading " << iEv << " / " << nEvts << endl;

        double wEvSample = 1.0;
        // get the product of all the event weights -- sample
        if (sample.getType() != Sample::kData){
            for (unsigned int iw = 0; iw < sample.getWeights().size(); ++iw)
            {
                wEvSample *= boost::apply_visitor(get_variant_as_double(), valuesMap[sample.getWeights().at(iw).getName()]);
            }
        }

        for (unsigned int isel = 0; isel < selections_.size(); ++isel)
        {

            if (!(vTTF.at(isel)->EvalInstance())) continue;


            double wEvSel = 1.0;
            const Selection& currSel = selections_.at(isel);
            if (sample.getType() != Sample::kData)
            {
                for (unsigned int iw = 0; iw < currSel.getWeights().size(); ++iw)
                {   
                    wEvSel *= boost::apply_visitor(get_variant_as_double(), valuesMap[currSel.getWeights().at(iw).getName()]);
                    
                    // if (sample.getType() == Sample::kBkg)
                    //     cout << "~~~~~~~  : ~~~ " << iEv << " / evt sel: " << currSel.getWeights().at(iw).getName() << " = " << boost::apply_visitor(get_variant_as_double(), valuesMap[currSel.getWeights().at(iw).getName()]) << endl;
                }
            }
            
            // loop on all vars to fill
            for (unsigned int ivar = 0; ivar < variables_.size(); ++ivar)
            {
                double varvalue = boost::apply_visitor( get_variant_as_double(), valuesMap[variables_.at(ivar)]);
                if (sample.getType() == Sample::kData)
                    plots.at(isel).at(ivar).at(0)->Fill(varvalue);
                else
                    plots.at(isel).at(ivar).at(0)->Fill(varvalue, wEvSample*wEvSel);
                
                // if (sample.getType() == Sample::kBkg)
                //     cout << ">>>>  : >>> " << iEv << " / FILLING " << plots.at(isel).at(ivar).at(0)->GetName() << " varvalue:" << varvalue << " wEvSample:" << wEvSample << " wEvSel:" << wEvSel << " new integral:" << plots.at(isel).at(ivar).at(0)->Integral() << endl;

                if (sample.getType() != Sample::kData)
                {
                    for (unsigned int isyst = 1; isyst < plots.at(isel).at(ivar).size(); ++isyst) // start from 1, as 0 is nominal case
                    {
                        auto names = systMap.at(plots.at(isel).at(ivar).key(isyst));
                        double wnom   = boost::apply_visitor( get_variant_as_double(), valuesMap[names.first]);
                        double wshift = boost::apply_visitor( get_variant_as_double(), valuesMap[names.second]);
                        double wnew   = ( wshift == 0 && wnom == 0 ? 0.0 : wEvSample*wEvSel*wshift/wnom); // a protection from null weights. FIXME: should I redo all the multiplication to avoid this effect?
                        plots.at(isel).at(ivar).at(isyst)->Fill(varvalue, wnew);                        
                        // cout << " :::::: DDDDD ::::: " << wEvSample*wEvSel*wshift/wnom << " " << wnew << " " << wEvSample << " " << wEvSel << " " << wshift << " " << wnom << " " << names.first << " " << names.second << " " << sample.getName() << " " << iEv << endl;
                    }
                }
            }

            // loop on all 2D vars to fill
            // loop on all vars to fill
            for (unsigned int ivar = 0; ivar < variables2D_.size(); ++ivar)
            {
                string var1 = variables2D_.at(ivar).first;
                string var2 = variables2D_.at(ivar).second;
                double varvalue1 = boost::apply_visitor( get_variant_as_double(), valuesMap[var1]);
                double varvalue2 = boost::apply_visitor( get_variant_as_double(), valuesMap[var2]);
                if (sample.getType() == Sample::kData)
                    plots2D.at(isel).at(ivar).at(0)->Fill(varvalue1, varvalue2);
                else
                    plots2D.at(isel).at(ivar).at(0)->Fill(varvalue1, varvalue2, wEvSample*wEvSel);
                
                if (sample.getType() != Sample::kData)
                {
                    for (unsigned int isyst = 1; isyst < plots2D.at(isel).at(ivar).size(); ++isyst) // start from 1, as 0 is nominal case
                    {
                        auto names = systMap.at(plots2D.at(isel).at(ivar).key(isyst));
                        double wnom   = boost::apply_visitor( get_variant_as_double(), valuesMap[names.first]);
                        double wshift = boost::apply_visitor( get_variant_as_double(), valuesMap[names.second]);
                        double wnew   = ( wshift == 0 && wnom == 0 ? 0.0 : wEvSample*wEvSel*wshift/wnom); // a protection from null weights. FIXME: should I redo all the multiplication to avoid this effect?
                        plots2D.at(isel).at(ivar).at(isyst)->Fill(varvalue1, varvalue2, wnew);                        
                        // cout << " :::::: DDDDD ::::: " << wEvSample*wEvSel*wshift/wnom << " " << wnew << " " << wEvSample << " " << wEvSel << " " << wshift << " " << wnom << " " << names.first << " " << names.second << " " << sample.getName() << " " << iEv << endl;
                    }
                }
            }
        }
    }

    // filling is finished, scale to the sample denominator evt sum to include acceptance
    if (sample.getType() != Sample::kData && sample.getType() != Sample::kDatadriven)
        sample.scaleAll(lumi_, weight_aliases_);

    if (multithreaded_)
        thePromise.set_value();
}

void AnalysisHelper::activateBranches(Sample& sample)
{
    if (DEBUG) cout << " ..........DEBUG: entering AnalysisHelper::activateBranches" << endl;

    TChain* tree = sample.getTree();
    tree->SetBranchStatus("*", 0);

    // activate all vars
    for (string var : variables_)
    {
        tree->SetBranchStatus(var.c_str(), 1);
    }

    for (auto var2d : variables2D_)
    {
        tree->SetBranchStatus(var2d.first.c_str(), 1);
        tree->SetBranchStatus(var2d.second.c_str(), 1);
    }

    if (DEBUG) cout << " ..........DEBUG: activated var branches" << endl;

    // activate all weights
    // sample
    if(sample.getType() != Sample::kData){
        for (uint iw = 0; iw < sample.getWeights().size(); ++iw)
        {
            const Weight& currW = sample.getWeights().at(iw);

            // this is not default weight for this sample
            if (hasBranch(tree, currW.getName()))
                tree->SetBranchStatus(currW.getName().c_str(), 1);
            
            for (int isys = 0; isys < currW.getNSysts(); ++isys)
            {
               //currW.getSyst(isys); // <----- keep an eye on it. It happened to throw range 
                if (hasBranch(tree, currW.getSyst(isys)))
                    tree->SetBranchStatus(currW.getSyst(isys).c_str(), 1); 
            }
        }
        if (DEBUG) cout << " ..........DEBUG: activated sample weights branches" << endl;
    }

    // selection -- probably not the most efficient as many w are shared so will be chacked many times
    // but this function is called only a few times
    if(sample.getType() != Sample::kData){
        for (uint isel = 0; isel < selections_.size(); ++isel)
        {
            const Selection& currSel = selections_.at(isel);
            for (uint iw = 0; iw < currSel.getWeights().size(); ++iw)
            {
                const Weight& currW = currSel.getWeights().at(iw);
                if (hasBranch(tree, currW.getName()))
                    tree->SetBranchStatus(currW.getName().c_str(), 1);
                for (int isys = 0; isys < currW.getNSysts(); ++isys)
                {
                    if (hasBranch(tree, currW.getSyst(isys)))
                       tree->SetBranchStatus(currW.getSyst(isys).c_str(), 1); 
                }
            }
        }
        if (DEBUG) cout << " ..........DEBUG: activated selections weights branches" << endl;
    }

    // // activate all variables for cuts
    TObjArray* branchList =  tree->GetListOfBranches();
    int nBranch = tree->GetNbranches(); // all trees in the chain are identical
    for (int iB = 0 ; iB < nBranch; ++iB)
    {
        string bName = branchList->At(iB)->GetName();
        for (uint isel = 0; isel < selections_.size(); isel++)
        {
            string theCut = selections_.at(isel).getValue().GetTitle(); // gives the content of tCut as char*
            if (theCut.find(bName) != string::npos)
            {
                tree->SetBranchStatus (bName.c_str(), 1);
            }
        }
    }
    if (DEBUG) cout << " ..........DEBUG: activated cut variables branches" << endl;

}

pair <string, string> AnalysisHelper::unpack2DName (string packedName)
{
    stringstream packedNameS(packedName);
    string segment;
    vector<string> unpackedNames;
    while(std::getline(packedNameS, segment, ':'))
        unpackedNames.push_back(segment);
    if (unpackedNames.size() != 2)
    {
        cout << "** AnalysisHelper : unpack2DName : error : couldn't interpret 2D variable name " << packedName << " (expecting X:Y)" << endl;
        return make_pair("", "");
    }
    return make_pair(unpackedNames.at(0), unpackedNames.at(1));
}

string AnalysisHelper::pack2DName (string name1, string name2)
{
    return (name1 + string(":") + name2);
}


// vector<const Weight*> AnalysisHelper::getWeightsWithSyst (const Selection& sel, const Sample& sample)
// {
//     vector<const Weight*> vWeights;

//     // sample
//     for (uint iw = 0; iw < sample.getWeights().size(); ++iw)
//     {
//         if (sample.getWeights().at(iw).hasSysts())
//             vWeights.push_back(&(sample.getWeights().at(iw)));
//     }

//     // selection
//     for (uint iw = 0; iw < sel.getWeights().size(); ++iw)
//     {
//         if (sel.getWeights().at(iw).hasSysts())
//             vWeights.push_back(&(sel.getWeights().at(iw)));
//     }

//     return vWeights;

//     // 1) const for pointers
//     // 2) pointer to element of a vector
// }

// bool AnalysisHelper::readSingleSelection (std::string name, bool isComposed)
// {
//     if (!cutCfg_->hasOpt(name))
//     {
//         cerr << "** AnalysisHelper : readSingleSelection : error : could not find selection " << name << endl;
//         return false;
//     }


// }

void AnalysisHelper::fillHistos()
{
    // for (uint isample = 0; isample < data_samples_.size(); ++isample) // loop on samples
    // {             
    //     fillHistosSample(*(data_samples_.at(isample)));
    // }

    // // sig
    // for (uint isample = 0; isample < sig_samples_.size(); ++isample) // loop on samples
    // {             
    //     fillHistosSample(*(sig_samples_.at(isample)));
    // }

    // // bkg    
    // for (uint isample = 0; isample < bkg_samples_.size(); ++isample) // loop on samples
    // {             
    //     fillHistosSample(*(bkg_samples_.at(isample)));
    // }

    // // datadriven    
    // for (uint isample = 0; isample < datadriven_samples_.size(); ++isample) // loop on samples
    // {             
    //     fillHistosSample(*(datadriven_samples_.at(isample)));
    // }

    if (multithreaded_)
        fillHistos_mt();
    else
        fillHistos_non_mt();
}

void AnalysisHelper::fillHistos_non_mt()
{
    for (uint isample = 0; isample < data_samples_.size(); ++isample) // loop on samples
    {             
        fillHistosSample(*(data_samples_.at(isample)), std::promise<void>());
    }

    // sig
    for (uint isample = 0; isample < sig_samples_.size(); ++isample) // loop on samples
    {             
        fillHistosSample(*(sig_samples_.at(isample)), std::promise<void>());
    }

    // bkg    
    for (uint isample = 0; isample < bkg_samples_.size(); ++isample) // loop on samples
    {             
        fillHistosSample(*(bkg_samples_.at(isample)), std::promise<void>());
    }

    // datadriven    
    for (uint isample = 0; isample < datadriven_samples_.size(); ++isample) // loop on samples
    {             
        fillHistosSample(*(datadriven_samples_.at(isample)), std::promise<void>());
    }
}

void AnalysisHelper::fillHistos_mt()
{
    using namespace std::chrono_literals;
    std::vector< std::pair<std::future<void>, std::thread> > theThreadVector;
    auto totalMap = data_samples_ + datadriven_samples_ + sig_samples_ + bkg_samples_;

    for(uint isample = 0; isample < numberOfThreads_; ++isample)
    {
        if(isample >= totalMap.size()) break;
        std::promise<void> thePromise;
        auto theFuture = thePromise.get_future();
        theThreadVector.emplace_back( std::move(theFuture), std::thread(&AnalysisHelper::fillHistosSample, this, std::ref(*(totalMap.at(isample))), std::move(thePromise) ));
    }

    uint numberOfSampleSubmitted = numberOfThreads_;
    while(numberOfSampleSubmitted <totalMap.size())
    {
        std::this_thread::sleep_for(1s);
        size_t completedThreadPosition = 0;
        for(; completedThreadPosition<numberOfThreads_; ++completedThreadPosition)
        {
            if(theThreadVector[completedThreadPosition].first.wait_for(0ms) == std::future_status::ready) 
            {
                theThreadVector[completedThreadPosition].second.join();
                break;
            }
        }
        if(completedThreadPosition<numberOfThreads_)
        {
            std::promise<void> thePromise;
            auto theFuture = thePromise.get_future();
            theThreadVector[completedThreadPosition] = std::move(make_pair(std::move(theFuture), std::thread(&AnalysisHelper::fillHistosSample, this, std::ref(*(totalMap.at(numberOfSampleSubmitted))), std::move(thePromise)) ));
            ++numberOfSampleSubmitted;
        }
    }

    for(auto &theThread : theThreadVector) theThread.second.join();
    theThreadVector.clear();
}


void AnalysisHelper::setSplitting (int idxsplit, int nsplit)
{
    if (idxsplit >= nsplit)
    {
        cout << "** Warning: AnalysisHelper::setSplitting : cannot have idx splitting : " << idxsplit << " if nsplit is " << nsplit << ", skipping..." << endl;
        return;
    }
    nsplit_ = nsplit;
    idxsplit_ = idxsplit;
    
    // replace output name with suffix
    string appendix = ".root";
    size_t start_pos = outputFileName_.find(appendix);
    if(start_pos == std::string::npos)
        outputFileName_ += std::to_string(idxsplit_);
    else
        outputFileName_.replace(start_pos, appendix.length(), (string("_")+std::to_string(idxsplit_)+appendix));

    cout << "@@ split idx set to  : " << idxsplit_ <<  " of ntotal: " << nsplit_ << endl;       
    cout << "@@ new output name   : " << outputFileName_ << endl;
}

// list all the information analysis helper knows
void AnalysisHelper::dump(int detail)
{
    cout << " ========= dumping AnalysisHelper information =========" << endl;
    cout << endl;
    
    cout << "@@@@@@@@ GENERAL @@@@@@@@" << endl;
    cout << "@ lumi                   : " << lumi_ << endl;
    cout << "@ main cfg               : " << mainCfg_->getCfgName() << endl;
    cout << "@ sample cfg             : " << sampleCfg_->getCfgName() << endl;
    cout << "@ sel. cfg               : " << cutCfg_->getCfgName() << endl;
    cout << "@ n. selections          : " << selections_.size() << endl;
    cout << "@ n. variables           : " << variables_.size() << endl;
    cout << "@ n. 2D variables        : " << variables2D_.size() << endl;
    cout << "@ n. data samples        : " << data_samples_.size() << endl;
    cout << "@ n. sig samples         : " << sig_samples_.size() << endl;
    cout << "@ n. bkg samples         : " << bkg_samples_.size() << endl;
    cout << "@ n. datadriven samples  : " << datadriven_samples_.size() << endl;
    cout << endl;

    cout << "@@@@@@@@ VARIABLES @@@@@@@@" << endl;
    cout << "@ variable list: " << endl;
    for (uint iv = 0; iv < variables_.size(); ++iv)
    {
        cout << "  " << iv << " >> " << variables_.at(iv) << endl;
    }
    cout << endl;

    cout << "@ 2D variable list: " << endl;
    for (uint iv = 0; iv < variables2D_.size(); ++iv)
    {
        cout << "  " << iv << " >> " << variables2D_.at(iv).first << ":" << variables2D_.at(iv).second << endl;
    }
    cout << endl;


    cout << "@@@@@@@@ SELECTIONS @@@@@@@@" << endl;
    cout << "@ selection list: " << endl;
    for (uint is = 0; is < selections_.size(); ++is)
        cout << "  " << is << " >> " << setw(25) << left << selections_.at(is).getName() << setw(13) << " nweights: " << selections_.at(is).getWeights().size() << endl;
    if (detail >=1)
    {
        cout << "@ printing selections... " << endl;
        printSelections((detail >= 2 ? true : false), (detail >= 3 ? true : false));
    }
    cout << endl;

    cout << "@@@@@@@@ SAMPLES @@@@@@@@" << endl;
    cout << "@ data sample list: " << endl;
    for (uint is = 0; is < data_samples_.size(); ++is)
        cout << "  " << is << " >> " << setw(25) << left << data_samples_.at(is)->getName() << setw(13) << " nweights: " << data_samples_.at(is)->getWeights().size() << endl;

    cout << "@ sig sample list: " << endl;
    for (uint is = 0; is < sig_samples_.size(); ++is)
        cout << "  " << is << " >> " << setw(25) << left << sig_samples_.at(is)->getName() << setw(13) << " nweights: " << sig_samples_.at(is)->getWeights().size() << endl;

    cout << "@ bkg sample list: " << endl;
    for (uint is = 0; is < bkg_samples_.size(); ++is)
    {
        cout << "  " << is << " >> " << setw(25) << left << bkg_samples_.at(is)->getName() << setw(13) << " nweights: " << bkg_samples_.at(is)->getWeights().size() << endl;
    }
    cout << "@ datadriven sample list: " << endl;
    for (uint is = 0; is < datadriven_samples_.size(); ++is)
    {
        cout << "  " << is << " >> " << setw(25) << left << datadriven_samples_.at(is)->getName() << setw(13) << " nweights: " << datadriven_samples_.at(is)->getWeights().size() << endl;
    }
    cout << endl;
    if (detail >=1)
    {
        cout << "@ printing details... " << endl;
        printSamples((detail >= 2 ? true : false), (detail >= 3 ? true : false));
    }

    cout << " ================== end of printouts ==================" << endl;

}

void AnalysisHelper::prepareHistos()
{
    prepareSamplesHistos();
    prepareSamples2DHistos();
}

void AnalysisHelper::mergeSamples()
{
    for (unsigned int isnew = 0; isnew < sample_merge_list_.size(); ++isnew)
    {
        string newname = sample_merge_list_.key(isnew);
        cout << "@@ Merging histograms into " << newname << endl;

        // create an empty new sample.
        // NOTE: call this method after you finished to fill histos, the new sample has no tree associated and can't be filled!
        shared_ptr<Sample> snew (new Sample(newname, ""));
        snew->initCutHisto(selections_);

        // take the first histo in the list of masters
        string snamefirst = sample_merge_list_.at(isnew).at(0);
        shared_ptr<Sample> smaster = nullptr;
        ordered_map <std::string, std::shared_ptr<Sample>>* chosenMap = nullptr;
        int type = -1;
        
        if (data_samples_.has_key(snamefirst)){
            type = (int) Sample::kData;
            smaster = data_samples_.at(snamefirst);
            chosenMap = &data_samples_;
        }

        else if (bkg_samples_.has_key(snamefirst)){
            type = (int) Sample::kBkg;
            smaster = bkg_samples_.at(snamefirst);
            chosenMap = &bkg_samples_;
        }

        else if (datadriven_samples_.has_key(snamefirst)){
            type = (int) Sample::kDatadriven;
            smaster = datadriven_samples_.at(snamefirst);
            chosenMap = &datadriven_samples_;
        }

        else if (sig_samples_.has_key(snamefirst)){
            type = (int) Sample::kSig;
            smaster = sig_samples_.at(snamefirst);
            chosenMap = &sig_samples_;
        }
        else {
            cerr << "** AnalysisHelper : mergeSamples : error : could not find the sample " << snamefirst << " to merge, won't merge" << endl;
            return;
        }
        
        if (DEBUG) cout << "   DEBUG: --- merging histos - type is: " << type << endl;

        //////////////////////// -- 1D plots //////////////////////////////////
        // clone the histogram structure from the master

        Sample::selColl& plmaster = smaster->plots();
        Sample::selColl& plnew    = snew->plots();
        TH1F* hcnew               = snew->getCutHistogram();
        
        if (DEBUG) cout << "   DEBUG: --- merging histos - going to loop over 1d plot to make structure" << endl;

        for (unsigned int isel = 0; isel < plmaster.size(); ++isel){
            string selName = plmaster.key(isel);
            plnew.append(selName, Sample::varColl());

            // if (DEBUG) cout << "   DEBUG: --- 1. merging histos - " << selName << " appended to plnew" << endl;
            
            for (unsigned int ivar = 0; ivar < plmaster.at(isel).size(); ++ivar ){
                string varName = plmaster.at(isel).key(ivar);
                plnew.at(isel).append(varName, Sample::systColl());
                // if (DEBUG) cout << "   DEBUG: ---   2. merging histos - " << selName << " at " << varName << " appended to plnew" << endl;
            
                for (unsigned int isyst = 0; isyst < plmaster.at(isel).at(ivar).size(); ++isyst ){
                    string systName = plmaster.at(isel).at(ivar).key(isyst);
                    string hname = formHistoName (newname, selName, varName, systName);
                    // if (DEBUG) cout << "   DEBUG: ---      .merging histos - new histo name is: " << hname << " from: " << newname << " " <<  selName << " " <<  varName << " " <<  systName << "-||-" << endl;
                    std::shared_ptr<TH1F> hist ((TH1F*) plmaster.at(isel).at(ivar).at(isyst)->Clone(hname.c_str())) ;
                    hist->SetTitle(hist->GetName());
                    plnew.at(isel).at(ivar).append(systName, hist);
                    // if (DEBUG) cout << "   DEBUG: ---     3. merging histos - " << selName << " at " << varName << " at " << systName << " done new histo, nbins: " << hist->GetNbinsX() << endl;
                }   
            }
        }

        if (DEBUG) cout << "   DEBUG: --- merging histos - going to add the counter histograms" << endl;

        // NB: index starts from 0 because the original histogram is empty
        // cfr with the plot merge that starts from 1 because the "master" plots were already cloned
        for (unsigned int idx = 0; idx < sample_merge_list_.at(isnew).size(); ++idx)
        {
            string sname = sample_merge_list_.at(isnew).at(idx);
            TH1F* htoadd = chosenMap->at(sname)->getCutHistogram();
            hcnew->Add(htoadd);
        }

        if (DEBUG) cout << "   DEBUG: --- merging histos - going to add the other samples" << endl;

        // now add the content of the other histos to merge
        for (unsigned int idx = 1; idx < sample_merge_list_.at(isnew).size(); ++idx)
        {
            string sname = sample_merge_list_.at(isnew).at(idx);
            Sample::selColl& pltoadd = chosenMap->at(sname)->plots();
            for (unsigned int isel = 0; isel < plnew.size(); ++isel){
                for (unsigned int ivar = 0; ivar < plnew.at(isel).size(); ++ivar ){
                    for (unsigned int isyst = 0; isyst < plnew.at(isel).at(ivar).size(); ++isyst ){
                        plnew.at(isel).at(ivar).at(isyst)->Add(pltoadd.at(isel).at(ivar).at(isyst).get());
                    }   
                }
            }
        }

        //////////////////////// -- 2D plots //////////////////////////////////
        // clone the histogram structure from the master

        Sample::selColl2D& pl2Dmaster = smaster->plots2D();
        Sample::selColl2D& pl2Dnew    = snew->plots2D();
        
        if (DEBUG) cout << "   DEBUG: --- merging histos - going to loop over 1d plot to make structure" << endl;

        for (unsigned int isel = 0; isel < pl2Dmaster.size(); ++isel){
            string selName = pl2Dmaster.key(isel);
            pl2Dnew.append(selName, Sample::varColl2D());
            // if (DEBUG) cout << "   DEBUG: --- 1. merging histos - " << selName << " appended to pl2Dnew" << endl;
            
            for (unsigned int ivar = 0; ivar < pl2Dmaster.at(isel).size(); ++ivar ){
                string varName = pl2Dmaster.at(isel).key(ivar);
                pl2Dnew.at(isel).append(varName, Sample::systColl2D());
                // if (DEBUG) cout << "   DEBUG: ---   2. merging histos - " << selName << " at " << varName << " appended to pl2Dnew" << endl;
                string varName1 = variables2D_.at(ivar).first;
                string varName2 = variables2D_.at(ivar).second;
                for (unsigned int isyst = 0; isyst < pl2Dmaster.at(isel).at(ivar).size(); ++isyst ){
                    string systName = pl2Dmaster.at(isel).at(ivar).key(isyst);
                    string hname = formHisto2DName (newname, selName, varName1, varName2, systName);
                    // if (DEBUG) cout << "   DEBUG: ---      .merging histos - new histo name is: " << hname << " from: " << newname << " " <<  selName << " " <<  varName << " " <<  systName << "-||-" << endl;
                    std::shared_ptr<TH2F> hist ((TH2F*) pl2Dmaster.at(isel).at(ivar).at(isyst)->Clone(hname.c_str())) ;
                    hist->SetTitle(hist->GetName());
                    pl2Dnew.at(isel).at(ivar).append(systName, hist);
                    // if (DEBUG) cout << "   DEBUG: ---     3. merging histos - " << selName << " at " << varName << " at " << systName << " done new histo, nbins: " << hist->GetNbinsX() << endl;
                }   
            }
        }

        if (DEBUG) cout << "   DEBUG: --- merging histos - going to add the other samples" << endl;

        // now add the content of the other histos to merge
        for (unsigned int idx = 1; idx < sample_merge_list_.at(isnew).size(); ++idx)
        {
            string sname = sample_merge_list_.at(isnew).at(idx);
            Sample::selColl2D& pltoadd = chosenMap->at(sname)->plots2D();
            for (unsigned int isel = 0; isel < pl2Dnew.size(); ++isel){
                for (unsigned int ivar = 0; ivar < pl2Dnew.at(isel).size(); ++ivar ){
                    for (unsigned int isyst = 0; isyst < pl2Dnew.at(isel).at(ivar).size(); ++isyst ){
                        pl2Dnew.at(isel).at(ivar).at(isyst)->Add(pltoadd.at(isel).at(ivar).at(isyst).get());
                    }   
                }
            }
        }

        //////////////////////// now add the freshly created sample to its list, and remove old ones //////////////////////////////////

        if (DEBUG) cout << "   DEBUG: --- merging histos - appending new sample" << endl;
        chosenMap->append(newname, snew);
        if (DEBUG) cout << "   DEBUG: --- merging histos - deleting merged samples" << endl;
        for (string s : sample_merge_list_.at(isnew))
            chosenMap->remove(s);
        if (DEBUG) cout << "   DEBUG: --- merging histos - all done with sample " << newname << endl;
        if (DEBUG){
            cout << "   DEBUG: --- list of new samples " << endl;
            for (unsigned int ii = 0; ii < chosenMap->size(); ++ii)
                cout << "    ................ " << chosenMap->key(ii) << endl;
        }
    }
}


bool   AnalysisHelper::hasDefaultWeight(std::string weightName)
{
    return cutCfg_ -> hasOpt( Form("defaultWeight::%s",weightName.c_str()));
}



double AnalysisHelper::getDefaultWeight(std::string weightName)
{
    double def_val = (double) cutCfg_ -> readFloatOpt( Form("defaultWeight::%s",weightName.c_str()));
    return def_val;
}

bool AnalysisHelper::hasBranch(TTree* tree, std::string branchName)
{
    auto* br = tree->GetListOfBranches()->FindObject(branchName.c_str());
    
    if (!br)
        return false;
    else
        return true;
}


void AnalysisHelper::updateWeightSystAliasesList(const std::vector<std::pair<std::string, std::string> >& wlist)
{
    for (size_t iw = 0; iw < wlist.size(); ++iw)
    {
        string key   = wlist.at(iw).first; // my alias in the plot name
        string value = wlist.at(iw).second; // the actual weight name

        auto it = weight_aliases_.find(key);

        if (it == weight_aliases_.end())
            weight_aliases_[key] = value; // just save it
        else
        {
            string curr_val = it->second;
            if (curr_val == value) // was already there with the right name
                continue;
            else
                throw std::runtime_error("Weight systematic with alias " + key + " is doubly defined with different content");
        }
    }
}