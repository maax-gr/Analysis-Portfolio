%reset -f
import MDAnalysis as mda
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from MDAnalysis.analysis import align
from MDAnalysis.analysis.rms import rmsd
#%%

#ordnerSel="C:/Users/maxim/OneDrive/TMR/structure_bundles/08_eighth_bundle_free/";
#bundle = "Fit_Elke08_woTMR_50conf_XG_normal"
#bundle = "Fit_Elke08_woTMR_50conf_XG_normal_R3"
#bundle = "Fit_Elke08_woTMR_50conf_7000struct_XG_normal"
#bundle = "Fit_Elke08_woTMR_50conf_7000struct_XG_normal_R3"
#bundle = "Fit_Elke08_woTMR_50conf_7000struct_XG_normal_R3_N10"
#writeSele ="all and not (name ELEC or resid 49:80) and not resname TMR"



ordnerSel="C:/Users/maxim/OneDrive/TMR/database_data/Paper/"; 
#bundle = "Fit_Elke09_50conf_TFcutof40_startLater5_woTMR_7000struct_N10_unsorted_P1P3aligned"
#writeSele ="all and not (name ELEC or resid 49:80)"

bundle = "Fit_Elke08_woTMR_50conf_7000struct_XG_newbckg0924XG_Rlrg3_P1P3aligned"
#bundle = "Fit_Elke08_woTMR_50conf_7000struct_XG_newbckg0924XG_Rsm3_P1P3aligned"
writeSele ="all and not (name ELEC or resid 49:80) and not resname TMR"


trj = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)
ref = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)


alignSele= {'mobile': writeSele, 'reference': writeSele}

aligned_rmsd = np.zeros([ref.trajectory.trajectory.n_frames,ref.trajectory.trajectory.n_frames])

for fram in range(ref.trajectory.trajectory.n_frames):
    ref.trajectory[fram]  # set reference trajectory to third frame

    for fram2 in range(ref.trajectory.trajectory.n_frames):
        trj.trajectory[fram2]
        #aligner = align.AlignTraj(trj, ref, select=writeSele, in_memory=True).run()
        aligned_rmsd[fram,fram2] = mda.analysis.rms.rmsd(trj.atoms.positions, ref.atoms.positions, superposition=True)

aligned_rmsd_sum = np.sum(aligned_rmsd,1)
plt.plot(np.linspace(0,ref.trajectory.trajectory.n_frames-1,ref.trajectory.trajectory.n_frames),aligned_rmsd_sum)


trj = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)
ref = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)
ref.select_atoms(writeSele).write(ordnerSel+bundle+"_refFrame_"+str(np.argmin(aligned_rmsd_sum)+1)+".pdb",frames = [np.argmin(aligned_rmsd_sum)])
refframe = mda.Universe(ordnerSel+bundle+"_refFrame_"+str(np.argmin(aligned_rmsd_sum)+1)+".pdb")

with mda.Writer(ordnerSel+bundle+"_aligned_refFrame_"+str(np.argmin(aligned_rmsd_sum)+1)+".pdb",trj.select_atoms(writeSele).n_atoms) as W:
    for ts in trj.trajectory:
        mda.analysis.align.alignto(trj, refframe, select=writeSele) 
        W.write(trj.select_atoms(writeSele))
        
        


#%
trj_aligned = mda.Universe(ordnerSel+bundle+"_aligned_refFrame_"+str(np.argmin(aligned_rmsd_sum)+1)+".pdb")
tmrApt = trj_aligned.select_atoms(writeSele)
#trj = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)
#tmrApt = trj.select_atoms(writeSele)

rmsfer = mda.analysis.rms.RMSF(tmrApt, verbose=True).run()

R = np.zeros([81,1])
nm_atoms_res = np.zeros([81,1])

plt.plot(rmsfer.rmsf)
plt.show()


dx = 0
for di in tmrApt.resnums:
    #print(di)
    #if di == 81:
    #    di = 49
    R[di-1,0] = R[di-1,0]+rmsfer.rmsf[dx]
    dx = dx+1
    nm_atoms_res[di-1,0] = nm_atoms_res[di-1,0]+1
    
plt.plot(tmrApt.resnums, rmsfer.rmsf)
plt.plot(np.linspace(0,80,81),R)



np.savetxt(ordnerSel+bundle+"_rmsf_sumoverResid_normed_RMSDaligned.txt",R/nm_atoms_res)
#np.savetxt(ordnerSel+"rmsf_sumoverResid_normed.txt",R/nm_atoms_res)
plt.show()
plt.plot(np.linspace(0,80,81),R/nm_atoms_res,'o')
plt.show()

