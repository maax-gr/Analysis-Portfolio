import pymol
from pymol import cmd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize


pymol.finish_launching()
#ordnerSel="C:/Users/Max/OneDrive/TMR/structure_bundles/05_fifth_bundle/"; 
ordnerSel="C:/Users/maxim/OneDrive/TMR/structure_bundles/05_fifth_bundle/";

# Load reference structure
cmd.load(ordnerSel+"Fit_Elke05_50conf_XG_TFcutoff40_normal_refFrame_2.pdb", "ref")

# Load RMSF values
rmsf = np.loadtxt(ordnerSel+"Fit_Elke05_50conf_XG_TFcutoff40_normal_rmsf_sumoverResid_normed_RMSDaligned.txt")

# Define the min and max RMSF values
min_rmsf = min(rmsf)
max_rmsf = max(rmsf)

# Normalize RMSF values for coloring
norm_rmsf = (rmsf - min_rmsf) / (max_rmsf - min_rmsf)
#norm_rmsf = rmsf

colors = [(0,0.2,0.8),(0.90,0.90,0.90),(0.6350, 0.0780, 0.1840)]
#colors = [(0, 0, 1), (1, 1, 1), (1, 0, 0)]  # Blue -> White -> Red
positions = [0, 0.5, 1]
custom_cmap = LinearSegmentedColormap.from_list("blue_white_red", list(zip(positions, colors)))
colormapped = custom_cmap(norm_rmsf)


# Apply colors based on normalized RMSF values
for i, norm_value in enumerate(norm_rmsf):
    color = list(colormapped[i,0:3])
    #color = [norm_value, 0, (1 - norm_value)]  # Create a gradient from blue (low RMSF) to red (high RMSF)
    #col = [1, 1, 1]  # Create a gradient from blue (low RMSF) to red (high RMSF)
    cmd.set_color(f"color_{i}", color)
    #cmd.alter(f"ref and resi {i+1}", f"b={rmsf[i]}")  # Set the B-factor to RMSF value
    cmd.color(f"color_{i}", f"ref and resi {i+1}")

cmd.show("cartoon", "ref")
#cmd.spectrum("b", "blue_white_red", "ref", minimum=min_rmsf, maximum=max_rmsf)

#cmd.quit()