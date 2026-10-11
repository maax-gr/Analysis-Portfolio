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
#ordnerSel="C:/Users/maxim/OneDrive/TMR/structure_bundles/05_fifth_bundle/"; 
#merge = mda.Universe(ordnerSel+"test10000.pdb")

#ordnerSel="C:/Users/maxim/OneDrive/TMR/structure_bundles/08_eighth_bundle_free/"; 
#merge = mda.Universe(ordnerSel+"free10000.pdb")

ordnerSel="C:/Users/maxim/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/"; 
merge = mda.Universe(ordnerSel+"test10000B09.pdb")

NMRpublished = mda.Universe('C:/Users/maxim/OneDrive/TMR/structure_bundles/average_6gzk.pdb')

#ordnerSel='C:/Users/maxim/OneDrive/TMR/structure_bundles/07_seventh_bundle_junction/'; merge = mda.Universe(ordnerSel+"junction_10000.pdb")
#NMRpublished = mda.Universe('C:/Users/maxim/OneDrive/TMR/structure_bundles/average_6gzk - Kopie.pdb')

#%%
#writeSele ="all and not ( name ELEC or  resid 49:80)"
writeSele = "all"
merge.select_atoms(writeSele).write(ordnerSel+'firstframeB09.pdb')

with mda.Writer(ordnerSel+"test10000B09.xtc",merge.select_atoms(writeSele).n_atoms) as W:
    #for ts in merge.trajectory[dieseframes]:
    for ts in merge.trajectory:
        W.write(merge.select_atoms(writeSele))

#average = align.AverageStructure(merge, merge, select="all",ref_frame=0).run()
#average.universe.select_atoms("all").write(ordnerSel+"average_full_all.xyz")

#firstframe = mda.Universe(ordnerSel + "firstframe_forPCA.pdb")
#for ts in merge.trajectory:
#    
#mda.analysis.align.alignto(merge, firstframe, select=writeSele) 


#align.rmsd(trajec.select_atoms('nucleic').positions, ref.select_atoms('nucleic').positions,superposition=True)
#align.AlignTraj(trajec, ref, filename='DEeven_trjal.dcd',superposition=True).run()
    

#average = align.AverageStructure(merge, select=writeSele).run()
#average.universe.select_atoms(writeSele).write(ordnerSel+"average_full.pdb")

#average = align.AverageStructure(merge, merge, select="nucleic",ref_frame=0).run()
#average.universe.select_atoms("nucleic").write(ordnerSel+"average_nucleic_full.pdb")


#%%
#selname = "Fit_Elke05_50conf_XG_TFcutoff40_normal"
#selname = "Fit_Elke05_50conf_XG_TFcutoff40_normal_C30C47mainPeak"
#selname = "Fit_Elke05_50conf_XG_TFcutoff_1_08_normal_C30C47mainPeak"
#selname = "Fit_Elke07_50conf_TFcutof50_XG_normal"
#selname = "Fit_Elke08_woTMR_50conf_XG_normal_R3"
#selname = "Fit_Elke08_woTMR_50conf_7000struct_XG_normal"
#selname = "Fit_Elke08_woTMR_50conf_7000struct_XG_normal_R3"
#selname = "Fit_Elke08_woTMR_50conf_7000struct_XG_normal_R3_N10"
#selname = "Fit_Elke09_50conf_TFcutof40_startLater_woTMR_N10_auswertung0824"
#selname = "Fit_Elke09_50conf_TFcutof40_start_woTMR_7000struct_N10_auswertung0824"
#ordnerSel="C:/Users/maxim/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/"; 
#selname = "Fit_Elke09_50conf_TFcutof40_start_woTMR_7000struct_N10_auswertung0824"


merge = mda.Universe(ordnerSel+"all_restraints_longer_10000.pdb")

#%%
zusammen = ordnerSel + selname+ '_P1P3aligned_unsorted_N20.pdb'

read_DF = pd.read_csv(ordnerSel+selname+'_unsorted.txt')
dieseframes = np.unique(np.array(read_DF["test"])[0:20])
dieseframes= dieseframes-1

sel1 = "(resid 1:5 or resid 44:46 or resid 48 or resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
#sel2 = "(resid 1:5 or resid 44:46 or resid 48 or resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"

#P1#sel1 = "(resid 1:5 or resid 44:46 or resid 48) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
#P2#sel1 = "(resid 8:11 or resid 13 or resid 18:23) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
#P3#sel1 = "(resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
sel2 = sel1
#sel1 = "resname TMR"; sel2 = "resid 101"


ribose = {'mobile': sel1, 'reference': sel2}

#writeSele ="all and not (name ELEC or resid 49:80) and not resname TMR"
writeSele ="all and not resid 49:80"

with mda.Writer(zusammen,merge.select_atoms("all").n_atoms) as W:
    for ts in merge.trajectory[dieseframes]:
        mda.analysis.align.alignto(merge, NMRpublished, select=ribose) 
        W.write(merge.select_atoms(writeSele))
        #W.write(merge.select_atoms('all'))



#%%
#selname = "Fit_Elke05_50conf_XG_TFcutoff40_normal"

zusammen = ordnerSel + selname+ '_forPCA.pdb'

read_DF = pd.read_csv(ordnerSel+selname+'.txt')
dieseframes = np.unique(np.array(read_DF["test"]))

sel1 = "(resid 1:5 or resid 44:46 or resid 48 or resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"
sel2 = "(resid 1:5 or resid 44:46 or resid 48 or resid 26:29 or resid 35:39) and name [ C1' , C2' , C3' , C4' , C5' , O5' ]"

ribose = {'mobile': sel1, 'reference': sel2}     

writeSele ="all and not ( name ELEC or  resid 49:80)"

with mda.Writer(zusammen,merge.select_atoms("nucleic").n_atoms) as W:
    for ts in merge.trajectory[dieseframes]:
        mda.analysis.align.alignto(merge, NMRpublished, select=ribose) 
        W.write(merge.select_atoms(writeSele))
        
selUni = mda.Universe(ordnerSel+selname+"_forPCA.pdb")
selUni.select_atoms(writeSele).write(ordnerSel+'firstframe_'+selname+'_forPCA.pdb')

#average = align.AverageStructure(trajec, trajec, select='all',ref_frame=0).run()
#average.universe.select_atoms('all').write(ordner+"average_"+wat+".pdb")




    