#%%
ordnerSel="C:/Users/maxim/OneDrive/TMR/database_data/Paper/"; 
ordnerWrite = ordnerSel;
ordnerWrite = "C:/Users/maxim/OneDrive/TMR/database_data/Paper/newSubEnsembles/"; 
#bundle = "Fit_Elke09_50conf_TFcutof40_startLater5_woTMR_7000struct_N10_unsorted_P1P3aligned"
#writeSele ="all and not (name ELEC or resid 49:80)"

writeSele ="all and not (name ELEC or resid 49:80) and not resname TMR"
whichFram = 1

#bundle = "Fit_Elke08_woTMR_50conf_7000struct_XG_newbckg0924XG_Rsm3_P1P3aligned"
#Rsm3 P1 curled
#fr = np.array([1,3,5,9,11,12,13])-1
#whichFram = 12
#Rsm3 T shapexxx
#fr = np.array([2,4,6,7,8,10,14,15,16,17,18])-1
#whichFram = 8

bundle = "Fit_Elke08_woTMR_50conf_7000struct_XG_newbckg0924XG_Rlrg3_P1P3aligned"
#Rlrg3 empty
#fr = np.array([1,3,4,8,9,10,11,12,13,15,16,18,21,22,25,27])-1
#whichFram = 8
#Rlrg3 collapsed
fr = np.array([2,5,6,7,14,17,19,20,23,24,26,28,29,30,31,32])-1
whichFram = 20
#Rlrg3 fully curled
#fr = np.array([7,17,19,24,30])-1



trj = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)
ref = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)


alignSele= {'mobile': writeSele, 'reference': writeSele}

aligned_rmsd = np.zeros([ref.trajectory.trajectory.n_frames,ref.trajectory.trajectory.n_frames])

#for fram in range(ref.trajectory.trajectory.n_frames):
#    ref.trajectory[fram]  # set reference trajectory to third frame
#
#    for fram2 in range(ref.trajectory.trajectory.n_frames):
#        trj.trajectory[fram2]
#        #aligner = align.AlignTraj(trj, ref, select=writeSele, in_memory=True).run()
#        aligned_rmsd[fram,fram2] = mda.analysis.rms.rmsd(trj.atoms.positions, ref.atoms.positions, superposition=True)

#aligned_rmsd_sum = np.sum(aligned_rmsd,1)
#plt.plot(np.linspace(0,ref.trajectory.trajectory.n_frames-1,ref.trajectory.trajectory.n_frames),aligned_rmsd_sum)


trj = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)
ref = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)

ref.select_atoms(writeSele).write(ordnerWrite+bundle+"_refFrame_"+str(whichFram)+".pdb",frames = [whichFram-1])
refframe = mda.Universe(ordnerWrite+bundle+"_refFrame_"+str(whichFram)+".pdb")

with mda.Writer(ordnerWrite+bundle+"_aligned_refFrame_"+str(whichFram)+".pdb",trj.select_atoms(writeSele).n_atoms) as W:
    for ts in trj.trajectory[fr]:
        mda.analysis.align.alignto(trj, refframe, select=writeSele) 
        W.write(trj.select_atoms(writeSele))
        
        


#%
trj_aligned = mda.Universe(ordnerWrite+bundle+"_aligned_refFrame_"+str(whichFram)+".pdb")
tmrApt = trj_aligned.select_atoms(writeSele)
#trj = mda.Universe(ordnerSel+bundle+".pdb")#.select_atoms(writeSele)
#tmrApt = trj.select_atoms(writeSele)

rmsfer = mda.analysis.rms.RMSF(tmrApt, verbose=True).run()

R = np.zeros([81,1])
nm_atoms_res = np.zeros([81,1])

plt.plot(rmsfer.rmsf)
plt.show()


dx = 0
for di in tmrApt.resnums:
    #print(di)
    #if di == 81:
    #    di = 49
    R[di-1,0] = R[di-1,0]+rmsfer.rmsf[dx]
    dx = dx+1
    nm_atoms_res[di-1,0] = nm_atoms_res[di-1,0]+1
    
plt.plot(tmrApt.resnums, rmsfer.rmsf)
plt.plot(np.linspace(0,80,81),R)



