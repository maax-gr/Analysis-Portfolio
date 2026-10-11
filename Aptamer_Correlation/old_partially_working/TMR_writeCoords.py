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
#ordner = "C:/Users/Max/OneDrive/TMR/structure_bundles/04_fourth_bundle_broaderC30C47/"
#merge = mda.Universe(ordner+"TMR3_1_5A.pdb")
#ordner = "C:/Users/maxim/OneDrive/TMR/structure_bundles/05_fifth_bundle/"
#merge = mda.Universe(ordner+"test10000.pdb")
#ordner = "C:/Users/Max/OneDrive/TMR/structure_bundles/06_sixth_bundle_like05/"
#merge = mda.Universe(ordner+"all_restraints_longer_10000.pdb")
#ordner = "C:/Users/Max/OneDrive/TMR/structure_bundles/07_seventh_bundle_junction/"
#merge = mda.Universe(ordner+"junction_10000.pdb")
#ordner = "C:/Users/Max/OneDrive/TMR/structure_bundles/08_eigth_bundle_free/"
#merge = mda.Universe(ordner+"free10000.pdb")
ordner = "C:/Users/maxim/OneDrive/TMR/structure_bundles/09_ninth_bundle_viele_bound/"
merge = mda.Universe(ordner+"all_restraints_longer_10000.pdb")

#%%
BP12 = np.zeros([merge.trajectory.n_frames,3])
BP30 = np.zeros([merge.trajectory.n_frames,3])
BP47 = np.zeros([merge.trajectory.n_frames,3])

ts = 0
#atoms = ['N1','C2','C4','C5','C13','C14','C16','C17','N10','O11']
atoms = ['C12','C13','C15','C17','N16','O21','ELEC']
#atoms = ['N16']

for which in atoms:
    BP12sel = "resid 12 and name "+which
    BP30sel = "resid 30 and name "+which
    BP47sel = "resid 47 and name "+which
    for st in merge.trajectory:
        BP12[ts,:] =  merge.select_atoms(BP12sel).positions[0]
        #BP30[ts,:] =  merge.select_atoms(BP30sel).positions[0]
        BP47[ts,:] =  merge.select_atoms(BP47sel).positions[0]
        ts = ts+1
    ts = 0
    
    np.savetxt(ordner+'BP12_'+(which),np.array(BP12))
    #np.savetxt(ordner+'BP30_'+(which),np.array(BP30))
    np.savetxt(ordner+'BP47_'+(which),np.array(BP47))
    
    
#%%
#if no gmx
ordner='C:/Users/maxim/OneDrive/TMR/structure_bundles/02_second_bundle/'
part1 = ordner+'TMR3_EPR_1.pdb'
part2 = ordner+'TMR3_EPR_2.pdb'
part3 = ordner+'TMR3_EPR_3.pdb'
part4 = ordner+'TMR3_EPR_4.pdb'
part5 = ordner+'TMR3_EPR_5.pdb'
part6 = ordner+'TMR3_EPR_6.pdb'
part7 = ordner+'TMR3_EPR_7.pdb'
part8 = ordner+'TMR3_EPR_8.pdb'
part9 = ordner+'TMR3_EPR_9.pdb'
part10 = ordner+'TMR3_EPR_10.pdb'

"""
ordner='C:/Users/maxim/OneDrive/TMR/structure_bundles/03_third_bundle_junction_loose/'
part1 = ordner+'TMR3_EPR_junc_1.pdb'
part2 = ordner+'TMR3_EPR_junc_2.pdb'
part3 = ordner+'TMR3_EPR_junc_3.pdb'
part4 = ordner+'TMR3_EPR_junc_4.pdb'
part5 = ordner+'TMR3_EPR_junc_5.pdb'
part6 = ordner+'TMR3_EPR_junc_6.pdb'
part7 = ordner+'TMR3_EPR_junc_7.pdb'
part8 = ordner+'TMR3_EPR_junc_8.pdb'
part9 = ordner+'TMR3_EPR_junc_9.pdb'
part10 = ordner+'TMR3_EPR_junc_10.pdb'"""

zusammen=ordner +'first_TMR.pdb'
merge = mda.Universe(part1)
with mda.Writer(zusammen,merge.select_atoms("all").n_atoms) as W:
    for ts in merge.trajectory[[0]]:
        W.write(merge.select_atoms('all'))
        
#%%
ordner = "C:/Users/maxim/OneDrive/TMR/structure_bundles/02_second_bundle_wrong/"
#zusammen=ordner +'TMR3_12_30_47_all.pdb'
zusammen=ordner +'tst.pdb'
part1 = ordner+'TMR3_EPR_1.pdb'

#merge = mda.Universe(ordner+'first_TMR.pdb',part1,part2,part3,part4,part5)
merge = mda.Universe(ordner+'first_TMR.pdb',part1,part2,part3,part4,part5,part6,part7,part8,part9,part10)
#merge = mda.Universe(ordner+'first_TMR.pdb',part1)

with mda.Writer(zusammen,merge.select_atoms("all").n_atoms) as W:
    for ts in merge.trajectory:
        W.write(merge.select_atoms('all'))

#%% needs gmx
ordner='/02_second_bundle/'
part1 = ordner+'TMR3_EPR_1.pdb'
part2 = ordner+'TMR3_EPR_2.pdb'
part3 = ordner+'TMR3_EPR_3.pdb'
part4 = ordner+'TMR3_EPR_4.pdb'
part5 = ordner+'TMR3_EPR_5.pdb'
part6 = ordner+'TMR3_EPR_6.pdb'
part7 = ordner+'TMR3_EPR_7.pdb'
part8 = ordner+'TMR3_EPR_8.pdb'
part9 = ordner+'TMR3_EPR_9.pdb'
part10 = ordner+'TMR3_EPR_10.pdb'

"""
ordner='TMR/03_third_bundle_junction_loose/'
part1 = ordner+'TMR3_EPR_junc_1.pdb'
part2 = ordner+'TMR3_EPR_junc_2.pdb'
part3 = ordner+'TMR3_EPR_junc_3.pdb'
part4 = ordner+'TMR3_EPR_junc_4.pdb'
part5 = ordner+'TMR3_EPR_junc_5.pdb'
part6 = ordner+'TMR3_EPR_junc_6.pdb'
part7 = ordner+'TMR3_EPR_junc_7.pdb'
part8 = ordner+'TMR3_EPR_junc_8.pdb'
part9 = ordner+'TMR3_EPR_junc_9.pdb'
part10 = ordner+'TMR3_EPR_junc_10.pdb'
"""

"""
part1 = ordner+'TMR3_12_30_47.pdb'
part2 = ordner+'TMR3_12_30_47_2.pdb'
part3 = ordner+'TMR3_12_30_47_3.pdb'
part4 = ordner+'TMR3_12_30_47_4.pdb'
part5 = ordner+'TMR3_12_30_47_5.pdb'
"""

befl = 'trjconv'; befl2 = "-s"; befl3 = part1;
befl4 = "-f";befl5 = part1;befl6 = "-dump" 
befl7 = "0"
befl8 = "-o"; befl9 = ordner+"first_TMR.pdb"

subprocess.run(["gmx",befl,befl2,befl3,befl4,befl5,befl6,befl7,befl8,befl9],text=True,input = "0")

