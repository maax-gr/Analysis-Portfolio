%reset -f
import MDAnalysis as mda
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from MDAnalysis.analysis import align
from MDAnalysis.analysis.rms import rmsd
import MDAnalysis.lib.NeighborSearch as KDNS
import pandas as pd
import csv
import subprocess

#%%
#merge = mda.Universe('C:/Users/maxim/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/test10000B09.pdb')
#merge = mda.Universe('C:/Users/maxim/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/firstframeB09.pdb','C:/Users/maxim/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/all_restraints_longer_10000.xtc')


#merge = mda.Universe('C:/Users/maxim/OneDrive/TMR/structure_bundles/08_eighth_bundle_free/free10000.pdb')
#merge = mda.Universe('C:/Users/maxim/OneDrive/TMR/structure_bundles/08_eighth_bundle_free/firstframeB08.pdb','C:/Users/maxim/OneDrive/TMR/structure_bundles/08_eighth_bundle_free/free10000.xtc')


#%%
computer = "maxim"
NMRpublished = mda.Universe('C:/Users/'+computer+'/OneDrive/TMR/structure_bundles/average_6gzk.pdb')


ordnerSel = "C:/Users/"+computer+"/OneDrive/TMR/database_data/Paper/"; 
selname = "Fit_Elke08_woTMR_50conf_7000struct_XG_newbckg0924XG"; merge = mda.Universe('C:/Users/'+computer+'/OneDrive/TMR/structure_bundles/08_eighth_bundle_free/firstframeB08.pdb','C:/Users/'+computer+'/OneDrive/TMR/structure_bundles/08_eighth_bundle_free/free10000.xtc')
#selname = "Fit_Elke09_50conf_TFcutof40_startLater5_woTMR_7000struct_N10"; merge = mda.Universe('C:/Users/'+computer+'/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/firstframeB09.pdb','C:/Users/'+computer+'/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/test10000B09.xtc')

#read_DF = pd.read_csv(ordnerSel+selname+'_Rlrg3.txt')
#zusammen = ordnerSel + selname+ '_Rlrg3_P1P3aligned.pdb'
#firstframe = ordnerSel+selname+'_Rlrg3_firstframe.pdb'

read_DF = pd.read_csv(ordnerSel+selname+'_Rsm3.txt')
zusammen = ordnerSel + selname+ '_Rsm3_P1P3aligned.pdb'
firstframe = ordnerSel+selname+'_Rsm3_firstframe.pdb'


#read_DF = pd.read_csv(ordnerSel+selname+'_unsorted.txt')
#zusammen = ordnerSel + selname+ '_unsorted_P1P3aligned_N20.pdb'
#firstframe = ordnerSel+selname+'_unsorted_firstframe_N20.pdb'

#read_DF = pd.read_csv(ordnerSel+selname+'_sorted.txt')
#zusammen = ordnerSel + selname+ '_sorted_P1P3aligned_N20.pdb'
#firstframe = ordnerSel+selname+'_sorted_firstframe.pdb'

#dieseframes = (np.array(read_DF["test"])[0:20])
dieseframes = (np.array(read_DF["test"]))
#dieseframes = np.unique(np.array(read_DF["test"]))
dieseframes= dieseframes-1

sel1 = "(resid 1:5 or resid 44:46 or resid 48 or resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
#sel2 = "(resid 1:5 or resid 44:46 or resid 48 or resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"

#P1#sel1 = "(resid 1:5 or resid 44:46 or resid 48) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
#P2#sel1 = "(resid 8:11 or resid 13 or resid 18:23) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
#P3#sel1 = "(resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"

sel2 = sel1
ribose = {'mobile': sel1, 'reference': sel2}

writeSele ="all and not resid 49:80"

#mda.analysis.align.alignto(merge, NMRpublished, select=ribose) 
#merge.select_atoms(writeSele).write(ordnerSel+selname+'_unsorted_firstframe.pdb')

with mda.Writer(zusammen,merge.select_atoms("all").n_atoms) as W:
    for ts in merge.trajectory[dieseframes]:
        mda.analysis.align.alignto(merge, NMRpublished, select=ribose) 
        W.write(merge.select_atoms(writeSele))
        
with mda.Writer(firstframe,merge.select_atoms("all").n_atoms) as W:       
    for ts in merge.trajectory[[dieseframes[0]]]:
        mda.analysis.align.alignto(merge, NMRpublished, select=ribose) 
        W.write(merge.select_atoms(writeSele))