np.savetxt(ordnerWrite+bundle+"_rmsf_sumoverResid_normed_RMSDaligned_refFrame"+str(whichFram)+".txt",R/nm_atoms_res)
#np.savetxt(ordnerSel+"rmsf_sumoverResid_normed.txt",R/nm_atoms_res)
plt.show()
plt.plot(np.linspace(0,80,81),R/nm_atoms_res,'o')
plt.show()

#%%
reffram = mda.Universe(ordnerSel+bundle+"_refFrame_"+str(np.argmin(aligned_rmsd_sum)+1)+".pdb")
Fitframs = mda.Universe(ordnerSel+bundle+".pdb")
aligner = align.AlignTraj(Fitframs, reffram,select=writeSele,in_memory=True).run()

Fitframs = mda.Universe(ordnerSel+bundle+".pdb")
rmsfer = mda.analysis.rms.RMSF(Fitframs.select_atoms(writeSele)).run()

plt.plot(rmsfer.rmsf)
plt.show()



#%%
u.add_TopologyAttr('tempfactors') # add empty attribute for all atoms
protein = u.select_atoms('protein') # select protein atoms
for residue, r_value in zip(protein.residues, R.results.rmsf):
    residue.atoms.tempfactors = r_value

































#%%
import numpy as np
from Bio.PDB import PDBParser

def calculate_rmsf(structures):
    parser = PDBParser()
    all_coords = []
    
    for structure in structures:
        model = parser.get_structure(structure, structure)
        coords = []
        for atom in model.get_atoms():
            coords.append(atom.get_coord())
        all_coords.append(np.array(coords))
    
    all_coords = np.array(all_coords)
    mean_coords = np.mean(all_coords, axis=0)
    rmsf = np.sqrt(np.mean((all_coords - mean_coords) ** 2, axis=0))
    
    return rmsf

structures = ["rna1.pdb", "rna2.pdb", "rna3.pdb", ...]
rmsf = calculate_rmsf(structures)
np.savetxt("rmsf.txt", rmsf)


#%%
import pymol
from pymol import cmd
import numpy as np

pymol.finish_launching()
ordnerSel="C:/Users/Max/OneDrive/TMR/structure_bundles/05_fifth_bundle/"; 

#cmd.load("reference_structure.pdb", "ref")
cmd.load("C:/Users/Max/OneDrive/TMR/structure_bundles/05_fifth_bundle/refFrame.pdb","ref")

# Load RMSF values
rmsf = np.loadtxt(ordnerSel+"rmsf.txt")

# Define a color gradient (e.g., blue to red)
cmd.set_color("low", [0, 0, 1])
cmd.set_color("high", [1, 0, 0])

# Apply colors based on RMSF
for i, value in enumerate(rmsf):
    color = [min(1, max(0, value)), 0, min(1, max(0, 1 - value))]
    cmd.set_color(f"color_{i}", color)
    cmd.alter(f"ref and resi {i+1}", f"color=color_{i}")

cmd.show("cartoon", "ref")
cmd.spectrum("b", "blue_white_red", "ref", minimum=min(rmsf), maximum=max(rmsf))
cmd.ramp_new("ramp", "ref", [min(rmsf), max(rmsf)], ["blue", "white", "red"])

cmd.quit()


#%%
import pymol
from pymol import cmd
import numpy as np

#pymol.finish_launching()
ordnerSel="C:/Users/Max/OneDrive/TMR/structure_bundles/05_fifth_bundle/"; 

# Load reference structure
#cmd.load(ordnerSel+"refFrame.pdb", "ref")

# Load RMSF values
rmsf = np.loadtxt(ordnerSel+"rmsf.txt")

# Define the min and max RMSF values
min_rmsf = min(rmsf)
max_rmsf = max(rmsf)

# Normalize RMSF values for coloring
norm_rmsf = (rmsf - min_rmsf) / (max_rmsf - min_rmsf)

# Apply colors based on normalized RMSF values
for i, norm_value in enumerate(norm_rmsf):
    color = [norm_value, 0, 1 - norm_value]  # Create a gradient from blue (low RMSF) to red (high RMSF)
    cmd.set_color(f"color_{i}", color)
    cmd.alter(f"ref and resi {i+1}", f"b={rmsf[i]}")  # Set the B-factor to RMSF value
    cmd.color(f"color_{i}", f"ref and resi {i+1}")

cmd.show("cartoon", "ref")
cmd.spectrum("b", "blue_white_red", "ref", minimum=min_rmsf, maximum=max_rmsf)

#cmd.quit()
#%%
import matplotlib.pyplot as plt
plt.plot(norm_rmsf)