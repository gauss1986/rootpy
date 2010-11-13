import math
from rootpy.utils import *
from operator import itemgetter, add
from ROOT import TLorentzVector

def toRel16Tracking(tree):
    """
    Based on Ryan Reece's code here:
    https://svnweb.cern.ch/trac/atlasgrp/browser/CombPerf/Tau/Analysis/ZToTwoTausAnalysis/trunk/src/ThinTauVarsCycle.cxx
    """
    for itau in range(tree.tau_n[0]):

        if tree.tau_author[itau] == 2:
            continue

        tau_numTrack = tree.tau_numTrack[itau]
        tau_eta = tree.tau_seedCalo_eta[itau]
        tau_phi = tree.tau_seedCalo_phi[itau]
        sumTrkPt = 0.
        dRsumTrkPt = 0.
        leadTrkPt = -1111.
        new_charge = 0
        tracks = []
        new_numTrack = 0

        if tau_numTrack != tree.tau_track_n[itau]:
            print "WARNING: tau_numTrack (%i) != tau_track_n (%i)"%(tau_numTrack,tree.tau_track_n[itau])

        # recount core tracks with rel 16 selection
        for itrack in range(tau_numTrack):
            track_eta = tree.tau_track_eta[itau][itrack]
            track_phi = tree.tau_track_phi[itau][itrack]
            track_d0 = tree.tau_track_atPV_d0[itau][itrack]
            track_theta = tree.tau_track_atPV_theta[itau][itrack]
            track_z0 = tree.tau_track_atPV_z0[itau][itrack]
            track_nBLHits = tree.tau_track_nBLHits[itau][itrack]
            track_nPixHits = tree.tau_track_nPixHits[itau][itrack]
            track_nSCTHits = tree.tau_track_nSCTHits[itau][itrack]
            track_pt = tree.tau_track_pt[itau][itrack]
            #track_charge = tree.tau_track_charge[itau][itrack]
            dR = dr(tau_eta, tau_phi, track_eta, track_phi)
            if dR < .2 and \
               track_pt > 1000 and \
               track_nBLHits > 0 and \
               track_nPixHits > 1 and \
               track_nPixHits + track_nSCTHits > 6 and \
               abs(track_d0) < 1.0 and \
               abs(track_z0 * math.sin(track_theta)) < 1.5:
     
                if track_pt > leadTrkPt:
                    leadTrkPt = track_pt
                new_numTrack += 1
                #new_charge += track_charge
                sumTrkPt += track_pt
                dRsumTrkPt += dR*track_pt
                track = TLorentzVector()
                track.SetPtEtaPhiM(track_pt,track_eta,track_phi,105.0)#139.57)
                tracks.append(track)

        # get wide tracks with rel 16 selection
        for itrack in range(tree.trk_n[0]):
            track_eta = tree.trk_eta[itrack]
            track_phi = tree.trk_phi[itrack]
            track_d0 = tree.trk_d0_wrtPV[itrack]
            track_theta = tree.trk_theta[itrack]
            track_z0 = tree.trk_z0_wrtPV[itrack]
            track_nBLHits = tree.trk_nBLHits[itrack]
            track_nPixHits = tree.trk_nPixHits[itrack]
            track_nSCTHits = tree.trk_nSCTHits[itrack]
            track_pt = tree.trk_pt[itrack]
            dR = dr(tau_eta, tau_phi, track_eta, track_phi)
            if dR >= .2 and dR < .4 and \
               track_pt > 1000 and \
               track_nBLHits > 0 and \
               track_nPixHits > 1 and \
               track_nPixHits + track_nSCTHits > 6 and \
               abs(track_d0) < 1.0 and \
               abs(track_z0 * math.sin(track_theta)) < 1.5:

                sumTrkPt += track_pt
                dRsumTrkPt += dR*track_pt
                track = TLorentzVector()
                track.SetPtEtaPhiM(track_pt,track_eta,track_phi,105.0)#139.57)
                tracks.append(track)

        # correct numTrack
        tree.tau_numTrack[itau] = new_numTrack

        # correct charge
        #tree.tau_charge[itau] = new_charge

        # correct leadTrkPt
        tree.tau_leadTrkPt[itau] = leadTrkPt

        # correct etOverPtLeadTrk
        if leadTrkPt != 0:
            tree.tau_etOverPtLeadTrk[itau] = ( tree.tau_seedCalo_etEMAtEMScale[itau] + tree.tau_seedCalo_etHadAtEMScale[itau] )/ leadTrkPt
        else:
            tree.tau_etOverPtLeadTrk[itau] = -1111.
        
        # correct trkAvgDist
        if sumTrkPt!=0:
            (tree.tau_seedCalo_trkAvgDist)[itau] = dRsumTrkPt/sumTrkPt
        else:
            (tree.tau_seedCalo_trkAvgDist)[itau] = -1111.

        (tree.tau_calcVars_sumTrkPt)[itau] = sumTrkPt

        # correct massTrkSys
        if len(tracks) > 1:
            tree.tau_massTrkSys[itau] = reduce(add,tracks).M()
        else:
            tree.tau_massTrkSys[itau] = -1111.

""" Soshi's version: 
def toRel16Tracking(tree):

    for itau in range(tree.tau_n[0]):

        # here should be applied to the EM scale correction. -- Saminder
        # Tau_Et[i] = correction(pt,eta,EMF)*(TauCalo_etEMAtEMScale[i]+TauCalo_etHadAtEMScale[i]);

        # seed position
        seedPhi = (tree.tau_jet_phi)[itau]
        seedEta = (tree.tau_jet_eta)[itau]

        # Create rel.16 tracks
        if (tree.tau_author)[itau]!=2:
            seedTrack = []
            coreTrack = []

            for itrack in range(tree.tau_track_n[itau]):
                dR = dr(seedEta,seedPhi,(tree.tau_track_eta)[itau][itrack],(tree.tau_track_phi)[itau][itrack])
                if (tree.tau_track_pt)[itau][itrack]>1000. and dR<0.2:
                    # find seed tracks
                    if (tree.tau_track_pt)[itau][itrack]>6000. and \
                       abs((tree.tau_track_atPV_d0)[itau][itrack])<2.0 and \
                       abs((tree.tau_track_atPV_z0)[itau][itrack]*math.sin((tree.tau_track_atPV_theta)[itau][itrack]))<10.0 and \
                       (tree.tau_track_nPixHits)[itau][itrack]+(tree.tau_track_nSCTHits)[itau][itrack]>6 and \
                       (tree.tau_track_nTRTHits)[itau][itrack]>0:
              
                        seedTrack.append(((tree.tau_track_pt)[itau][itrack],(tree.tau_track_eta)[itau][itrack],(tree.tau_track_phi)[itau][itrack],itrack))

                    # find core tracks
                    if abs((tree.tau_track_atPV_d0)[itau][itrack])<1.0 and \
                       abs((tree.tau_track_atPV_z0)[itau][itrack]*math.sin((tree.tau_track_atPV_theta)[itau][itrack]))<1.5 and \
                       (tree.tau_track_nPixHits)[itau][itrack]>1 and \
                       (tree.tau_track_nBLHits)[itau][itrack]>0 and \
                       (tree.tau_track_nTRTHits)[itau][itrack]>0:

                        coreTrack.append(((tree.tau_track_pt)[itau][itrack],(tree.tau_track_eta)[itau][itrack],(tree.tau_track_phi)[itau][itrack],itrack))

            seedTrack.sort(key=itemgetter(0),reverse=True)
            coreTrack.sort(key=itemgetter(0),reverse=True)

            # Overwrite newly created variables
            if len(seedTrack)>0:
                (tree.tau_leadTrkPt)[itau] = seedTrack[0][0]
                if (tree.tau_leadTrkPt)[itau] != 0:
                    (tree.tau_etOverPtLeadTrk)[itau] = ((tree.tau_seedCalo_etEMAtEMScale)[itau]+(tree.tau_seedCalo_etHadAtEMScale)[itau])/(tree.tau_leadTrkPt)[itau] # at EM scale
                else:
                    (tree.tau_etOverPtLeadTrk)[itau] = -1111.
            else:
                (tree.tau_leadTrkPt)[itau] = -1111.
                (tree.tau_etOverPtLeadTrk)[itau] = -1111.

            nTauTrack = 0
            trkRadius = 0.
            sumTrkPt = 0.
            sumdRTrkPt = 0.

            for track in seedTrack:
                dR = dr(seedEta,seedPhi,track[1],track[2])
                sumTrkPt += track[0]
                sumdRTrkPt += dR*track[0]
                nTauTrack += 1

            for track in coreTrack:
                overlap = False
                for seedtrack in seedTrack:
                    if track[3] == seedtrack[3]:
                        overlap = True
                if not overlap:
                    dR = dr(seedEta,seedPhi,track[1],track[2])
                    sumTrkPt += track[0]
                    sumdRTrkPt += dR*track[0]
                    nTauTrack += 1

            if sumTrkPt!=0.0:
                trkRadius = sumdRTrkPt/sumTrkPt
            else:
                trkRadius = -1111.

            (tree.tau_numTrack)[itau] = nTauTrack
            (tree.tau_seedCalo_trkAvgDist)[itau] = trkRadius
            (tree.tau_calcVars_sumTrkPt)[itau]   = sumTrkPt
"""